from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from operacoes.cancelamento import CancelamentoOperacao, OperacaoCancelada
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
        self._validar_pdf(origem, cancelamento)
        self._converter_com_pdf2docx(origem, destino, cancelamento)

    @staticmethod
    def _validar_pdf(origem: Path, cancelamento: CancelamentoOperacao) -> None:
        mensagem_invalido = "Não foi possível ler o documento. Escolha um PDF válido."
        try:
            with origem.open("rb") as arquivo:
                if arquivo.read(5) != b"%PDF-":
                    raise ValueError(mensagem_invalido)
                arquivo.seek(0)
                leitor = PdfReader(arquivo)

                if leitor.is_encrypted:
                    raise ValueError(
                        "O arquivo PDF está protegido por senha e não pode ser convertido."
                    )
                if len(leitor.pages) == 0:
                    raise ValueError("O arquivo PDF não possui páginas.")

                for pagina in leitor.pages:
                    cancelamento.verificar()
                    if (pagina.extract_text() or "").strip():
                        return
        except (PdfReadError, OSError) as erro:
            raise ValueError(mensagem_invalido) from erro

        raise ValueError(
            "O PDF não contém texto selecionável. Use um PDF com texto ou "
            "aplique OCR ao documento digitalizado antes de converter."
        )

    @staticmethod
    def _converter_com_pdf2docx(
        origem: Path, destino: Path, cancelamento: CancelamentoOperacao
    ) -> None:
        cancelamento.verificar()
        try:
            from pdf2docx import Converter
        except (ImportError, OSError) as erro:
            raise ValueError(
                "O conversor PDF para DOCX está indisponível. "
                "Instale as dependências do SCRAP e tente novamente."
            ) from erro

        try:
            conversor = Converter(str(origem))
            try:
                ajustes = conversor.default_settings
                ajustes["ignore_page_error"] = False
                conversor.load_pages()
                cancelamento.verificar()
                conversor.parse_document(**ajustes)
                for pagina in conversor.pages:
                    cancelamento.verificar()
                    pagina.parse(**ajustes)

                # Grava todas as páginas em um único documento.
                cancelamento.verificar()
                conversor.make_docx(str(destino), **ajustes)
            finally:
                conversor.close()
        except (OperacaoCancelada, OSError):
            raise
        except Exception as erro:
            raise ValueError(
                "Não foi possível converter todas as páginas para DOCX. "
                "Tente um PDF com texto selecionável e layout mais simples."
            ) from erro

        cancelamento.verificar()
        if not destino.is_file() or destino.stat().st_size == 0:
            raise ValueError("A conversão não gerou um arquivo DOCX.")
