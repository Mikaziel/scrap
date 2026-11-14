import shutil
import subprocess
from pathlib import Path
from zipfile import BadZipFile

from docx import Document
from docx.opc.exceptions import PackageNotFoundError
from fpdf import FPDF

from operacoes.operacao_arquivo import OperacaoArquivo


class ConversaoDocxParaPdf(OperacaoArquivo):
    def executar(self, origens: tuple[Path, ...], destino: Path) -> None:
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
        if self._converter_com_libreoffice(origem, destino):
            return

        # 3. Fallback 100% Python (python-docx + fpdf2) — funciona em qualquer SO
        self._converter_nativo_python(documento, destino)

    def _converter_com_libreoffice(self, origem: Path, destino: Path) -> bool:
        executavel = shutil.which("libreoffice") or shutil.which("soffice")
        if not executavel:
            return False

        pasta_saida = destino.parent
        try:
            resultado = subprocess.run(
                [
                    executavel,
                    "--headless",
                    "--convert-to",
                    "pdf",
                    "--outdir",
                    str(pasta_saida),
                    str(origem),
                ],
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
            pdf_gerado = pasta_saida / f"{origem.stem}.pdf"
            if resultado.returncode == 0 and pdf_gerado.exists():
                if pdf_gerado != destino:
                    pdf_gerado.replace(destino)
                return True
        except (OSError, subprocess.SubprocessError):
            return False

        return False

    def _converter_nativo_python(self, documento: Document, destino: Path) -> None:
        try:
            pdf = FPDF(orientation="P", unit="mm", format="A4")
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.set_margins(left=15, top=15, right=15)
            pdf.add_page()

            largura_util = pdf.epw

            # Renderiza parágrafos e títulos
            for paragrafo in documento.paragraphs:
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
                pdf.ln(3)
                pdf.set_font("Helvetica", size=10)
                with pdf.table(width=largura_util) as tabela_pdf:
                    for linha in tabela.rows:
                        linha_pdf = tabela_pdf.row()
                        for celula in linha.cells:
                            linha_pdf.cell(self._sanitizar_texto(celula.text.strip()))
                pdf.ln(3)

            pdf.output(str(destino))
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