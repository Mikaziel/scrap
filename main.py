from interface.janela_principal import JanelaPrincipal
from operacoes.compactacao_zip import CompactacaoZip
from operacoes.conversao_docx_pdf import ConversaoDocxParaPdf
from operacoes.conversao_imagem import ConversaoImagem
from operacoes.conversao_pdf import ConversaoImagemParaPdf
from servicos.servico_operacao import ServicoOperacao


def main():
    janela = JanelaPrincipal(
        ServicoOperacao(),
        conversao_jpg_para_png=ConversaoImagem("PNG"),
        conversao_png_para_jpg=ConversaoImagem("JPEG"),
        conversao_imagem_para_pdf=ConversaoImagemParaPdf(),
        conversao_docx_para_pdf=ConversaoDocxParaPdf(),
        compactacao_zip=CompactacaoZip(),
    )
    janela.mainloop()


if __name__ == "__main__":
    main()