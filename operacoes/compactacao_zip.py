from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from operacoes.operacao_arquivo import OperacaoArquivo


class CompactacaoZip(OperacaoArquivo):
    def executar(self, origens: tuple[Path, ...], destino: Path) -> None:
        if not origens:
            raise ValueError("Selecione pelo menos um arquivo ou pasta para compactar.")

        nomes_raiz: set[str] = set()
        for origem in origens:
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
                    if origem.is_file():
                        arquivo_zip.write(origem, arcname=origem.name)
                    elif origem.is_dir():
                        self._adicionar_pasta(arquivo_zip, origem)
        except OSError as erro:
            raise ValueError(
                "Não foi possível ler os arquivos ou pastas selecionados."
            ) from erro

    def _adicionar_pasta(self, arquivo_zip: ZipFile, pasta_raiz: Path) -> None:
        base = pasta_raiz.parent
        itens = list(pasta_raiz.rglob("*"))

        if not itens:
            # Preserva a pasta mesmo se estiver vazia
            arquivo_zip.writestr(f"{pasta_raiz.name}/", "")
            return

        for item in itens:
            caminho_relativo = item.relative_to(base).as_posix()
            if item.is_dir():
                if not any(item.iterdir()):
                    arquivo_zip.writestr(f"{caminho_relativo}/", "")
            elif item.is_file():
                arquivo_zip.write(item, arcname=caminho_relativo)