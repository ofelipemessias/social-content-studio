"""Geracao do roteiro do carrossel: templates offline ou IA (opcional).

O modo offline usa bancos de templates por tom de voz e nao precisa de
nenhuma chave nem de rede - e o modo usado nos testes e na demo.
O modo "ai" chama a API da Anthropic com a chave em ANTHROPIC_API_KEY.
"""

from __future__ import annotations

import os

HOOKS = {
    "didatico": [
        "{topic}: o guia rapido que faltava",
        "Entenda {topic} de uma vez por todas",
        "{topic} explicado sem juridiques",
    ],
    "provocador": [
        "Voce pode estar errando em {topic} (e nem sabe)",
        "Pare de acreditar em tudo que le sobre {topic}",
        "Ninguem te conta isso sobre {topic}",
    ],
    "institucional": [
        "{topic}: informacao de qualidade para voce",
        "Nossa analise sobre {topic}",
        "{topic}: o que voce precisa saber",
    ],
}

# Cada item: (titulo do slide, corpo). Use **duplo asterisco** para destacar.
BODIES = {
    "didatico": [
        ("Por que isso importa",
         "{topic} gera muita duvida em {audience}. Entender o tema e o "
         "**primeiro passo** para nao sair no prejuizo."),
        ("1. Comece pelo basico",
         "Antes de qualquer decisao, entenda **como a lei trata** esse assunto. "
         "Informacao de qualidade evita erros caros."),
        ("2. Reuna documentos",
         "Contratos, mensagens, comprovantes: **guarde tudo**. Na pratica, a "
         "maioria dos casos se decide pela qualidade das provas."),
        ("3. Respeite os prazos",
         "Todo direito tem **prazo**. Perder o prazo pode significar perder o "
         "proprio direito - anote as datas importantes."),
        ("4. Evite erros comuns",
         "O erro mais comum e agir por impulso ou por dica de rede social. "
         "**Cada caso tem detalhes** que mudam completamente o resultado."),
        ("5. Procure orientacao",
         "Um profissional de {niche} analisa o seu caso concreto e indica "
         "**o melhor caminho**. Informacao generica nao substitui analise individual."),
    ],
    "provocador": [
        ("O mito",
         "Circula muita desinformacao sobre {topic}. O que voce le por ai "
         "pode estar **completamente errado** - e te custando caro."),
        ("A realidade",
         "Na pratica, {audience} raramente conhecem **todos os seus direitos** "
         "nesse tema. E e exatamente ai que mora o problema."),
        ("O custo do erro",
         "Errar aqui nao e so chato: pode significar **perda de dinheiro, de "
         "prazo e ate do proprio direito**."),
        ("O que quase ninguem faz",
         "Pouca gente para para **reunir provas e entender prazos** antes de "
         "agir. Quem faz isso sai na frente."),
        ("A saida",
         "Nao existe formula magica: existe **informacao correta** e analise "
         "do seu caso por quem entende de {niche}."),
    ],
    "institucional": [
        ("Contexto",
         "{topic} e um tema relevante para {audience}. Preparamos esta analise "
         "para **esclarecer os pontos principais**."),
        ("Panorama",
         "A legislacao sobre o tema e clara nos pontos centrais, mas a "
         "aplicacao pratica **exige atencao aos detalhes** de cada situacao."),
        ("Pontos de atencao",
         "Documentacao completa e respeito aos **prazos legais** sao fatores "
         "decisivos na maioria dos casos."),
        ("Nossa recomendacao",
         "Recomendamos **avaliacao individualizada**: cada caso apresenta "
         "particularidades que influenciam diretamente o resultado."),
        ("Compromisso",
         "Conteudo informativo produzido com responsabilidade. Para o seu caso "
         "concreto, consulte um profissional de {niche}."),
    ],
}

CTA_HEADING = "Gostou?"


