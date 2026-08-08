from collections.abc import Iterator
from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.config import Settings
from app.main import create_app


@pytest.fixture
def app(tmp_path):
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
        upload_dir=tmp_path / "uploads",
        ai_provider="stub",
        max_image_bytes=1024 * 1024,
        _env_file=None,
    )
    return create_app(settings)


@pytest.fixture
def client(app) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def location(client: TestClient) -> dict:
    response = client.post(
        "/api/v1/locations",
        json={
            "name": "Karangahape Road Store",
            "address_line": "123 Karangahape Road",
            "suburb": "Auckland Central",
            "city": "Auckland",
            "region": "Auckland",
            "postcode": "1010",
            "latitude": -36.857,
            "longitude": 174.761,
        },
    )
    assert response.status_code == 201
    return response.json()


def make_image_bytes(image_format: str = "PNG", color: str = "blue") -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (32, 32), color=color).save(buffer, format=image_format)
    return buffer.getvalue()


@pytest.fixture
def png_bytes() -> bytes:
    return make_image_bytes()

