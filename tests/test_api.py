from fastapi.testclient import TestClient

from app.schemas import AIOutput
from app.services.ai import GeminiAIProvider, ImageInput
from tests.conftest import make_image_bytes


def upload_listing(client: TestClient, location_id: str, count: int = 1):
    files = [
        ("images", (f"item-{index}.png", make_image_bytes(color="blue"), "image/png"))
        for index in range(count)
    ]
    return client.post(
        "/api/v1/listings",
        data={"location_id": location_id},
        files=files,
    )


def test_health_and_categories_are_seeded_once(client: TestClient, app) -> None:
    health = client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json() == {"status": "ok", "database": "ok", "ai_provider": "stub"}

    first = client.get("/api/v1/categories").json()
    assert len(first) == 11
    assert first[0]["slug"] == "clothing"
    assert first[-1]["slug"] == "other"

    # Running startup logic in another app instance against the same DB remains idempotent.
    with TestClient(app):
        second = client.get("/api/v1/categories").json()
    assert len(second) == 11


def test_location_create_list_and_patch(client: TestClient, location: dict) -> None:
    listed = client.get("/api/v1/locations")
    assert listed.status_code == 200
    assert listed.json()[0]["id"] == location["id"]

    updated = client.patch(
        f"/api/v1/locations/{location['id']}", json={"suburb": "Newton"}
    )
    assert updated.status_code == 200
    assert updated.json()["suburb"] == "Newton"


def test_upload_analyze_and_serve_multiple_images(
    client: TestClient, location: dict
) -> None:
    response = upload_listing(client, location["id"], count=2)
    assert response.status_code == 201
    listing = response.json()
    assert listing["status"] == "draft"
    assert listing["category"]["slug"] == "other"
    assert listing["analysis"]["status"] == "succeeded"
    assert listing["analysis"]["provider"] == "stub"
    assert [image["sort_order"] for image in listing["images"]] == [0, 1]

    media = client.get(listing["images"][0]["url"])
    assert media.status_code == 200
    assert media.headers["content-type"] == "image/png"


def test_review_publish_and_filter(client: TestClient, location: dict) -> None:
    listing = upload_listing(client, location["id"]).json()
    categories = client.get("/api/v1/categories").json()
    clothing = next(category for category in categories if category["slug"] == "clothing")

    cleared = client.patch(
        f"/api/v1/listings/{listing['id']}", json={"category_id": None}
    )
    assert cleared.status_code == 200
    assert client.post(f"/api/v1/listings/{listing['id']}/publish").status_code == 422

    updated = client.patch(
        f"/api/v1/listings/{listing['id']}", json={"category_id": clothing["id"]}
    )
    assert updated.status_code == 200
    assert updated.json()["category"]["slug"] == "clothing"

    assert client.get("/api/v1/listings").json()["total"] == 0
    published = client.post(f"/api/v1/listings/{listing['id']}/publish")
    assert published.status_code == 200
    assert published.json()["status"] == "published"
    assert client.post(f"/api/v1/listings/{listing['id']}/publish").status_code == 409

    matching = client.get(
        "/api/v1/listings",
        params={"category": "clothing", "location_id": location["id"]},
    ).json()
    assert matching["total"] == 1
    assert matching["items"][0]["id"] == listing["id"]
    assert client.get("/api/v1/listings", params={"category": "furniture"}).json()[
        "total"
    ] == 0


def test_image_validation_and_last_image_guard(
    client: TestClient, app, location: dict
) -> None:
    invalid = client.post(
        "/api/v1/listings",
        data={"location_id": location["id"]},
        files=[("images", ("fake.png", b"not an image", "image/png"))],
    )
    assert invalid.status_code == 422

    empty = client.post(
        "/api/v1/listings",
        data={"location_id": location["id"]},
        files=[("images", ("empty.png", b"", "image/png"))],
    )
    assert empty.status_code == 422

    unsupported = client.post(
        "/api/v1/listings",
        data={"location_id": location["id"]},
        files=[("images", ("item.gif", make_image_bytes(), "image/gif"))],
    )
    assert unsupported.status_code == 415

    oversized = client.post(
        "/api/v1/listings",
        data={"location_id": location["id"]},
        files=[("images", ("huge.png", b"x" * (1024 * 1024 + 1), "image/png"))],
    )
    assert oversized.status_code == 413

    too_many = upload_listing(client, location["id"], count=6)
    assert too_many.status_code == 422
    assert list(app.state.storage.root.rglob("*")) == []

    listing = upload_listing(client, location["id"]).json()
    rejected = client.delete(
        f"/api/v1/listings/{listing['id']}/images/{listing['images'][0]['id']}"
    )
    assert rejected.status_code == 409


def test_add_delete_and_reanalyze_images(client: TestClient, location: dict) -> None:
    listing = upload_listing(client, location["id"]).json()
    added = client.post(
        f"/api/v1/listings/{listing['id']}/images",
        files=[("images", ("second.png", make_image_bytes(color="red"), "image/png"))],
    )
    assert added.status_code == 200
    assert added.json()["analysis"]["status"] == "pending"
    assert added.json()["analysis"]["summary"] is None
    assert len(added.json()["images"]) == 2

    first_image_id = added.json()["images"][0]["id"]
    deleted = client.delete(
        f"/api/v1/listings/{listing['id']}/images/{first_image_id}"
    )
    assert deleted.status_code == 200
    assert deleted.json()["images"][0]["sort_order"] == 0

    analyzed = client.post(f"/api/v1/listings/{listing['id']}/analyze")
    assert analyzed.status_code == 200
    assert analyzed.json()["analysis"]["status"] == "succeeded"


class FailingProvider:
    name = "failing-test-provider"

    def analyze(self, _images, _category_slugs) -> AIOutput:
        raise RuntimeError("provider unavailable")


def test_ai_failure_preserves_retryable_draft(
    client: TestClient, app, location: dict
) -> None:
    app.state.ai_provider = FailingProvider()
    created = upload_listing(client, location["id"])
    assert created.status_code == 201
    listing = created.json()
    assert listing["status"] == "draft"
    assert listing["analysis"]["status"] == "failed"
    assert listing["analysis"]["provider"] == "failing-test-provider"

    retry = client.post(f"/api/v1/listings/{listing['id']}/analyze")
    assert retry.status_code == 502
    preserved = client.get(f"/api/v1/listings/{listing['id']}").json()
    assert preserved["analysis"]["status"] == "failed"
    assert len(preserved["images"]) == 1


class FakeGeminiModels:
    def __init__(self) -> None:
        self.config = None

    def generate_content(self, *, model, contents, config):
        self.config = config

        class Response:
            parsed = {
                "category_slug": "clothing",
                "confidence": 0.91,
                "summary": "A denim jacket",
                "detected_text": ["SIZE M"],
            }
            text = None

        return Response()


def test_gemini_provider_uses_structured_category_schema() -> None:
    provider = GeminiAIProvider.__new__(GeminiAIProvider)
    fake_models = FakeGeminiModels()
    provider.client = type("FakeClient", (), {"models": fake_models})()
    provider.model = "test-model"

    result = provider.analyze(
        [ImageInput(data=make_image_bytes(), mime_type="image/png")],
        ["clothing", "other"],
    )

    assert result.category_slug == "clothing"
    assert result.detected_text == ["SIZE M"]
    assert fake_models.config.response_json_schema["properties"]["category_slug"][
        "enum"
    ] == ["clothing", "other"]
