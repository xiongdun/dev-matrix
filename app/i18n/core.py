import json
import os
from functools import lru_cache
from typing import Dict, Optional

from app.config import get_settings


@lru_cache()
def _load_locale(locale: str) -> Dict[str, str]:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, "locales", f"{locale}.json")
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


_current_locale: Optional[str] = None


def get_locale() -> str:
    global _current_locale
    if _current_locale is not None:
        return _current_locale
    return get_settings().default_locale


def set_locale(locale: str) -> None:
    global _current_locale
    _current_locale = locale


def get_text(key: str, locale: Optional[str] = None, **kwargs) -> str:
    loc = locale or get_locale()
    translations = _load_locale(loc)
    text = translations.get(key, key)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass
    return text
