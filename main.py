from interface.janela_principal import JanelaPrincipal
from operacoes.conversao_imagem import ConversaoImagem
from servicos.servico_operacao import ServicoOperacao


def main():
    janela = JanelaPrincipal(
        ServicoOperacao(),
        conversao_jpg_para_png=ConversaoImagem("PNG"),
        conversao_png_para_jpg=ConversaoImagem("JPEG"),
    )
    janela.mainloop()


if __name__ == "__main__":
    main()
