"""Camada de conformidade de conteudo: regras configuraveis aplicadas ao roteiro.

As regras ficam em JSON (ruleset) e sao expressoes regulares aplicadas ao
titulo e corpo de cada slide. Cada regra tem severidade "error" (bloqueia)
ou "warning" (alerta). O ruleset de exemplo em rules/ e inspirado em boas
praticas de publicidade profissional - e um EXEMPLO, nao um parecer juridico.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass


@dataclass
class ComplianceRule:
    id: str
    description: str
    pattern: str
    severity: str = "error"      # "error" | "warning"
    suggestion: str = ""

    def __post_init__(self) -> None:
        if self.severity not in ("error", "warning"):
            raise ValueError(f"severity invalida: {self.severity!r}")
        self.regex = re.compile(self.pattern, re.IGNORECASE)


@dataclass
class Finding:
    rule_id: str
    severity: str
    slide: int          # indice do slide (0 = capa)
    excerpt: str        # trecho encontrado
    suggestion: str


def load_ruleset(path: str) -> list[ComplianceRule]:
    """Carrega um ruleset JSON: {"name", "rules": [{"id", ...}]}."""
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    return [ComplianceRule(**r) for r in data["rules"]]


def check_script(script: dict, rules: list[ComplianceRule]) -> list[Finding]:
    """Aplica as regras a todos os slides. Retorna os achados (pode ser vazio)."""
    findings: list[Finding] = []
    for idx, slide in enumerate(script.get("slides", [])):
        text = f"{slide.get('heading', '')}\n{slide.get('body', '')}"
        for rule in rules:
            for match in rule.regex.finditer(text):
                findings.append(Finding(
                    rule_id=rule.id,
                    severity=rule.severity,
                    slide=idx,
                    excerpt=match.group(0),
                    suggestion=rule.suggestion,
                ))
    return findings


def has_errors(findings: list[Finding]) -> bool:
    return any(f.severity == "error" for f in findings)


def summarize(findings: list[Finding]) -> tuple[int, int]:
    """Retorna (n_erros, n_warnings)."""
    errors = sum(1 for f in findings if f.severity == "error")
    return errors, len(findings) - errors
