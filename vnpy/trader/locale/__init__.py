from __future__ import annotations
from __future__ import annotations
import gettext
from pathlib import Path


localedir: Path = Path(__file__).parent

translations: gettext.GNUTranslations | gettext.NullTranslations = gettext.translation("vnpy", localedir=localedir, fallback=True)

_ = translations.gettext
