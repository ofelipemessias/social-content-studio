"""Renderizador de cards PNG 1080x1350 estilo tweet com Pillow.

Cada slide vira um card: cabecalho com avatar (iniciais), nome, @handle e
selo; corpo com quebra automatica e trechos em **negrito** destacados;
rodape com indicador de progresso (bolinhas). Temas: light, dark, paper.
Fontes DejaVu embutidas (licenca em content_studio/fonts/).
"""

from __future__ import annotations

import os
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

CARD_W, CARD_H = 1080, 1350
MARGIN = 80
FONTS_DIR = os.path.join(os.path.dirname(__file__), "fonts")

THEMES = {
    "light": {"bg": "#FFFFFF", "text": "#0F1419", "secondary": "#536471"},
    "dark": {"bg": "#15202B", "text": "#FFFFFF", "secondary": "#8B98A5"},
    "paper": {"bg": "#F7F3EB", "text": "#2B2B2B", "secondary": "#6B6255"},
}


def parse_bold(text: str) -> list[tuple[str, bool]]:
    """Divide o texto em segmentos (texto, em_negrito) a partir de **marcadores**.

    Um '**' sem par e tratado como texto literal. Quebras de linha viram espaco.
    """
    text = text.replace("\n", " ")
    runs: list[tuple[str, bool]] = []
    parts = text.split("**")
    if len(parts) % 2 == 0:
        # numero impar de marcadores: o ultimo '**' ficou sem par -> literal
        parts[-2] = parts[-2] + "**" + parts[-1]
        parts.pop()
    for i, part in enumerate(parts):
        if part:
            runs.append((part, i % 2 == 1))
    return runs


def _tokenize(runs: list[tuple[str, bool]]) -> list[tuple[str, bool]]:
    tokens: list[tuple[str, bool]] = []
    for text, bold in runs:
        parts = text.split(" ")
        for i, part in enumerate(parts):
            token = part + (" " if i < len(parts) - 1 else "")
            if token:
                tokens.append((token, bold))
    return tokens


class CardRenderer:
    def __init__(self, profile, theme: Optional[str] = None,
                 width: int = CARD_W, height: int = CARD_H):
        self.profile = profile
        self.width, self.height = width, height
        self.theme = THEMES[theme or profile.theme]
        self.accent = profile.primary_color
        self._fonts: dict[tuple[int, bool], ImageFont.FreeTypeFont] = {}

    def _font(self, size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
        key = (size, bold)
        if key not in self._fonts:
            name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
            self._fonts[key] = ImageFont.truetype(os.path.join(FONTS_DIR, name), size)
        return self._fonts[key]

    def _wrap(self, draw: ImageDraw.ImageDraw, runs, size: int, max_width: int):
        """Quebra os segmentos em linhas que cabem em max_width."""
        lines: list[list[tuple[str, bool]]] = []
        cur: list[tuple[str, bool]] = []
        width = 0.0
        for token, bold in _tokenize(runs):
            font = self._font(size, bold)
            tw = draw.textlength(token, font=font)
            if cur and width + tw > max_width:
                lines.append(cur)
                cur, width = [], 0.0
            cur.append((token, bold))
            width += tw
        if cur:
            lines.append(cur)
        return lines

    def _draw_lines(self, draw, lines, x: int, y: int, size: int, fill: str) -> int:
        """Desenha as linhas; retorna o y da proxima linha."""
        line_h = int(size * 1.4)
        for line in lines:
            cursor = x
            for token, bold in line:
                font = self._font(size, bold)
                draw.text((cursor, y), token, font=font, fill=fill)
                cursor += draw.textlength(token, font=font)
            y += line_h
        return y

    def _draw_header(self, draw) -> None:
        p = self.profile
        cy = MARGIN + 48
        # avatar: circulo com iniciais na cor da marca
        draw.ellipse([MARGIN, MARGIN, MARGIN + 96, MARGIN + 96], fill=self.accent)
        font_init = self._font(40, bold=True)
        draw.text((MARGIN + 48, cy), p.initials, font=font_init,
                  fill="#FFFFFF", anchor="mm")
        # nome + selo de verificado
        x = MARGIN + 128
        font_name = self._font(40, bold=True)
        draw.text((x, MARGIN + 6), p.name, font=font_name, fill=self.theme["text"])
        name_w = draw.textlength(p.name, font=font_name)
        bx, by = x + name_w + 14, MARGIN + 6 + 22
        draw.ellipse([bx, by - 16, bx + 32, by + 16], fill=self.accent)
        draw.line([(bx + 8, by), (bx + 14, by + 7)], fill="#FFFFFF", width=4)
        draw.line([(bx + 14, by + 7), (bx + 25, by - 8)], fill="#FFFFFF", width=4)
        # handle
        draw.text((x, MARGIN + 58), p.handle, font=self._font(32),
                  fill=self.theme["secondary"])
        # divisor
        draw.line([(MARGIN, MARGIN + 150), (self.width - MARGIN, MARGIN + 150)],
                  fill=self.theme["secondary"], width=2)

    def _draw_footer(self, draw, index: int, total: int) -> None:
        spacing, r = 40, 9
        total_w = (total - 1) * spacing
        x0 = (self.width - total_w) // 2
        y = self.height - 90
        for i in range(total):
            color = self.accent if i == index else self.theme["secondary"]
            cx = x0 + i * spacing
            draw.ellipse([cx - r, y - r, cx + r, y + r], fill=color)

    def render_slide(self, slide: dict, index: int, total: int) -> Image.Image:
        img = Image.new("RGB", (self.width, self.height), self.theme["bg"])
        draw = ImageDraw.Draw(img)
        self._draw_header(draw)
        max_w = self.width - 2 * MARGIN
        kind = slide.get("kind", "content")
        y = MARGIN + 210

        if kind == "cover":
            head_size = 68
        elif kind == "cta":
            head_size = 56
        else:
            head_size = 48

        head_lines = self._wrap(draw, [(slide["heading"], True)], head_size, max_w)
        y = self._draw_lines(draw, head_lines, MARGIN, y, head_size,
                             self.theme["text"])
        y += 36

        body_size = 40 if kind != "cover" else 38
        body_lines = self._wrap(draw, parse_bold(slide["body"]), body_size, max_w)
        body_color = self.theme["text"] if kind != "cover" else self.theme["secondary"]
        y = self._draw_lines(draw, body_lines, MARGIN, y, body_size, body_color)

        if kind == "cta":
            y += 48
            label = self.profile.handle
            font_btn = self._font(36, bold=True)
            tw = draw.textlength(label, font=font_btn)
            draw.rounded_rectangle(
                [MARGIN, y, MARGIN + tw + 72, y + 88], radius=44,
                fill=self.accent)
            draw.text((MARGIN + 36, y + 24), label, font=font_btn, fill="#FFFFFF")

        self._draw_footer(draw, index, total)
        return img


def render_carousel(script: dict, profile, out_dir: str,
                    theme: Optional[str] = None) -> list[str]:
    """Renderiza todos os slides em PNG. Retorna os caminhos gerados."""
    os.makedirs(out_dir, exist_ok=True)
    renderer = CardRenderer(profile, theme=theme)
    slides = script["slides"]
    paths = []
    for i, slide in enumerate(slides):
        img = renderer.render_slide(slide, i, len(slides))
        path = os.path.join(out_dir, f"slide-{i + 1}.png")
        img.save(path)
        paths.append(path)
    return paths
