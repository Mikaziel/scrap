from abc import ABC, abstractmethod
from pathlib import Path


class OperacaoArquivo(ABC):
    @abstractmethod
    def executar(self, origens: tuple[Path, ...], destino: Path) -> None:
        """Grava o resultado da operação no caminho fornecido."""
