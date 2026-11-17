from pathlib import Path

from PIL import Image, ImageOps

from operacoes.cancelamento import CancelamentoOperacao
from operacoes.operacao_arquivo import OperacaoArquivo


class CompressaoImagem(OperacaoArquivo):
    def __init__(self, qualidade_jpeg: int = 70, cores_png: int = 256):
        self.qualidade_jpeg = max(10, min(95, qualidade_jpeg))
        self.cores_png = max(16, min(256, cores_png))

    def executar(
        self,
        origens: tuple[Path, ...],
        destino: Path,
        *,
        cancelamento: CancelamentoOperacao | None = None,
    ) -> None:
        cancelamento = cancelamento or CancelamentoOperacao()
        cancelamento.verificar()

        if len(origens) != 1:
            raise ValueError("Selecione uma única imagem JPG ou PNG para comprimir.")

        origem = origens[0]
        if not origem.exists() or not origem.is_file():
            raise ValueError(
                "Não foi possível ler a imagem. Escolha um arquivo JPG ou PNG válido."
            )

        try:
            with Image.open(origem, formats=("JPEG", "PNG")) as original:
                formato_detectado = original.format
                imagem = ImageOps.exif_transpose(original)
                imagem.load()
        except (OSError, Image.DecompressionBombError) as erro:
            raise ValueError(
                "Não foi possível ler a imagem. Escolha um arquivo JPG ou PNG válido."
            ) from erro

        cancelamento.verificar()

        try:
            if formato_detectado == "JPEG":
                self._comprimir_jpeg(imagem, destino, cancelamento)
            elif formato_detectado == "PNG":
                self._comprimir_png(imagem, destino, cancelamento)
            else:
                raise ValueError("Formato não suportado. Escolha uma imagem JPG ou PNG.")
        finally:
            imagem.close()

    def _comprimir_jpeg(
        self,
        imagem: Image.Image,
        destino: Path,
        cancelamento: CancelamentoOperacao,
    ) -> None:
        if imagem.mode not in ("L", "RGB"):
            imagem = imagem.convert("RGB")

        cancelamento.verificar()
        imagem.save(
            destino,
            format="JPEG",
            quality=self.qualidade_jpeg,
            optimize=True,
            progressive=True,
        )

    def _comprimir_png(
        self,
        imagem: Image.Image,
        destino: Path,
        cancelamento: CancelamentoOperacao,
    ) -> None:
        # Quantiza para paleta de até 256 cores preservando transparência (alfa)
        if imagem.mode not in ("P", "1", "L"):
            metodo = (
                Image.Quantize.FASTOCTREE
                if imagem.has_transparency_data
                else Image.Quantize.MEDIANCUT
            )
            imagem = imagem.quantize(colors=self.cores_png, method=metodo)

        cancelamento.verificar()
        imagem.save(
            destino,
            format="PNG",
            optimize=True,
            compress_level=9,
        )