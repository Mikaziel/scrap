from pathlib import Path
from typing import Literal

from PIL import Image, ImageOps

from operacoes.operacao_arquivo import OperacaoArquivo


class ConversaoImagem(OperacaoArquivo):
    def __init__(self, formato_destino: Literal["PNG", "JPEG"] = "PNG"):
        self.formato_destino = formato_destino

    def executar(self, origens: tuple[Path, ...], destino: Path) -> None:
        formato_origem = "PNG" if self.formato_destino == "JPEG" else "JPEG"
        nome_origem = "PNG" if formato_origem == "PNG" else "JPG"
        if len(origens) != 1:
            raise ValueError(f"Selecione um único arquivo {nome_origem}.")

        try:
            with Image.open(origens[0], formats=(formato_origem,)) as original:
                imagem = ImageOps.exif_transpose(original)
        except (OSError, Image.DecompressionBombError) as erro:
            raise ValueError(
                f"Não foi possível ler a imagem. Escolha um {nome_origem} válido."
            ) from erro

        if self.formato_destino == "JPEG" and imagem.has_transparency_data:
            imagem_rgba = imagem.convert("RGBA")
            fundo_branco = Image.new("RGB", imagem_rgba.size, "white")
            fundo_branco.paste(imagem_rgba, mask=imagem_rgba.getchannel("A"))
            imagem = fundo_branco
        elif imagem.mode not in ("L", "RGB"):
            imagem = imagem.convert("RGB")

        imagem.save(destino, format=self.formato_destino)
