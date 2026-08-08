from dataclasses import dataclass
from io import BytesIO
from pathlib import Path, PurePosixPath
from shutil import rmtree
from uuid import uuid4

from fastapi import UploadFile
from PIL import Image as PillowImage
from PIL import UnidentifiedImageError


ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
FORMAT_DETAILS = {
    "JPEG": ("image/jpeg", ".jpg"),
    "PNG": ("image/png", ".png"),
    "WEBP": ("image/webp", ".webp"),
}


class StorageValidationError(ValueError):
    def __init__(self, message: str, status_code: int = 422) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass(frozen=True)
class PreparedImage:
    original_name: str
    mime_type: str
    extension: str
    data: bytes


class LocalStorage:
    def __init__(self, root: Path, max_image_bytes: int) -> None:
        self.root = root.resolve()
        self.max_image_bytes = max_image_bytes

    def initialize(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)

    async def prepare(self, upload: UploadFile) -> PreparedImage:
        if upload.content_type not in ALLOWED_MIME_TYPES:
            raise StorageValidationError(
                "Only JPEG, PNG, and WebP images are supported.", status_code=415
            )

        data = await upload.read(self.max_image_bytes + 1)
        if not data:
            raise StorageValidationError("Uploaded images cannot be empty.")
        if len(data) > self.max_image_bytes:
            raise StorageValidationError(
                f"Each image must be at most {self.max_image_bytes} bytes.",
                status_code=413,
            )

        try:
            with PillowImage.open(BytesIO(data)) as image:
                detected_format = image.format
                image.verify()
        except (UnidentifiedImageError, OSError, PillowImage.DecompressionBombError) as exc:
            raise StorageValidationError("The uploaded file is not a valid image.") from exc

        if detected_format not in FORMAT_DETAILS:
            raise StorageValidationError(
                "Only JPEG, PNG, and WebP images are supported.", status_code=415
            )
        detected_mime, extension = FORMAT_DETAILS[detected_format]
        if detected_mime != upload.content_type:
            raise StorageValidationError("The image content does not match its MIME type.")

        return PreparedImage(
            original_name=(upload.filename or "image")[:255],
            mime_type=detected_mime,
            extension=extension,
            data=data,
        )

    def save(self, listing_id: str, image: PreparedImage) -> str:
        directory = self.root / listing_id
        directory.mkdir(parents=True, exist_ok=True)
        filename = f"{uuid4()}{image.extension}"
        path = directory / filename
        path.write_bytes(image.data)
        return str(PurePosixPath(listing_id, filename))

    def read(self, storage_name: str) -> bytes:
        return self._safe_path(storage_name).read_bytes()

    def delete(self, storage_name: str) -> None:
        path = self._safe_path(storage_name)
        path.unlink(missing_ok=True)
        try:
            path.parent.rmdir()
        except OSError:
            pass

    def delete_listing(self, listing_id: str) -> None:
        directory = (self.root / listing_id).resolve()
        if directory.parent != self.root:
            raise ValueError("Invalid listing storage path")
        if directory.exists():
            rmtree(directory)

    def _safe_path(self, storage_name: str) -> Path:
        path = (self.root / Path(storage_name)).resolve()
        if self.root not in path.parents:
            raise ValueError("Invalid storage path")
        return path

