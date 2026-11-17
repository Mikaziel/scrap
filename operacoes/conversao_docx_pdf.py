import os
import shutil
import signal
import subprocess
from pathlib import Path
from sys import platform
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

        try:
            documento = Document(str(origem))
        except (PackageNotFoundError, BadZipFile, KeyError, ValueError, OSError) as erro:
            raise ValueError(
                "Não foi possível ler o documento. Escolha um DOCX válido."
            ) from erro

        cancelamento.verificar()
        executavel = self._localizar_libreoffice()

        # Se o LibreOffice estiver instalado, usa ele para fidelidade máxima de layout
        if executavel is not None:
            self._converter_com_libreoffice(executavel, origem, destino, cancelamento)
            return

        # Caso contrário, faz a conversão nativa em Python sem depender do LibreOffice
        self._converter_nativo_python(documento, destino, cancelamento)

    def _converter_com_libreoffice(
        self,
        executavel: str,
        origem: Path,
        destino: Path,
        cancelamento: CancelamentoOperacao,
    ) -> None:
        with TemporaryDirectory(dir=destino.parent) as temporario:
            pasta_saida = Path(temporario).resolve()
            perfil = (pasta_saida / "perfil").as_uri()
            comando = [
                executavel,
                f"-env:UserInstallation={perfil}",
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(pasta_saida),
                str(origem.resolve()),
            ]
            try:
                codigo = self._executar_libreoffice(comando, cancelamento)
            except subprocess.TimeoutExpired as erro:
                raise ValueError(
                    "O LibreOffice demorou mais de 60 segundos para converter o DOCX."
                ) from erro

            cancelamento.verificar()
            pdf_gerado = pasta_saida / f"{origem.stem}.pdf"
            if codigo != 0 or not pdf_gerado.is_file() or pdf_gerado.stat().st_size == 0:
                raise ValueError(
                    "O LibreOffice não conseguiu gerar o PDF. Confira se o DOCX abre "
                    "no LibreOffice e tente novamente."
                )
            pdf_gerado.replace(destino)

    def _converter_nativo_python(
        self,
        documento: Document,
        destino: Path,
        cancelamento: CancelamentoOperacao,
    ) -> None:
        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_margins(left=15, top=15, right=15)
        pdf.add_page()
        largura_util = pdf.epw

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

        for tabela in documento.tables:
            cancelamento.verificar()
            pdf.ln(3)
            pdf.set_font("Helvetica", size=10)
            with pdf.table(width=largura_util) as tabela_pdf:
                for linha in tabela.rows:
                    linha_pdf = tabela_pdf.row()
                    for celula in linha.cells:
                        linha_pdf.cell(self._sanitizar_texto(celula.text.strip()))
            pdf.ln(3)

        pdf.output(str(destino))

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

    @staticmethod
    def _localizar_libreoffice() -> str | None:
        executavel = shutil.which("libreoffice") or shutil.which("soffice")
        if executavel or platform != "darwin":
            return executavel

        for pasta in (Path("/Applications"), Path.home() / "Applications"):
            caminho = pasta / "LibreOffice.app/Contents/MacOS/soffice"
            if caminho.is_file() and os.access(caminho, os.X_OK):
                return str(caminho)
        return None

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