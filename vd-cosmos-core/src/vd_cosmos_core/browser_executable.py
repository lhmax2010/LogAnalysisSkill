"""Shared verifier/test choice: explicit path, otherwise the installed wrapper."""
import os
from pathlib import Path
import shutil


def resolve(explicit=None):
    value = explicit or os.environ.get('VD_COSMOS_CHROME')
    if not value:
        value = shutil.which('google-chrome') or shutil.which('google-chrome-stable')
    if not value:
        value = next((p for p in ('/opt/google/chrome/google-chrome','/usr/bin/chromium','/usr/bin/chromium-browser') if Path(p).is_file()), None)
    if not value:
        return None
    path = Path(value).resolve()
    return str(path) if path.is_file() and os.access(path,os.X_OK) else None
