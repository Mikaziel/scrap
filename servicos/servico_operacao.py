import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

from operacoes.cancelamento import CancelamentoOperacao
from operacoes.operacao_arquivo import OperacaoArquivo


class DestinoExistenteError(FileExistsError):
    pass


class ServicoOperacao:
    def executar(
        self,
        operacao: OperacaoArquivo,
        origens: tuple[Path, ...],
        destino: Path,
        *,
        sobrescrever: bool = False,
        cancelamento: CancelamentoOperacao | None = None,
    ) -> Path:
        if cancelamento is not None:
            cancelamento.verificar()

        destino_resolvido = destino.resolve()
        for origem in origens:
            origem_resolvida = origem.resolve()
            if origem_resolvida == destino_resolvido:
                raise ValueError("Selecione um destino diferente do arquivo de origem.")
            if origem_resolvida in destino_resolvido.parents:
                raise ValueError(
                    "Selecione um destino fora da pasta que está sendo compactada."
                )

        if destino.is_dir() and not sobrescrever:
            raise DestinoExistenteError(destino)

        if not sobrescrever and (destino.exists() or destino.is_symlink()):
            raise DestinoExistenteError(destino)

        with TemporaryDirectory(dir=destino.parent) as pasta_temporaria:
            arquivo_temporario = Path(pasta_temporaria) / destino.name
            if cancelamento is None:
                operacao.executar(origens, arquivo_temporario)
            else:
                try:
                    operacao.executar(
                        origens, arquivo_temporario, cancelamento=cancelamento
                    )
                except (ValueError, OSError):
                    cancelamento.verificar()
                    raise
                cancelamento.iniciar_publicacao()

            if not sobrescrever:
                if arquivo_temporario.is_dir():
                    if destino.exists() or destino.is_symlink():
                        raise DestinoExistenteError(destino)
                else:
                    try:
                        with destino.open("xb"):
                            pass
                    except FileExistsError as erro:
                        raise DestinoExistenteError(destino) from erro
            elif destino.exists() or destino.is_symlink():
                if destino.is_dir() and not destino.is_symlink():
                    shutil.rmtree(destino)
                else:
                    destino.unlink(missing_ok=True)

            try:
                arquivo_temporario.replace(destino)
            except OSError:
                if not sobrescrever and not destino.is_dir():
                    destino.unlink(missing_ok=True)
                raise

        return destino