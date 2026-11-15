from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from operacoes.cancelamento import CancelamentoOperacao
from operacoes.operacao_arquivo import OperacaoArquivo


class CompactacaoZip(OperacaoArquivo):
    def executar(
        self,
        origens: tuple[Path, ...],
        destino: Path,
        *,
        cancelamento: CancelamentoOperacao | None = None,
    ) -> None:
        cancelamento = cancelamento or CancelamentoOperacao()
        if not origens:
            raise ValueError("Selecione pelo menos um arquivo ou pasta para compactar.")

        nomes_raiz: set[str] = set()
        for origem in origens:
            cancelamento.verificar()
            if not origem.exists():
                raise ValueError(f"O caminho selecionado não existe: {origem.name}")
            if origem.name in nomes_raiz:
                raise ValueError(
                    f"Não é possível compactar itens com o mesmo nome ({origem.name})."
                )
            nomes_raiz.add(origem.name)

        try:
            with ZipFile(destino, mode="w", compression=ZIP_DEFLATED) as arquivo_zip:
                for origem in origens:
                    cancelamento.verificar()
                    if origem.is_file():
                        self._adicionar_arquivo(arquivo_zip, origem, origem.name, cancelamento)
                    elif origem.is_dir():
                        self._adicionar_pasta(arquivo_zip, origem, cancelamento)
        except OSError as erro:
            raise ValueError(
                "Não foi possível ler os arquivos ou pastas selecionados."
            ) from erro

    def _adicionar_arquivo(
        self,
        arquivo_zip: ZipFile,
        caminho: Path,
        nome_no_zip: str,
        cancelamento: CancelamentoOperacao,
    ) -> None:
        info = ZipInfo.from_file(caminho, arcname=nome_no_zip)
        info.compress_type = arquivo_zip.compression
        with caminho.open("rb") as origem, arquivo_zip.open(info, "w") as entrada_zip:
            while bloco := origem.read(1024 * 1024):
                cancelamento.verificar()
                entrada_zip.write(bloco)

    def _adicionar_pasta(
        self, arquivo_zip: ZipFile, pasta_raiz: Path, cancelamento: CancelamentoOperacao
    ) -> None:
        base = pasta_raiz.parent
        if not any(pasta_raiz.iterdir()):
            # Preserva a pasta mesmo se estiver vazia
            arquivo_zip.writestr(f"{pasta_raiz.name}/", "")
            return

        for item in pasta_raiz.rglob("*"):
            cancelamento.verificar()
            caminho_relativo = item.relative_to(base).as_posix()
            if item.is_dir():
                if not any(item.iterdir()):
                    arquivo_zip.writestr(f"{caminho_relativo}/", "")
            elif item.is_file():
                self._adicionar_arquivo(arquivo_zip, item, caminho_relativo, cancelamento)
