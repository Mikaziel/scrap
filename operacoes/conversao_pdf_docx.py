from pathlib import Path

from docx import Document
from pypdf import PdfReader
from pypdf.errors import PdfReadError, PdfStreamError

from operacoes.cancelamento import CancelamentoOperacao
from operacoes.operacao_arquivo import OperacaoArquivo


class ConversaoPdfParaDocx(OperacaoArquivo):
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
            raise ValueError("Selecione um único arquivo PDF.")

        origem = origens[0]
        if not origem.exists() or not origem.is_file():
            raise ValueError("Não foi possível ler o documento. Escolha um PDF válido.")

        leitor = self._validar_e_abrir_pdf(origem)
        cancelamento.verificar()

        # 1. Tenta conversão mantendo layout, tabelas e imagens via pdf2docx
        if self._converter_com_pdf2docx(origem, destino, len(leitor.pages), cancelamento):
            return

        # 2. Fallback nativo extraindo texto página a página com pypdf + python-docx
        self._converter_com_pypdf(leitor, destino, cancelamento)

    @staticmethod
    def _validar_e_abrir_pdf(origem: Path) -> PdfReader:
        try:
            with origem.open("rb") as arquivo:
                assinatura = arquivo.read(5)
            if assinatura != b"%PDF-":
                raise ValueError("Assinatura PDF inválida.")

            leitor = PdfReader(str(origem))
            if leitor.is_encrypted:
                raise ValueError(
                    "O arquivo PDF está protegido por senha e não pode ser convertido."
                )
            if len(leitor.pages) == 0:
                raise ValueError("O arquivo PDF não possui páginas.")
            return leitor
        except ValueError as erro:
            if "protegido por senha" in str(erro):
                raise
            raise ValueError(
                "Não foi possível ler o documento. Escolha um PDF válido."
            ) from erro
        except (PdfReadError, PdfStreamError, OSError, Exception) as erro:
            raise ValueError(
                "Não foi possível ler o documento. Escolha um PDF válido."
            ) from erro

    @staticmethod
    def _converter_com_pdf2docx(
        origem: Path,
        destino: Path,
        total_paginas: int,
        cancelamento: CancelamentoOperacao,
    ) -> bool:
        try:
            from pdf2docx import Converter
        except ImportError:
            return False

        conversor = None
        try:
            cancelamento.verificar()
            conversor = Converter(str(origem))
            for indice_pagina in range(total_paginas):
                cancelamento.verificar()
                conversor.convert(
                    str(destino),
                    start=indice_pagina,
                    end=indice_pagina + 1,
                )
            cancelamento.verificar()
            return destino.is_file() and destino.stat().st_size > 0
        except Exception:
            if cancelamento.solicitado:
                cancelamento.verificar()
            return False
        finally:
            if conversor is not None:
                try:
                    conversor.close()
                except Exception:
                    pass

    @staticmethod
    def _converter_com_pypdf(
        leitor: PdfReader,
        destino: Path,
        cancelamento: CancelamentoOperacao,
    ) -> None:
        try:
            documento = Document()
            total_paginas = len(leitor.pages)

            for indice, pagina in enumerate(leitor.pages):
                cancelamento.verificar()
                texto = (pagina.extract_text() or "").strip()

                if texto:
                    for linha in texto.splitlines():
                        cancelamento.verificar()
                        linha_limpa = "".join(
                            ch for ch in linha if ch.isprintable() or ch in "\t"
                        )
                        documento.add_paragraph(linha_limpa)
                else:
                    documento.add_paragraph("")

                if indice < total_paginas - 1:
                    documento.add_page_break()

            cancelamento.verificar()
            documento.save(str(destino))
        except Exception as erro:
            if cancelamento.solicitado:
                cancelamento.verificar()
            raise ValueError(
                "Não foi possível converter o arquivo PDF para DOCX."
            ) from erro