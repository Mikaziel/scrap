from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.errors import PdfReadError, PdfStreamError

from operacoes.cancelamento import CancelamentoOperacao
from operacoes.operacao_arquivo import OperacaoArquivo


def _abrir_pdf_valido(caminho: Path) -> PdfReader:
    if not caminho.exists() or not caminho.is_file():
        raise ValueError(f"Não foi possível ler o arquivo: {caminho.name}")

    try:
        with caminho.open("rb") as arquivo:
            if arquivo.read(5) != b"%PDF-":
                raise ValueError(f"O arquivo '{caminho.name}' não é um PDF válido.")

        leitor = PdfReader(str(caminho))
        if leitor.is_encrypted:
            raise ValueError(
                f"O arquivo '{caminho.name}' está protegido por senha."
            )
        if len(leitor.pages) == 0:
            raise ValueError(f"O arquivo '{caminho.name}' não possui páginas.")
        return leitor
    except ValueError:
        raise
    except (PdfReadError, PdfStreamError, OSError, Exception) as erro:
        raise ValueError(
            f"Não foi possível ler '{caminho.name}'. Escolha um PDF válido."
        ) from erro


class MesclarPdf(OperacaoArquivo):
    def executar(
        self,
        origens: tuple[Path, ...],
        destino: Path,
        *,
        cancelamento: CancelamentoOperacao | None = None,
    ) -> None:
        cancelamento = cancelamento or CancelamentoOperacao()
        cancelamento.verificar()

        if len(origens) < 2:
            raise ValueError("Selecione pelo menos 2 arquivos PDF para mesclar.")

        escritor = PdfWriter()
        try:
            for origem in origens:
                cancelamento.verificar()
                leitor = _abrir_pdf_valido(origem)
                for pagina in leitor.pages:
                    cancelamento.verificar()
                    escritor.add_page(pagina)

            cancelamento.verificar()
            with destino.open("wb") as saida:
                escritor.write(saida)
        except ValueError:
            raise
        except OSError as erro:
            raise ValueError(
                "Não foi possível salvar o arquivo PDF mesclado."
            ) from erro
        finally:
            escritor.close()


class DividirPdf(OperacaoArquivo):
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
            raise ValueError("Selecione um único arquivo PDF para dividir.")

        origem = origens[0]
        leitor = _abrir_pdf_valido(origem)

        try:
            destino.mkdir(parents=True, exist_ok=True)
            largura_digitos = max(3, len(str(len(leitor.pages))))

            for indice, pagina in enumerate(leitor.pages, start=1):
                cancelamento.verificar()
                escritor = PdfWriter()
                try:
                    escritor.add_page(pagina)
                    nome_pagina = f"{origem.stem}-pagina-{indice:0{largura_digitos}d}.pdf"
                    caminho_pagina = destino / nome_pagina
                    with caminho_pagina.open("wb") as saida:
                        escritor.write(saida)
                finally:
                    escritor.close()
        except OSError as erro:
            raise ValueError(
                "Não foi possível extrair as páginas do PDF."
            ) from erro