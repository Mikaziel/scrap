from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from operacoes.operacao_arquivo import OperacaoArquivo
from servicos.servico_operacao import DestinoExistenteError, ServicoOperacao

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class JanelaPrincipal(ctk.CTk):
    def __init__(
        self,
        servico_operacao: ServicoOperacao,
        conversao_jpg_para_png: OperacaoArquivo,
        conversao_png_para_jpg: OperacaoArquivo,
        conversao_imagem_para_pdf: OperacaoArquivo,
        conversao_docx_para_pdf: OperacaoArquivo,
        compactacao_zip: OperacaoArquivo,
    ):
        super().__init__()
        self.title("SCRAP — Conversão e Compressão de Arquivos")
        self.geometry("980x620")
        self.minsize(860, 540)

        self.servico_operacao = servico_operacao
        self.conversao_jpg_para_png = conversao_jpg_para_png
        self.conversao_png_para_jpg = conversao_png_para_jpg
        self.conversao_imagem_para_pdf = conversao_imagem_para_pdf
        self.conversao_docx_para_pdf = conversao_docx_para_pdf
        self.compactacao_zip = compactacao_zip

        # Estrutura temporária que futuramente virá do Banco de Dados (SQLite/ORM)
        self.registros_historico: list[dict[str, str]] = []

        # Layout principal: Coluna 0 = Sidebar | Coluna 1 = Conteúdo Principal
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._construir_sidebar()
        self._construir_area_principal()
        self._construir_barra_status()

        self.mostrar_secao("conversao")

    # =========================================================================
    # CONSTRUÇÃO DA INTERFACE (LAYOUT MODERNO)
    # =========================================================================

    def _construir_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=230, corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar.grid_rowconfigure(5, weight=1)

        logo = ctk.CTkLabel(
            self.sidebar,
            text="⚡ SCRAP",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        logo.grid(row=0, column=0, padx=24, pady=(28, 4), sticky="w")

        subtitulo = ctk.CTkLabel(
            self.sidebar,
            text="File Studio & Converter",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray60"),
        )
        subtitulo.grid(row=1, column=0, padx=24, pady=(0, 28), sticky="w")

        self.botoes_nav: dict[str, ctk.CTkButton] = {}
        itens_menu = [
            ("conversao", "🔄   Conversão"),
            ("compactacao", "📦   Compactação"),
            ("historico", "🕒   Histórico"),
        ]

        for idx, (chave, rotulo) in enumerate(itens_menu, start=2):
            btn = ctk.CTkButton(
                self.sidebar,
                text=rotulo,
                anchor="w",
                height=42,
                corner_radius=8,
                font=ctk.CTkFont(size=14, weight="bold"),
                fg_color="transparent",
                text_color=("gray15", "gray85"),
                hover_color=("gray80", "gray25"),
                command=lambda c=chave: self.mostrar_secao(c),
            )
            btn.grid(row=idx, column=0, padx=16, pady=5, sticky="ew")
            self.botoes_nav[chave] = btn

        lbl_tema = ctk.CTkLabel(
            self.sidebar,
            text="Aparência:",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray60"),
        )
        lbl_tema.grid(row=6, column=0, padx=20, pady=(10, 4), sticky="w")

        seletor_tema = ctk.CTkOptionMenu(
            self.sidebar,
            values=["Escuro", "Claro", "Sistema"],
            command=self._alterar_tema,
            height=32,
        )
        seletor_tema.grid(row=7, column=0, padx=20, pady=(0, 24), sticky="ew")

    def _construir_area_principal(self):
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=0, column=1, padx=28, pady=(24, 12), sticky="nsew")
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

        self.secoes: dict[str, ctk.CTkFrame] = {
            "conversao": self._criar_secao_conversao(),
            "compactacao": self._criar_secao_compactacao(),
            "historico": self._criar_secao_historico(),
        }

    def _construir_barra_status(self):
        self.barra_status = ctk.CTkFrame(
            self, height=54, corner_radius=10, fg_color=("gray88", "gray17")
        )
        self.barra_status.grid(row=1, column=1, padx=28, pady=(0, 20), sticky="ew")
        self.barra_status.grid_columnconfigure(1, weight=1)

        self.indicador_status = ctk.CTkLabel(
            self.barra_status,
            text="●",
            font=ctk.CTkFont(size=18),
            text_color=("gray45", "gray55"),
        )
        self.indicador_status.grid(row=0, column=0, padx=(16, 8), pady=12)

        self.mensagem = ctk.CTkLabel(
            self.barra_status,
            text="Pronto. Selecione uma operação acima para começar.",
            font=ctk.CTkFont(size=13),
            anchor="w",
            justify="left",
            wraplength=640,
        )
        self.mensagem.grid(row=0, column=1, padx=(0, 16), pady=12, sticky="ew")

    # =========================================================================
    # SEÇÕES E COMPONENTES REUTILIZÁVEIS (CARDS)
    # =========================================================================

    def _criar_cabecalho_secao(
        self, parent: ctk.CTkFrame, titulo: str, descricao: str
    ) -> None:
        ctk.CTkLabel(
            parent,
            text=titulo,
            font=ctk.CTkFont(size=24, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            parent,
            text=descricao,
            font=ctk.CTkFont(size=13),
            text_color=("gray35", "gray65"),
        ).grid(row=1, column=0, pady=(4, 20), sticky="w")

    def _criar_card_operacao(
        self,
        parent: ctk.CTkFrame,
        linha: int,
        coluna: int,
        icone_badge: str,
        titulo: str,
        descricao: str,
        texto_botao: str,
        comando,
    ):
        card = ctk.CTkFrame(
            parent,
            corner_radius=12,
            border_width=1,
            border_color=("gray78", "gray25"),
        )
        card.grid(row=linha, column=coluna, padx=8, pady=8, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)

        badge = ctk.CTkLabel(
            card,
            text=icone_badge,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("gray82", "gray25"),
            corner_radius=6,
            padx=10,
            pady=4,
        )
        badge.grid(row=0, column=0, padx=20, pady=(18, 10), sticky="w")

        ctk.CTkLabel(
            card,
            text=titulo,
            font=ctk.CTkFont(size=17, weight="bold"),
        ).grid(row=1, column=0, padx=20, pady=(0, 6), sticky="w")

        ctk.CTkLabel(
            card,
            text=descricao,
            font=ctk.CTkFont(size=13),
            text_color=("gray35", "gray65"),
            justify="left",
            wraplength=270,
        ).grid(row=2, column=0, padx=20, pady=(0, 18), sticky="w")

        ctk.CTkButton(
            card,
            text=texto_botao,
            height=38,
            corner_radius=8,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=comando,
        ).grid(row=3, column=0, padx=20, pady=(0, 18), sticky="ew")

    def _criar_secao_conversao(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.container, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(2, weight=1)

        self._criar_cabecalho_secao(
            frame,
            "Conversão de Arquivos",
            "Transforme imagens e documentos mantendo a fidelidade visual e metadados.",
        )

        grade = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        grade.grid(row=2, column=0, sticky="nsew")
        grade.grid_columnconfigure((0, 1), weight=1)

        conversoes_disponiveis = [
            (
                "IMAGEM • JPG → PNG",
                "Converter JPG para PNG",
                "Converte fotos JPEG para o formato PNG sem perdas e com orientação EXIF corrigida.",
                "Selecionar JPG",
                self.converter_jpg,
            ),
            (
                "IMAGEM • PNG → JPG",
                "Converter PNG para JPG",
                "Transforma imagens PNG em arquivos JPEG compactos aplicando fundo branco na transparência.",
                "Selecionar PNG",
                self.converter_png,
            ),
            (
                "DOCUMENTO • IMG → PDF",
                "Converter Imagens para PDF",
                "Gera um documento PDF a partir de uma ou várias imagens (JPG e PNG), criando páginas em sequência.",
                "Selecionar Imagens",
                self.converter_imagens_pdf,
            ),
            (
                "DOCUMENTO • DOCX → PDF",
                "Converter DOCX para PDF",
                "Transforma documentos do Word (.docx) em arquivos PDF prontos para leitura e impressão.",
                "Selecionar DOCX",
                self.converter_docx_pdf,
            ),
        ]

        for idx, (badge, titulo, desc, texto_btn, cmd) in enumerate(
            conversoes_disponiveis
        ):
            linha, coluna = divmod(idx, 2)
            self._criar_card_operacao(
                grade, linha, coluna, badge, titulo, desc, texto_btn, cmd
            )

        return frame

    def _criar_secao_compactacao(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.container, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(2, weight=1)

        self._criar_cabecalho_secao(
            frame,
            "Compactação em ZIP",
            "Agrupe e comprima múltiplos arquivos avulsos ou diretórios inteiros.",
        )

        grade = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        grade.grid(row=2, column=0, sticky="nsew")
        grade.grid_columnconfigure((0, 1), weight=1)

        opcoes_zip = [
            (
                "ARQUIVOS • MÚLTIPLOS",
                "Compactar Arquivos em ZIP",
                "Selecione um ou vários arquivos individuais para gerar um pacote .zip único.",
                "Escolher Arquivos",
                self.compactar_arquivos_zip,
            ),
            (
                "DIRETÓRIO • RECURSIVO",
                "Compactar Pasta em ZIP",
                "Comprime uma pasta completa preservando toda a estrutura interna de subpastas.",
                "Escolher Pasta",
                self.compactar_pasta_zip,
            ),
        ]

        for idx, (badge, titulo, desc, texto_btn, cmd) in enumerate(opcoes_zip):
            linha, coluna = divmod(idx, 2)
            self._criar_card_operacao(
                grade, linha, coluna, badge, titulo, desc, texto_btn, cmd
            )

        return frame

    def _criar_secao_historico(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.container, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(2, weight=1)

        self._criar_cabecalho_secao(
            frame,
            "Histórico de Operações",
            "Registro das conversões e compactações realizadas (preparado para persistência em banco de dados).",
        )

        self.lista_historico_ui = ctk.CTkScrollableFrame(
            frame, corner_radius=12, border_width=1, border_color=("gray78", "gray25")
        )
        self.lista_historico_ui.grid(row=2, column=0, sticky="nsew")
        self.lista_historico_ui.grid_columnconfigure(0, weight=1)

        self._atualizar_lista_historico_ui()
        return frame

    # =========================================================================
    # NAVEGAÇÃO, TEMA E HISTÓRICO
    # =========================================================================

    def mostrar_secao(self, chave: str):
        for nome, frame in self.secoes.items():
            if nome == chave:
                frame.grid(row=0, column=0, sticky="nsew")
            else:
                frame.grid_forget()

        for nome, btn in self.botoes_nav.items():
            if nome == chave:
                btn.configure(fg_color=("gray75", "gray28"))
            else:
                btn.configure(fg_color="transparent")

    def _alterar_tema(self, escolha: str):
        mapa = {"Escuro": "Dark", "Claro": "Light", "Sistema": "System"}
        ctk.set_appearance_mode(mapa.get(escolha, "Dark"))

    def _definir_status(self, texto: str, tipo: str = "neutro"):
        cores = {
            "neutro": ("gray45", "gray55"),
            "sucesso": ("#16a34a", "#4ade80"),
            "erro": ("#dc2626", "#f87171"),
        }
        self.indicador_status.configure(text_color=cores.get(tipo, cores["neutro"]))
        self.mensagem.configure(text=texto)

    def _registrar_no_historico(
        self, tipo_operacao: str, origens: tuple[Path, ...], destino: Path
    ):
        horario = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        resumo_origem = (
            origens[0].name
            if len(origens) == 1
            else f"{len(origens)} arquivos selecionados"
        )
        self.registros_historico.insert(
            0,
            {
                "horario": horario,
                "operacao": tipo_operacao,
                "origem": resumo_origem,
                "destino": str(destino),
            },
        )
        self._atualizar_lista_historico_ui()

    def _atualizar_lista_historico_ui(self):
        for widget in self.lista_historico_ui.winfo_children():
            widget.destroy()

        if not self.registros_historico:
            ctk.CTkLabel(
                self.lista_historico_ui,
                text="Nenhuma operação registrada nesta sessão ainda.",
                font=ctk.CTkFont(size=13),
                text_color=("gray40", "gray60"),
            ).grid(row=0, column=0, padx=20, pady=36)
            return

        for idx, item in enumerate(self.registros_historico):
            linha = ctk.CTkFrame(
                self.lista_historico_ui, corner_radius=8, fg_color=("gray86", "gray20")
            )
            linha.grid(row=idx, column=0, padx=10, pady=6, sticky="ew")
            linha.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(
                linha,
                text=item["operacao"],
                font=ctk.CTkFont(size=12, weight="bold"),
                width=90,
                anchor="w",
            ).grid(row=0, column=0, padx=14, pady=10, sticky="w")

            ctk.CTkLabel(
                linha,
                text=f"{item['origem']}  →  {item['destino']}",
                font=ctk.CTkFont(size=12),
                anchor="w",
            ).grid(row=0, column=1, padx=8, pady=10, sticky="ew")

            ctk.CTkLabel(
                linha,
                text=item["horario"],
                font=ctk.CTkFont(size=11),
                text_color=("gray40", "gray60"),
            ).grid(row=0, column=2, padx=14, pady=10, sticky="e")

    # =========================================================================
    # AÇÕES DE CONVERSÃO E COMPACTAÇÃO
    # =========================================================================

    def converter_jpg(self):
        self.converter_imagem(
            self.conversao_jpg_para_png, "JPG", "PNG", ("*.jpg", "*.jpeg")
        )

    def converter_png(self):
        self.converter_imagem(self.conversao_png_para_jpg, "PNG", "JPG", ("*.png",))

    def converter_docx_pdf(self):
        self._definir_status("Selecionando documento DOCX...", "neutro")
        arquivo = filedialog.askopenfilename(
            parent=self,
            title="Selecionar documento DOCX",
            filetypes=[("Documento do Word", ("*.docx",))],
        )
        if not arquivo:
            self._definir_status("Operação cancelada.", "neutro")
            return

        origem = Path(arquivo)
        pasta = filedialog.askdirectory(
            parent=self,
            title="Escolher pasta para salvar o PDF",
            initialdir=str(origem.parent),
            mustexist=True,
        )
        if not pasta:
            self._definir_status("Operação cancelada.", "neutro")
            return

        destino = Path(pasta) / f"{origem.stem}.pdf"
        self._executar_operacao(self.conversao_docx_para_pdf, (origem,), destino, "PDF")

    def converter_imagem(
        self,
        operacao: OperacaoArquivo,
        formato_origem: str,
        formato_destino: str,
        extensoes_origem: tuple[str, ...],
    ):
        self._definir_status("Selecionando arquivo de origem...", "neutro")
        arquivo = filedialog.askopenfilename(
            parent=self,
            title=f"Selecionar imagem {formato_origem}",
            filetypes=[(f"Imagens {formato_origem}", extensoes_origem)],
        )
        if not arquivo:
            self._definir_status("Operação cancelada.", "neutro")
            return

        origem = Path(arquivo)
        pasta = filedialog.askdirectory(
            parent=self,
            title=f"Escolher pasta para salvar o {formato_destino}",
            initialdir=str(origem.parent),
            mustexist=True,
        )
        if not pasta:
            self._definir_status("Operação cancelada.", "neutro")
            return

        destino = Path(pasta) / f"{origem.stem}.{formato_destino.lower()}"
        self._executar_operacao(operacao, (origem,), destino, formato_destino)

    def converter_imagens_pdf(self):
        self._definir_status("Selecionando imagens para gerar o PDF...", "neutro")
        arquivos = filedialog.askopenfilenames(
            parent=self,
            title="Selecionar imagens para converter em PDF",
            filetypes=[("Imagens suportadas", ("*.jpg", "*.jpeg", "*.png"))],
        )
        if not arquivos:
            self._definir_status("Operação cancelada.", "neutro")
            return

        origens = tuple(Path(arquivo) for arquivo in arquivos)
        pasta = filedialog.askdirectory(
            parent=self,
            title="Escolher pasta para salvar o PDF",
            initialdir=str(origens[0].parent),
            mustexist=True,
        )
        if not pasta:
            self._definir_status("Operação cancelada.", "neutro")
            return

        nome_pdf = (
            f"{origens[0].stem}.pdf" if len(origens) == 1 else "imagens_convertidas.pdf"
        )
        destino = Path(pasta) / nome_pdf
        self._executar_operacao(self.conversao_imagem_para_pdf, origens, destino, "PDF")

    def compactar_arquivos_zip(self):
        self._definir_status("Selecionando arquivos para compactar...", "neutro")
        arquivos = filedialog.askopenfilenames(
            parent=self,
            title="Selecionar arquivos para compactar",
        )
        if not arquivos:
            self._definir_status("Operação cancelada.", "neutro")
            return

        origens = tuple(Path(arquivo) for arquivo in arquivos)
        nome_zip = f"{origens[0].stem}.zip" if len(origens) == 1 else "arquivos.zip"
        self._escolher_destino_e_compactar(origens, origens[0].parent, nome_zip)

    def compactar_pasta_zip(self):
        self._definir_status("Selecionando pasta para compactar...", "neutro")
        pasta_origem = filedialog.askdirectory(
            parent=self,
            title="Selecionar pasta para compactar",
            mustexist=True,
        )
        if not pasta_origem:
            self._definir_status("Operação cancelada.", "neutro")
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
            self._definir_status("Operação cancelada.", "neutro")
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
                    self._definir_status("Operação cancelada pelo usuário.", "neutro")
                    return
                resultado = self.servico_operacao.executar(
                    operacao, origens, destino, sobrescrever=True
                )
        except ValueError as erro:
            self._definir_status(str(erro), "erro")
        except OSError:
            self._definir_status(
                f"Não foi possível salvar o {formato_destino} no destino escolhido.",
                "erro",
            )
        else:
            self._definir_status(f"{formato_destino} salvo em {resultado}", "sucesso")
            self._registrar_no_historico(formato_destino, origens, resultado)