def _pick(bank: list, seed_text: str, offset: int = 0):
    """Escolhe um item do banco de forma deterministica a partir do tema."""
    idx = (sum(ord(c) for c in seed_text) + offset) % len(bank)
    return bank[idx]


def generate_script(profile, topic: str, max_slides: int = 6) -> dict:
    """Gera o roteiro do carrossel com templates offline.

    Retorna {"title", "topic", "slides": [{"kind", "heading", "body"}]}.
    kinds: cover (1), content (meio), cta (ultimo).
    """
    topic = topic.strip()
    if not topic:
        raise ValueError("topic nao pode ser vazio")
    if max_slides < 3:
        raise ValueError("max_slides minimo e 3 (capa, conteudo, CTA)")

    tone = profile.tone
    ctx = {
        "topic": topic,
        "niche": profile.niche,
        "audience": profile.audience,
        "name": profile.name,
    }

    hook = _pick(HOOKS[tone], topic)
    slides = [{"kind": "cover", "heading": hook.format(**ctx),
               "body": "Arraste para o lado e entenda **o essencial** em "
                       "menos de um minuto."}]

    body_bank = BODIES[tone]
    n_content = min(max_slides - 2, len(body_bank))
    start = sum(ord(c) for c in topic) % len(body_bank)
    for i in range(n_content):
        heading, body = body_bank[(start + i) % len(body_bank)]
        slides.append({"kind": "content", "heading": heading.format(**ctx),
                       "body": body.format(**ctx)})

    slides.append({"kind": "cta", "heading": CTA_HEADING, "body": profile.cta})
    return {"title": f"{topic} - {profile.name}", "topic": topic,
            "slides": slides, "source": "offline"}


def generate_script_ai(profile, topic: str, max_slides: int = 6) -> dict:
    """Gera o roteiro via API da Anthropic (opcional).

    Requer a variavel de ambiente ANTHROPIC_API_KEY e o pacote `anthropic`.
    """
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("modo ai requer ANTHROPIC_API_KEY no ambiente")
    try:
        import anthropic
    except ImportError as exc:
        raise RuntimeError("modo ai requer o pacote `anthropic` "
                           "(pip install anthropic)") from exc

    prompt = (
        "Crie um carrossel de Instagram em portugues para o perfil abaixo.\n"
        f"Perfil: {profile.name} ({profile.handle}), nicho: {profile.niche}, "
        f"publico: {profile.audience}, tom: {profile.tone}.\n"
        f"Tema: {topic}.\n"
        f"Responda SOMENTE com JSON no formato "
        '{"slides": [{"kind": "cover|content|cta", "heading": str, '
        '"body": str}]} com no maximo ' + str(max_slides) + " slides, "
        "primeiro cover e ultimo cta. Use **texto** para destacar trechos "
        "importantes no body."
    )
    client = anthropic.Anthropic(api_key=key)
    msg = client.messages.create(
        model="claude-sonnet-4-5", max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )
    import json

    text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
    data = json.loads(text[text.index("{"): text.rindex("}") + 1])
    slides = []
    for i, s in enumerate(data["slides"]):
        kind = s.get("kind") or ("cover" if i == 0 else
                                 "cta" if i == len(data["slides"]) - 1 else "content")
        slides.append({"kind": kind, "heading": s["heading"], "body": s["body"]})
    return {"title": f"{topic} - {profile.name}", "topic": topic,
            "slides": slides, "source": "ai"}


def generate(profile, topic: str, mode: str = "auto", max_slides: int = 6) -> dict:
    """mode: 'offline', 'ai' ou 'auto' (ai se houver chave, senao offline)."""
    if mode not in ("offline", "ai", "auto"):
        raise ValueError(f"mode invalido: {mode!r}")
    if mode == "ai" or (mode == "auto" and os.environ.get("ANTHROPIC_API_KEY")):
        return generate_script_ai(profile, topic, max_slides)
    return generate_script(profile, topic, max_slides)
