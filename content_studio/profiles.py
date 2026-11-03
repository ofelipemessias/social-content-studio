"""Perfil de marca usado na geracao e no render dos carrosseis."""

from __future__ import annotations

import json
from dataclasses import dataclass, field

VALID_TONES = ("didatico", "provocador", "institucional")
VALID_THEMES = ("light", "dark", "paper")


@dataclass
class BrandProfile:
    """Dados publicos de uma marca (escritorio, empresa, criador)."""

    name: str
    handle: str
    niche: str
    audience: str
    tone: str = "didatico"
    primary_color: str = "#1D4ED8"
    theme: str = "light"
    cta: str = "Salve este post e compartilhe com quem precisa."
    initials: str = field(default="")

    def __post_init__(self) -> None:
        if self.tone not in VALID_TONES:
            raise ValueError(f"tone invalido: {self.tone!r} (use {VALID_TONES})")
        if self.theme not in VALID_THEMES:
            raise ValueError(f"theme invalido: {self.theme!r} (use {VALID_THEMES})")
        if not self.handle.startswith("@"):
            self.handle = "@" + self.handle
        if not self.initials:
            words = [w for w in self.name.split() if w]
            self.initials = "".join(w[0] for w in words[:2]).upper()

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "handle": self.handle,
            "niche": self.niche,
            "audience": self.audience,
            "tone": self.tone,
            "primary_color": self.primary_color,
            "theme": self.theme,
            "cta": self.cta,
            "initials": self.initials,
        }


def load_profile(path: str) -> BrandProfile:
    """Carrega um BrandProfile de um arquivo JSON."""
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    known = {f for f in BrandProfile.__dataclass_fields__ if f != "initials"}
    return BrandProfile(**{k: v for k, v in data.items() if k in known})
