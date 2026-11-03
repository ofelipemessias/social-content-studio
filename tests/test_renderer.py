import os

from content_studio.profiles import BrandProfile
from content_studio.renderer import (CARD_H, CARD_W, CardRenderer, parse_bold,
                                     render_carousel)


def _profile(theme="light"):
    return BrandProfile(name="Aurora Advocacia", handle="@aurora.advocacia",
                        niche="direito", audience="todos", theme=theme)


def test_parse_bold_marks_segments():
    runs = parse_bold("ola **mundo** legal")
    assert ("mundo", True) in runs
    assert ("ola ", False) in runs
    assert (" legal", False) in runs


def test_parse_bold_unmatched_marker_is_literal():
    runs = parse_bold("texto com ** solto")
    assert all(not bold for _, bold in runs)
    assert "**" in "".join(t for t, _ in runs)


def test_render_slide_dimensions(tmp_path):
    slide = {"kind": "cover", "heading": "Titulo", "body": "corpo **forte**"}
    img = CardRenderer(_profile()).render_slide(slide, 0, 1)
    assert img.size == (CARD_W, CARD_H)


def test_themes_change_background(tmp_path):
    slide = {"kind": "content", "heading": "T", "body": "B"}
    light = CardRenderer(_profile("light")).render_slide(slide, 0, 1)
    dark = CardRenderer(_profile("dark")).render_slide(slide, 0, 1)
    assert light.getpixel((5, 5)) != dark.getpixel((5, 5))


def test_avatar_uses_brand_color():
    p = _profile()
    p.primary_color = "#FF0000"
    img = CardRenderer(p).render_slide({"kind": "content", "heading": "T", "body": "B"}, 0, 1)
    # centro do avatar: circulo de raio 48 a partir de (80, 80)
    assert img.getpixel((128, 128)) == (255, 0, 0)


def test_render_carousel_writes_pngs_and_json(tmp_path):
    from content_studio.generator import generate_script
    script = generate_script(_profile(), "tema", max_slides=4)
    paths = render_carousel(script, _profile(), str(tmp_path))
    assert len(paths) == 4
    for path in paths:
        assert path.endswith(".png") and os.path.getsize(path) > 1000
