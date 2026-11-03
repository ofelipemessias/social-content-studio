"""CLI do social-content-studio.

Exemplo:
  python -m content_studio.cli generate \
      --profile samples/perfil-aurora.json \
      --topic "5 direitos do trabalhador demitido sem justa causa" \
      --out out/
"""

from __future__ import annotations

import argparse
import sys

from .carousel import DEFAULT_RULESET, create_carousel
from .compliance import summarize
from .profiles import load_profile


def _cmd_generate(args: argparse.Namespace) -> int:
    profile = load_profile(args.profile)
    if args.theme:
        profile.theme = args.theme
    try:
        result = create_carousel(
            profile, args.topic, mode=args.mode, max_slides=args.max_slides,
            ruleset_path=args.ruleset, strict=args.strict, out_dir=args.out,
            theme=args.theme)
    except ValueError as exc:
        print(f"REJEITADO: {exc}", file=sys.stderr)
        return 2

    n_errors, n_warnings = summarize(result.findings)
    for f in result.findings:
        print(f"[{f.severity}] slide {f.slide + 1}: regra {f.rule_id} "
              f"-> \"{f.excerpt}\" {f.suggestion}".rstrip())
    if n_errors:
        status = "REJEITADO"
    elif n_warnings:
        status = "APROVADO COM RESSALVAS"
    else:
        status = "APROVADO"
    print(f"Conformidade: {status} "
          f"({n_errors} erro(s), {n_warnings} aviso(s))")
    print(f"{len(result.image_paths)} slide(s) gerados em {args.out}/ "
          f"+ carousel.json (fonte: {result.script.get('source')})")
    return 1 if n_errors else 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="social-content-studio",
        description="Gera carrosseis de rede social (roteiro + PNGs) a partir "
                    "de um perfil de marca e um tema.")
    sub = parser.add_subparsers(dest="command", required=True)
    gen = sub.add_parser("generate", help="gera um carrossel completo")
    gen.add_argument("--profile", required=True, help="JSON do perfil de marca")
    gen.add_argument("--topic", required=True, help="tema do carrossel")
    gen.add_argument("--mode", default="auto", choices=["auto", "offline", "ai"],
                     help="geracao do roteiro (padrao: auto)")
    gen.add_argument("--max-slides", type=int, default=6)
    gen.add_argument("--ruleset", default=DEFAULT_RULESET,
                     help="ruleset de conformidade em JSON ('' desativa)")
    gen.add_argument("--strict", action="store_true",
                     help="falha (exit 2) se houver erro de conformidade")
    gen.add_argument("--theme", choices=["light", "dark", "paper"],
                     help="sobrescreve o tema do perfil")
    gen.add_argument("--out", default="out", help="diretorio de saida")
    gen.set_defaults(func=_cmd_generate)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
