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
        compactacao_zip: OperacaoArquivo,
    ):
        super().__init__()
        self.title("SCRAP")
        self.geometry("800x500")

        self.servico_operacao = servico_operacao
        self.conversao_jpg_para_png = conversao_jpg_para_png
        self.conversao_png_para_jpg = conversao_png_para_jpg
        self.compactacao_zip = compactacao_zip

        ctk.CTkButton(
            self, text="Converter JPG → PNG", command=self.converter_jpg
        ).pack(pady=(28, 8))
        ctk.CTkButton(
            self, text="Converter PNG → JPG", command=self.converter_png
        ).pack(pady=8)
        ctk.CTkButton(
            self, text="Compactar Arquivos em ZIP", command=self.compactar_arquivos_zip
        ).pack(pady=8)
        ctk.CTkButton(
            self, text="Compactar Pasta em ZIP", command=self.compactar_pasta_zip
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
        self._executar_operacao(operacao, (origem,), destino, formato_destino)

    def compactar_arquivos_zip(self):
        self.mensagem.configure(text="")
        arquivos = filedialog.askopenfilenames(
            parent=self,
            title="Selecionar arquivos para compactar",
        )
        if not arquivos:
            return

        origens = tuple(Path(arquivo) for arquivo in arquivos)
        nome_zip = f"{origens[0].stem}.zip" if len(origens) == 1 else "arquivos.zip"
        self._escolher_destino_e_compactar(origens, origens[0].parent, nome_zip)

    def compactar_pasta_zip(self):
        self.mensagem.configure(text="")
        pasta_origem = filedialog.askdirectory(
            parent=self,
            title="Selecionar pasta para compactar",
            mustexist=True,
        )
        if not pasta_origem:
            return

        origem = Path(pasta_origem)
        nome_zip = f"{origem.name}.zip"
        self._escolher_destino_e_compactar((origem,), origem.parent, nome_zip)

    def _escolher_destino_e_compactar(
        self, origens: tuple[Path, ...], pasta_inicial: Path, nome_sugerido: str
    ):
        pasta_destino = filedialog.askdirectory(
            parent=self,
            title="Escolher pasta para salvar o ZIP",
            initialdir=str(pasta_inicial),
            mustexist=True,
        )
        if not pasta_destino:
            return

        destino = Path(pasta_destino) / nome_sugerido
        self._executar_operacao(self.compactacao_zip, origens, destino, "ZIP")

    def _executar_operacao(
        self,
        operacao: OperacaoArquivo,
        origens: tuple[Path, ...],
        destino: Path,
        formato_destino: str,
    ):
        try:
            try:
                resultado = self.servico_operacao.executar(operacao, origens, destino)
            except DestinoExistenteError:
                if not messagebox.askyesno(
                    "Substituir arquivo",
                    f"Já existe um arquivo chamado {destino.name}. Deseja substituí-lo?",
                    parent=self,
                ):
                    return
                resultado = self.servico_operacao.executar(
                    operacao, origens, destino, sobrescrever=True
                )
        except ValueError as erro:
            self.mensagem.configure(text=str(erro))
        except OSError:
            self.mensagem.configure(
                text=f"Não foi possível salvar o {formato_destino} no destino escolhido."
            )
        else:
            self.mensagem.configure(text=f"{formato_destino} salvo em {resultado}")