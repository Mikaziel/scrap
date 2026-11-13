from pathlib import Path

from PIL import Image, ImageOps

from operacoes.operacao_arquivo import OperacaoArquivo


class ConversaoImagem(OperacaoArquivo):
    def executar(self, origens: tuple[Path, ...], destino: Path) -> None:
        if len(origens) != 1:
            raise ValueError("Selecione um único arquivo JPG.")

        try:
            with Image.open(origens[0], formats=("JPEG",)) as jpeg:
                imagem = ImageOps.exif_transpose(jpeg)
        except (OSError, Image.DecompressionBombError) as erro:
            raise ValueError("Não foi possível ler a imagem. Escolha um JPG válido.") from erro

        if imagem.mode not in ("L", "RGB"):
            imagem = imagem.convert("RGB")
        imagem.save(destino, format="PNG")
