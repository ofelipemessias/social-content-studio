"""Orquestracao: perfil + tema -> roteiro -> conformidade -> PNGs."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

from .compliance import check_script, has_errors, load_ruleset
from .generator import generate
from .renderer import render_carousel

DEFAULT_RULESET = os.path.join(os.path.dirname(__file__),
                               "rules", "oab_publicidade.json")


@dataclass
class CarouselResult:
    script: dict
    findings: list = field(default_factory=list)
    image_paths: list = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return has_errors(self.findings)


def create_carousel(profile, topic: str, mode: str = "auto",
                    max_slides: int = 6, ruleset_path: str = DEFAULT_RULESET,
                    strict: bool = False, out_dir: str = "out",
                    theme: str = None) -> CarouselResult:
    """Fluxo completo. Com strict=True, erros de conformidade levantam ValueError."""
    script = generate(profile, topic, mode=mode, max_slides=max_slides)
    rules = load_ruleset(ruleset_path) if ruleset_path else []
    findings = check_script(script, rules)
    if strict and has_errors(findings):
        raise ValueError(
            f"roteiro reprovado na conformidade: "
            f"{sum(1 for f in findings if f.severity == 'error')} erro(s)")
    paths = render_carousel(script, profile, out_dir, theme=theme)
    json_path = os.path.join(out_dir, "carousel.json")
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(script, fh, ensure_ascii=False, indent=2)
    return CarouselResult(script=script, findings=findings, image_paths=paths)
