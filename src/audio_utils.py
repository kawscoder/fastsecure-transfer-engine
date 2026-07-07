from pathlib import Path
import wave


def get_audio_duration_seconds(file_path: str | Path) -> float | None:
    """Return WAV duration when possible. For MP3/others, return None without failing."""
    path = Path(file_path)
    if path.suffix.lower() != ".wav":
        return None
    try:
        with wave.open(str(path), "rb") as wav:
            frames = wav.getnframes()
            rate = wav.getframerate()
            if rate == 0:
                return None
            return round(frames / float(rate), 3)
    except Exception:
        return None
