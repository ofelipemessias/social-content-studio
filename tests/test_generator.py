import pytest

from content_studio.generator import generate, generate_script
from content_studio.profiles import BrandProfile


@pytest.fixture
def profile():
    return BrandProfile(name="Aurora Advocacia", handle="aurora.advocacia",
                        niche="direito trabalhista", audience="trabalhadores CLT")


def test_script_has_cover_content_and_cta(profile):
    script = generate_script(profile, "direitos do trabalhador")
    kinds = [s["kind"] for s in script["slides"]]
    assert kinds[0] == "cover"
    assert kinds[-1] == "cta"
    assert "content" in kinds


def test_max_slides_respected(profile):
    script = generate_script(profile, "tema qualquer", max_slides=4)
    assert len(script["slides"]) == 4


def test_max_slides_minimum(profile):
    with pytest.raises(ValueError):
        generate_script(profile, "tema", max_slides=2)


def test_empty_topic_rejected(profile):
    with pytest.raises(ValueError):
        generate_script(profile, "   ")


def test_bodies_have_bold_highlights(profile):
    script = generate_script(profile, "tema")
    content = [s for s in script["slides"] if s["kind"] == "content"]
    assert any("**" in s["body"] for s in content)


def test_offline_mode_needs_no_key(profile, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    script = generate(profile, "tema", mode="offline")
    assert script["source"] == "offline"


def test_invalid_mode_rejected(profile):
    with pytest.raises(ValueError):
        generate(profile, "tema", mode="magic")


def test_tone_variations_produce_different_hooks(profile):
    hooks = set()
    for tone in ("didatico", "provocador", "institucional"):
        profile.tone = tone
        hooks.add(generate_script(profile, "mesmo tema")["slides"][0]["heading"])
    assert len(hooks) == 3
