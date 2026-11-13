from interface.janela_principal import JanelaPrincipal
from operacoes.conversao_imagem import ConversaoImagem
from servicos.servico_operacao import ServicoOperacao


def main():
    janela = JanelaPrincipal(ServicoOperacao(), ConversaoImagem())
    janela.mainloop()


if __name__ == "__main__":
    main()
