import shutil
from pathlib import Path
from zipfile import BadZipFile, ZipFile, ZipInfo

from operacoes.cancelamento import CancelamentoOperacao
from operacoes.operacao_arquivo import OperacaoArquivo


class DescompactacaoZip(OperacaoArquivo):
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
            raise ValueError("Selecione um único arquivo ZIP para extrair.")

        origem = origens[0]
        if not origem.exists() or not origem.is_file():
            raise ValueError("Não foi possível ler o arquivo. Escolha um ZIP válido.")

        try:
            with ZipFile(origem, mode="r") as arquivo_zip:
                informacoes = arquivo_zip.infolist()
                if not informacoes:
                    raise ValueError("O arquivo ZIP selecionado está vazio.")

                destino.mkdir(parents=True, exist_ok=True)
                destino_resolvido = destino.resolve()

                for info in informacoes:
                    cancelamento.verificar()
                    caminho_alvo = self._resolver_caminho_seguro(
                        destino_resolvido, info
                    )
                    if info.is_dir():
                        caminho_alvo.mkdir(parents=True, exist_ok=True)
                    else:
                        caminho_alvo.parent.mkdir(parents=True, exist_ok=True)
                        self._extrair_membro(
                            arquivo_zip, info, caminho_alvo, cancelamento
                        )
        except BadZipFile as erro:
            raise ValueError(
                "O arquivo selecionado não é um ZIP válido ou está corrompido."
            ) from erro
        except ValueError:
            raise
        except (OSError, RuntimeError) as erro:
            if "password" in str(erro).lower() or "encrypted" in str(erro).lower():
                raise ValueError(
                    "O arquivo ZIP está protegido por senha e não pode ser extraído."
                ) from erro
            raise ValueError(
                "Não foi possível extrair os arquivos do pacote ZIP."
            ) from erro

    @staticmethod
    def _resolver_caminho_seguro(destino_base: Path, info: ZipInfo) -> Path:
        nome_normalizado = info.filename.replace("\\", "/")
        partes = [
            parte
            for parte in Path(nome_normalizado).parts
            if parte not in ("", ".", "/")
        ]
        if not partes or ".." in partes:
            raise ValueError(
                "O arquivo ZIP contém caminhos inseguros e foi bloqueado."
            )

        caminho_final = (destino_base / Path(*partes)).resolve()
        if (
            caminho_final != destino_base
            and destino_base not in caminho_final.parents
        ):
            raise ValueError(
                "O arquivo ZIP contém caminhos fora da pasta de destino."
            )
        return caminho_final

    @staticmethod
    def _extrair_membro(
        arquivo_zip: ZipFile,
        info: ZipInfo,
        caminho_alvo: Path,
        cancelamento: CancelamentoOperacao,
    ) -> None:
        with arquivo_zip.open(info, "r") as origem, caminho_alvo.open("wb") as saida:
            while bloco := origem.read(1024 * 1024):
                cancelamento.verificar()
                saida.write(bloco)