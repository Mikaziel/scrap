from pathlib import Path
from tempfile import TemporaryDirectory

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
    ) -> Path:
        if any(origem.resolve() == destino.resolve() for origem in origens):
            raise ValueError("Selecione um destino diferente do arquivo de origem.")

        if destino.is_dir():
            raise ValueError("Escolha um nome de arquivo para salvar o resultado.")

        if not sobrescrever and (destino.exists() or destino.is_symlink()):
            raise DestinoExistenteError(destino)

        with TemporaryDirectory(dir=destino.parent) as pasta_temporaria:
            arquivo_temporario = Path(pasta_temporaria) / destino.name
            operacao.executar(origens, arquivo_temporario)

            if not sobrescrever:
                try:
                    with destino.open("xb"):
                        pass
                except FileExistsError as erro:
                    raise DestinoExistenteError(destino) from erro

            try:
                arquivo_temporario.replace(destino)
            except OSError:
                if not sobrescrever:
                    destino.unlink(missing_ok=True)
                raise

        return destino
