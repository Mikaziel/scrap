import os
import shutil
import signal
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic
from zipfile import BadZipFile

from docx import Document
from docx.opc.exceptions import PackageNotFoundError
from fpdf import FPDF

from operacoes.cancelamento import CancelamentoOperacao, OperacaoCancelada
from operacoes.operacao_arquivo import OperacaoArquivo


class ConversaoDocxParaPdf(OperacaoArquivo):
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
            raise ValueError("Selecione um único arquivo DOCX.")

        origem = origens[0]
        if not origem.exists() or not origem.is_file():
            raise ValueError("Não foi possível ler o documento. Escolha um DOCX válido.")

        # 1. Valida se o arquivo é realmente um DOCX íntegro antes de processar
        try:
            documento = Document(str(origem))
        except (PackageNotFoundError, BadZipFile, KeyError, ValueError, OSError) as erro:
            raise ValueError(
                "Não foi possível ler o documento. Escolha um DOCX válido."
            ) from erro

        # 2. Tenta conversão via LibreOffice (se disponível no Linux/Container/Sistema)
        cancelamento.verificar()
        if self._converter_com_libreoffice(origem, destino, cancelamento):
            return

        # 3. Fallback 100% Python (python-docx + fpdf2) — funciona em qualquer SO
        cancelamento.verificar()
        self._converter_nativo_python(documento, destino, cancelamento)

    def _converter_com_libreoffice(
        self, origem: Path, destino: Path, cancelamento: CancelamentoOperacao
    ) -> bool:
        executavel = shutil.which("libreoffice") or shutil.which("soffice")
        if not executavel:
            return False

        pasta_saida = destino.parent
        try:
            # Um perfil próprio impede que a conversão seja encaminhada a outra sessão aberta.
            with TemporaryDirectory(dir=pasta_saida) as perfil:
                comando = [
                    executavel,
                    f"-env:UserInstallation={Path(perfil).resolve().as_uri()}",
                    "--headless",
                    "--convert-to",
                    "pdf",
                    "--outdir",
                    str(pasta_saida),
                    str(origem),
                ]
                codigo = self._executar_libreoffice(comando, cancelamento)
            cancelamento.verificar()
            pdf_gerado = pasta_saida / f"{origem.stem}.pdf"
            if codigo == 0 and pdf_gerado.exists():
                if pdf_gerado != destino:
                    pdf_gerado.replace(destino)
                return True
        except (OSError, subprocess.SubprocessError):
            return False

        return False

    @staticmethod
    def _executar_libreoffice(comando: list[str], cancelamento: CancelamentoOperacao) -> int:
        cancelamento.verificar()
        with subprocess.Popen(
            comando,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=os.name == "posix",
        ) as processo:
            limite = monotonic() + 60
            try:
                while True:
                    cancelamento.verificar()
                    restante = limite - monotonic()
                    if restante <= 0:
                        raise subprocess.TimeoutExpired(comando, 60)
                    try:
                        return processo.wait(timeout=min(0.1, restante))
                    except subprocess.TimeoutExpired:
                        continue
            except (OperacaoCancelada, subprocess.TimeoutExpired):
                try:
                    if os.name == "posix":
                        os.killpg(processo.pid, signal.SIGKILL)
                    else:
                        processo.kill()
                except ProcessLookupError:
                    pass
                raise

    def _converter_nativo_python(
        self, documento: Document, destino: Path, cancelamento: CancelamentoOperacao
    ) -> None:
        try:
            pdf = FPDF(orientation="P", unit="mm", format="A4")
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.set_margins(left=15, top=15, right=15)
            pdf.add_page()

            largura_util = pdf.epw

            # Renderiza parágrafos e títulos
            for paragrafo in documento.paragraphs:
                cancelamento.verificar()
                texto = self._sanitizar_texto(paragrafo.text)
                estilo = (paragrafo.style.name or "").lower() if paragrafo.style else ""

                if not texto.strip():
                    pdf.ln(4)
                    continue

                if "heading 1" in estilo or "título 1" in estilo:
                    pdf.set_font("Helvetica", style="B", size=18)
                    pdf.multi_cell(largura_util, 9, texto)
                    pdf.ln(2)
                elif "heading 2" in estilo or "título 2" in estilo:
                    pdf.set_font("Helvetica", style="B", size=15)
                    pdf.multi_cell(largura_util, 8, texto)
                    pdf.ln(2)
                elif "heading" in estilo or "título" in estilo:
                    pdf.set_font("Helvetica", style="B", size=13)
                    pdf.multi_cell(largura_util, 7, texto)
                    pdf.ln(1)
                else:
                    pdf.set_font("Helvetica", size=11)
                    pdf.multi_cell(largura_util, 6, texto)
                    pdf.ln(1)

            # Renderiza tabelas do documento, se existirem
            for tabela in documento.tables:
                cancelamento.verificar()
                pdf.ln(3)
                pdf.set_font("Helvetica", size=10)
                with pdf.table(width=largura_util) as tabela_pdf:
                    for linha in tabela.rows:
                        cancelamento.verificar()
                        linha_pdf = tabela_pdf.row()
                        for celula in linha.cells:
                            linha_pdf.cell(self._sanitizar_texto(celula.text.strip()))
                pdf.ln(3)

            cancelamento.verificar()
            pdf.output(str(destino))
        except OperacaoCancelada:
            raise
        except Exception as erro:
            raise ValueError(
                "Não foi possível converter o documento DOCX para PDF."
            ) from erro

    @staticmethod
    def _sanitizar_texto(texto: str) -> str:
        substituicoes = {
            "\u2013": "-",
            "\u2014": "-",
            "\u2018": "'",
            "\u2019": "'",
            "\u201c": '"',
            "\u201d": '"',
            "\u2022": "*",
            "\u2026": "...",
            "\u00a0": " ",
        }
        for original, substituto in substituicoes.items():
            texto = texto.replace(original, substituto)
        return texto.encode("latin-1", errors="replace").decode("latin-1")
