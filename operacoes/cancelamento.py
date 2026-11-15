from threading import Event, Lock


class OperacaoCancelada(Exception):
    pass


class CancelamentoOperacao:
    def __init__(self):
        self._solicitacao = Event()
        self._trava = Lock()
        self._publicando = False

    def solicitar(self) -> bool:
        with self._trava:
            if self._publicando or self._solicitacao.is_set():
                return False
            self._solicitacao.set()
            return True

    @property
    def solicitado(self) -> bool:
        return self._solicitacao.is_set()

    def verificar(self) -> None:
        if self.solicitado:
            raise OperacaoCancelada

    def iniciar_publicacao(self) -> None:
        # Ou o pedido de cancelamento é aceito, ou o serviço pode entregar o arquivo.
        with self._trava:
            self.verificar()
            self._publicando = True
