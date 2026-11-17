from pathlib import Path

import customtkinter as ctk
from PIL import Image, ImageDraw

PASTA_ICONES = Path(__file__).resolve().parent / "icons"


def carregar_icones() -> dict[str, ctk.CTkImage]:
    PASTA_ICONES.mkdir(parents=True, exist_ok=True)

    especificacoes = {
        "logo": ((28, 28), _desenhar_logo, "#3b82f6", "#60a5fa"),
        "conversao": ((20, 20), _desenhar_conversao, "#1f2937", "#e5e7eb"),
        "compactacao": ((20, 20), _desenhar_compactacao, "#1f2937", "#e5e7eb"),
        "historico": ((20, 20), _desenhar_historico, "#1f2937", "#e5e7eb"),
        "recuperar": ((16, 16), _desenhar_recuperar, "#ffffff", "#ffffff"),
    }

    icones: dict[str, ctk.CTkImage] = {}
    for nome, (tamanho, funcao_desenho, cor_claro, cor_escuro) in especificacoes.items():
        caminho_claro = PASTA_ICONES / f"{nome}_light.png"
        caminho_escuro = PASTA_ICONES / f"{nome}_dark.png"

        if not caminho_claro.exists():
            funcao_desenho(cor_claro).save(caminho_claro, format="PNG")
        if not caminho_escuro.exists():
            funcao_desenho(cor_escuro).save(caminho_escuro, format="PNG")

        img_claro = Image.open(caminho_claro)
        img_escuro = Image.open(caminho_escuro)
        icones[nome] = ctk.CTkImage(
            light_image=img_claro,
            dark_image=img_escuro,
            size=tamanho,
        )

    return icones


def _criar_tela(cor: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def _desenhar_logo(cor: str) -> Image.Image:
    img, draw = _criar_tela(cor)
    pontos = [(74, 10), (26, 72), (62, 72), (52, 118), (102, 54), (66, 54)]
    draw.polygon(pontos, fill=cor)
    return img


def _desenhar_conversao(cor: str) -> Image.Image:
    img, draw = _criar_tela(cor)
    # Seta superior (esquerda -> direita)
    draw.line([(20, 42), (96, 42)], fill=cor, width=12)
    draw.polygon([(82, 22), (112, 42), (82, 62)], fill=cor)
    # Seta inferior (direita -> esquerda)
    draw.line([(108, 86), (32, 86)], fill=cor, width=12)
    draw.polygon([(46, 66), (16, 86), (46, 106)], fill=cor)
    return img


def _desenhar_compactacao(cor: str) -> Image.Image:
    img, draw = _criar_tela(cor)
    # Caixa externa
    draw.rounded_rectangle([(18, 22), (110, 108)], radius=14, outline=cor, width=10)
    # Divisória da tampa
    draw.line([(18, 50), (110, 50)], fill=cor, width=10)
    # Fecho central (zíper/fita)
    draw.rectangle([(54, 22), (74, 76)], fill=cor)
    return img


def _desenhar_historico(cor: str) -> Image.Image:
    img, draw = _criar_tela(cor)
    # Círculo do relógio
    draw.ellipse([(16, 16), (112, 112)], outline=cor, width=10)
    # Ponteiros (vertical e horizontal)
    draw.line([(64, 36), (64, 66)], fill=cor, width=10)
    draw.line([(64, 66), (88, 80)], fill=cor, width=10)
    return img


def _desenhar_recuperar(cor: str) -> Image.Image:
    img, draw = _criar_tela(cor)
    # Seta apontando para baixo
    draw.line([(64, 18), (64, 78)], fill=cor, width=12)
    draw.polygon([(38, 64), (90, 64), (64, 94)], fill=cor)
    # Bandeja inferior de download
    draw.line([(24, 108), (104, 108)], fill=cor, width=12)
    return img