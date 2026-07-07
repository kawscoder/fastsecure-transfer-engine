from pathlib import Path
from dataclasses import dataclass


@dataclass
class ChunkInfo:
    sequence_number: int
    offset: int
    plain_size: int
    data: bytes


def iter_file_chunks(file_path: str | Path, chunk_size: int):
    """Yield chunks without loading the whole file into memory."""
    path = Path(file_path)
    sequence = 1
    offset = 0
    with path.open("rb") as f:
        while True:
            data = f.read(chunk_size)
            if not data:
                break
            yield ChunkInfo(sequence_number=sequence, offset=offset, plain_size=len(data), data=data)
            offset += len(data)
            sequence += 1


def count_chunks(file_size: int, chunk_size: int) -> int:
    if file_size == 0:
        return 0
    return (file_size + chunk_size - 1) // chunk_size
