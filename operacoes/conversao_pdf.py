from pathlib import Path

from PIL import Image, ImageOps

from operacoes.operacao_arquivo import OperacaoArquivo


class ConversaoImagemParaPdf(OperacaoArquivo):
    def executar(self, origens: tuple[Path, ...], destino: Path) -> None:
        if not origens:
            raise ValueError("Selecione pelo menos uma imagem para converter em PDF.")

        imagens_processadas: list[Image.Image] = []

        try:
            for origem in origens:
                try:
                    with Image.open(origem, formats=("JPEG", "PNG")) as original:
                        imagem = ImageOps.exif_transpose(original)
                        if imagem.has_transparency_data:
                            imagem_rgba = imagem.convert("RGBA")
                            fundo_branco = Image.new("RGB", imagem_rgba.size, "white")
                            fundo_branco.paste(
                                imagem_rgba, mask=imagem_rgba.getchannel("A")
                            )
                            imagem = fundo_branco
                        elif imagem.mode not in ("L", "RGB"):
                            imagem = imagem.convert("RGB")
                        else:
                            imagem = imagem.copy()

                        imagens_processadas.append(imagem)
                except (OSError, Image.DecompressionBombError) as erro:
                    raise ValueError(
                        f"Não foi possível ler a imagem '{origem.name}'. Escolha arquivos JPG ou PNG válidos."
                    ) from erro

            primeira_pagina, *paginas_extras = imagens_processadas
            primeira_pagina.save(
                destino,
                format="PDF",
                save_all=True,
                append_images=paginas_extras,
            )
        finally:
            for img in imagens_processadas:
                img.close()