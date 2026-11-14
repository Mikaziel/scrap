from interface.janela_principal import JanelaPrincipal
from operacoes.compactacao_zip import CompactacaoZip
from operacoes.conversao_imagem import ConversaoImagem
from servicos.servico_operacao import ServicoOperacao


def main():
    janela = JanelaPrincipal(
        ServicoOperacao(),
        conversao_jpg_para_png=ConversaoImagem("PNG"),
        conversao_png_para_jpg=ConversaoImagem("JPEG"),
        compactacao_zip=CompactacaoZip(),
    )
    janela.mainloop()


if __name__ == "__main__":
    main()