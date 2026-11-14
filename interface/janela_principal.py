from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from operacoes.operacao_arquivo import OperacaoArquivo
from servicos.servico_operacao import DestinoExistenteError, ServicoOperacao


class JanelaPrincipal(ctk.CTk):
    def __init__(
        self,
        servico_operacao: ServicoOperacao,
        conversao_jpg_para_png: OperacaoArquivo,
        conversao_png_para_jpg: OperacaoArquivo,
    ):
        super().__init__()
        self.title("SCRAP")
        self.geometry("800x500")

        self.servico_operacao = servico_operacao
        self.conversao_jpg_para_png = conversao_jpg_para_png
        self.conversao_png_para_jpg = conversao_png_para_jpg

        ctk.CTkButton(
            self, text="Converter JPG → PNG", command=self.converter_jpg
        ).pack(pady=(28, 8))
        ctk.CTkButton(
            self, text="Converter PNG → JPG", command=self.converter_png
        ).pack(pady=8)
        self.mensagem = ctk.CTkLabel(self, text="", wraplength=660)
        self.mensagem.pack(padx=24, pady=12)

    def converter_jpg(self):
        self.converter_imagem(
            self.conversao_jpg_para_png, "JPG", "PNG", ("*.jpg", "*.jpeg")
        )

    def converter_png(self):
        self.converter_imagem(self.conversao_png_para_jpg, "PNG", "JPG", ("*.png",))

    def converter_imagem(
        self,
        operacao: OperacaoArquivo,
        formato_origem: str,
        formato_destino: str,
        extensoes_origem: tuple[str, ...],
    ):
        self.mensagem.configure(text="")
        arquivo = filedialog.askopenfilename(
            parent=self,
            title=f"Selecionar imagem {formato_origem}",
            filetypes=[(f"Imagens {formato_origem}", extensoes_origem)],
        )
        if not arquivo:
            return

        origem = Path(arquivo)
        pasta = filedialog.askdirectory(
            parent=self,
            title=f"Escolher pasta para salvar o {formato_destino}",
            initialdir=str(origem.parent),
            mustexist=True,
        )
        if not pasta:
            return

        destino = Path(pasta) / f"{origem.stem}.{formato_destino.lower()}"

        try:
            try:
                resultado = self.servico_operacao.executar(operacao, (origem,), destino)
            except DestinoExistenteError:
                if not messagebox.askyesno(
                    "Substituir arquivo",
                    f"Já existe um arquivo chamado {destino.name}. Deseja substituí-lo?",
                    parent=self,
                ):
                    return
                resultado = self.servico_operacao.executar(
                    operacao, (origem,), destino, sobrescrever=True
                )
        except ValueError as erro:
            self.mensagem.configure(text=str(erro))
        except OSError:
            self.mensagem.configure(
                text=f"Não foi possível salvar o {formato_destino} no destino escolhido."
            )
        else:
            self.mensagem.configure(text=f"{formato_destino} salvo em {resultado}")
