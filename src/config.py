from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = PROJECT_ROOT / "input_files"
STORAGE_DIR = PROJECT_ROOT / "storage"
ENCRYPTED_DIR = STORAGE_DIR / "encrypted_chunks"
DECRYPTED_DIR = STORAGE_DIR / "decrypted_chunks"
RECOVERED_DIR = STORAGE_DIR / "recovered_files"
MANIFEST_DIR = STORAGE_DIR / "manifests"
LOG_DIR = PROJECT_ROOT / "logs"
REPORT_DIR = PROJECT_ROOT / "reports"
LOG_FILE = LOG_DIR / "transfer.log"
SECRET_KEY_FILE = PROJECT_ROOT / "secret.key"

SYSTEM_NAME = "FSTE - FastSecure Transfer Engine"
ALGORITHM = "AES-GCM"
HASH_ALGORITHM = "SHA-256"

# 4 MB is a good default for classroom demo and medium files.
# It avoids loading the whole file into RAM and keeps the number of chunks manageable.
DEFAULT_CHUNK_SIZE = 4 * 1024 * 1024

MEDIA_EXTENSIONS = {".mp3", ".wav", ".mp4", ".mkv", ".mov", ".avi", ".wmv", ".flac", ".aac", ".ogg", ".webm"}
FUTURE_DOCUMENT_EXTENSIONS = {".docx", ".pptx", ".xlsx", ".pdf", ".zip", ".rar", ".7z"}

for directory in [INPUT_DIR, ENCRYPTED_DIR, DECRYPTED_DIR, RECOVERED_DIR, MANIFEST_DIR, LOG_DIR, REPORT_DIR]:
    directory.mkdir(parents=True, exist_ok=True)
