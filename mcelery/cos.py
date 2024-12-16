from pathlib import Path
import shutil
from typing import Optional, Callable

cos_local = Path("/cos")


def get_local_path(key: str, rewriter: Callable[[str], Path] = None) -> Path:
    if rewriter is None:
        path = cos_local / key
    else:
        path = rewriter(key)
        if path is None:
            path = cos_local / key
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def download_cos_file(key: str, rewriter: Callable[[str], Path] = None) -> Optional[Path]:
    path = get_local_path(key, rewriter)
    
    if not path.exists() and Path(key).exists():
        shutil.copy(key, path)
    return path


def upload_cos_file(key: str, rewriter: Callable[[str], Path] = None):
    pass