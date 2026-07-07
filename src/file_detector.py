from pathlib import Path
from config import MEDIA_EXTENSIONS, FUTURE_DOCUMENT_EXTENSIONS


def detect_file_category(file_path: str | Path) -> str:
    ext = Path(file_path).suffix.lower()
    if ext in MEDIA_EXTENSIONS:
        return "media"
    if ext in FUTURE_DOCUMENT_EXTENSIONS:
        return "future_document"
    return "generic_binary"


def get_delivery_type(file_path: str | Path) -> str:
    category = detect_file_category(file_path)
    if category == "media":
        return "type_1_media"
    if category == "future_document":
        return "type_2_future_document"
    return "generic_binary"
