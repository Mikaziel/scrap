from abc import ABC, abstractmethod
from pathlib import Path

from operacoes.cancelamento import CancelamentoOperacao


class OperacaoArquivo(ABC):
    @abstractmethod
    def executar(
        self,
        origens: tuple[Path, ...],
        destino: Path,
        *,
        cancelamento: CancelamentoOperacao | None = None,
    ) -> None:
        """Grava o resultado da operação no caminho fornecido."""
