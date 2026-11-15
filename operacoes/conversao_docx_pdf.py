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

from operacoes.cancelamento import CancelamentoOperacao, OperacaoCancelada
from operacoes.operacao_arquivo import OperacaoArquivo


LIBREOFFICE_INDISPONIVEL = (
    "O LibreOffice está indisponível. Instale-o ou verifique a instalação "
    "para converter DOCX em PDF."
)


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
            Document(str(origem))
        except (PackageNotFoundError, BadZipFile, KeyError, ValueError, OSError) as erro:
            raise ValueError(
                "Não foi possível ler o documento. Escolha um DOCX válido."
            ) from erro

        cancelamento.verificar()
        executavel = self._localizar_libreoffice()
        if executavel is None:
            raise ValueError(LIBREOFFICE_INDISPONIVEL)

        with TemporaryDirectory(dir=destino.parent) as temporario:
            pasta_saida = Path(temporario).resolve()
            # O perfil próprio mantém a execução separada de janelas abertas do LibreOffice.
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
            except OSError as erro:
                raise ValueError(LIBREOFFICE_INDISPONIVEL) from erro
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
