import json
import os

from content_studio.cli import main


def test_cli_generates_carousel(tmp_path):
    out = tmp_path / "out"
    code = main(["generate", "--profile", "samples/perfil-aurora.json",
                 "--topic", "5 direitos do trabalhador demitido",
                 "--mode", "offline", "--out", str(out)])
    assert code == 0
    script = json.loads((out / "carousel.json").read_text(encoding="utf-8"))
    assert script["slides"]
    assert any(p.name.startswith("slide-") for p in out.iterdir())


def test_cli_strict_blocks_violation(tmp_path, capsys):
    code = main(["generate", "--profile", "samples/perfil-aurora.json",
                 "--topic", "garantimos a vitoria no seu processo",
                 "--mode", "offline", "--strict", "--out", str(tmp_path / "o")])
    # 'garantimos... vitoria' dispara a regra sem-promessa-de-resultado
    # (o topic entra no heading da capa)
    assert code == 2
    assert "REJEITADO" in capsys.readouterr().err


def test_cli_theme_override(tmp_path):
    out = tmp_path / "out"
    code = main(["generate", "--profile", "samples/perfil-aurora.json",
                 "--topic", "tema", "--theme", "dark", "--out", str(out)])
    assert code == 0
    from PIL import Image
    img = Image.open(out / "slide-1.png")
    assert img.getpixel((5, 5)) != (255, 255, 255)
