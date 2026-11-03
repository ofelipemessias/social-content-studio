import pytest

from content_studio.compliance import (check_script, has_errors, load_ruleset,
                                       summarize)


@pytest.fixture
def rules():
    return load_ruleset("content_studio/rules/oab_publicidade.json")


def _script(body):
    return {"slides": [{"kind": "content", "heading": "Titulo", "body": body}]}


def test_promessa_de_resultado_e_erro(rules):
    findings = check_script(_script("Nos garantimos o resultado do seu caso!"), rules)
    assert has_errors(findings)
    assert findings[0].rule_id == "sem-promessa-de-resultado"


def test_texto_limpo_sem_erros(rules):
    findings = check_script(_script("Entenda seus direitos de forma informativa."), rules)
    assert not has_errors(findings)


def test_warning_nao_bloqueia(rules):
    findings = check_script(_script("Corra para entender seus direitos."), rules)
    assert findings and all(f.severity == "warning" for f in findings)
    assert not has_errors(findings)
    errors, warnings = summarize(findings)
    assert (errors, warnings) == (0, len(findings))


def test_achado_aponta_slide_e_trecho(rules):
    script = {"slides": [
        {"kind": "cover", "heading": "Ok", "body": "texto limpo"},
        {"kind": "content", "heading": "Ok", "body": "somos o melhor escritorio"},
    ]}
    findings = check_script(script, rules)
    assert findings[0].slide == 1
    assert "melhor escritorio" in findings[0].excerpt.lower()
