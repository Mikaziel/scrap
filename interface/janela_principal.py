from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from operacoes.operacao_arquivo import OperacaoArquivo
from servicos.servico_operacao import DestinoExistenteError, ServicoOperacao


class JanelaPrincipal(ctk.CTk):
    def __init__(self, servico_operacao: ServicoOperacao, conversao_imagem: OperacaoArquivo):
        super().__init__()
        self.title("SCRAP")
        self.geometry("800x500")

        self.servico_operacao = servico_operacao
        self.conversao_imagem = conversao_imagem

        ctk.CTkButton(self, text="Converter JPG → PNG", command=self.converter_jpg).pack(pady=(28, 8))
        self.mensagem = ctk.CTkLabel(self, text="", wraplength=660)
        self.mensagem.pack(padx=24, pady=12)

    def converter_jpg(self):
        self.mensagem.configure(text="")
        arquivo = filedialog.askopenfilename(
            parent=self,
            title="Selecionar imagem JPG",
            filetypes=[("Imagens JPEG", ("*.jpg", "*.jpeg"))],
        )
        if not arquivo:
            return

        origem = Path(arquivo)
        pasta = filedialog.askdirectory(
            parent=self,
            title="Escolher pasta para salvar o PNG",
            initialdir=str(origem.parent),
            mustexist=True,
        )
        if not pasta:
            return

        destino = Path(pasta) / f"{origem.stem}.png"

        try:
            try:
                resultado = self.servico_operacao.executar(self.conversao_imagem, (origem,), destino)
            except DestinoExistenteError:
                if not messagebox.askyesno(
                    "Substituir arquivo",
                    f"Já existe um arquivo chamado {destino.name}. Deseja substituí-lo?",
                    parent=self,
                ):
                    return
                resultado = self.servico_operacao.executar(
                    self.conversao_imagem, (origem,), destino, sobrescrever=True
                )
        except ValueError as erro:
            self.mensagem.configure(text=str(erro))
        except OSError:
            self.mensagem.configure(text="Não foi possível salvar o PNG no destino escolhido.")
        else:
            self.mensagem.configure(text=f"PNG salvo em {resultado}")
