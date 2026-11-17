from pathlib import Path
from threading import Thread
from tkinter import filedialog, messagebox

import customtkinter as ctk

from interface.icones import carregar_icones
from operacoes.cancelamento import CancelamentoOperacao, OperacaoCancelada
from operacoes.descompactacao_zip import DescompactacaoZip
from operacoes.operacao_arquivo import OperacaoArquivo
from servicos.repositorio_historico import RegistroHistorico, RepositorioHistorico
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
        conversao_pdf_para_docx: OperacaoArquivo,
        compactacao_zip: OperacaoArquivo,
        descompactacao_zip: OperacaoArquivo | None = None,
        repositorio_historico: RepositorioHistorico | None = None,
    ):
        super().__init__()
        self.title("SCRAP — Conversão e Compressão de Arquivos")
        self.geometry("980x640")
        self.minsize(860, 560)

        self.servico_operacao = servico_operacao
        self.conversao_jpg_para_png = conversao_jpg_para_png
        self.conversao_png_para_jpg = conversao_png_para_jpg
        self.conversao_imagem_para_pdf = conversao_imagem_para_pdf
        self.conversao_docx_para_pdf = conversao_docx_para_pdf
        self.conversao_pdf_para_docx = conversao_pdf_para_docx
        self.compactacao_zip = compactacao_zip
        self.descompactacao_zip = descompactacao_zip or DescompactacaoZip()
        self.repositorio_historico = repositorio_historico or RepositorioHistorico()

        # Controle de execução em background e cancelamento
        self._cancelamento_atual: CancelamentoOperacao | None = None
        self._thread_operacao: Thread | None = None
        self._botoes_operacao: list[ctk.CTkButton] = []

        # Carrega (e gera se necessário) os ícones na pasta interface/icones/
        self.icones = carregar_icones()

        # Layout principal: Coluna 0 = Sidebar | Coluna 1 = Conteúdo Principal
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._construir_sidebar()
        self._construir_area_principal()
        self._construir_barra_status()

        self.mostrar_secao("conversao")

    # =========================================================================
    # CONSTRUÇÃO DA INTERFACE (LAYOUT MODERNO COM ÍCONES PNG)
    # =========================================================================

    def _construir_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=230, corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar.grid_rowconfigure(5, weight=1)

        logo = ctk.CTkLabel(
            self.sidebar,
            text="  SCRAP",
            image=self.icones["logo"],
            compound="left",
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
            ("conversao", "  Conversão", self.icones["conversao"]),
            ("compactacao", "  Compactação", self.icones["compactacao"]),
            ("historico", "  Histórico (30 dias)", self.icones["historico"]),
        ]

        for idx, (chave, rotulo, icone) in enumerate(itens_menu, start=2):
            btn = ctk.CTkButton(
                self.sidebar,
                text=rotulo,
                image=icone,
                compound="left",
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
            self, height=62, corner_radius=10, fg_color=("gray88", "gray17")
        )
        self.barra_status.grid(row=1, column=1, padx=28, pady=(0, 20), sticky="ew")
        self.barra_status.grid_columnconfigure(1, weight=1)

        self.indicador_status = ctk.CTkFrame(
            self.barra_status,
            width=12,
            height=12,
            corner_radius=6,
            fg_color=("gray45", "gray55"),
        )
        self.indicador_status.grid(row=0, column=0, padx=(18, 10), pady=16)

        self.mensagem = ctk.CTkLabel(
            self.barra_status,
            text="Pronto. Selecione uma operação acima para começar.",
            font=ctk.CTkFont(size=13),
            anchor="w",
            justify="left",
            wraplength=520,
        )
        self.mensagem.grid(row=0, column=1, padx=(0, 12), pady=12, sticky="ew")

        self.botao_cancelar = ctk.CTkButton(
            self.barra_status,
            text=" Cancelar",
            image=self.icones["cancelar"],
            compound="left",
            width=110,
            height=32,
            corner_radius=6,
            fg_color=("#dc2626", "#b91c1c"),
            hover_color=("#b91c1c", "#991b1b"),
            text_color="#ffffff",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.cancelar_operacao_atual,
        )

        self.barra_progresso = ctk.CTkProgressBar(
            self.barra_status, mode="indeterminate", height=6
        )

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

        botao = ctk.CTkButton(
            card,
            text=texto_botao,
            height=38,
            corner_radius=8,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=comando,
        )
        botao.grid(row=3, column=0, padx=20, pady=(0, 18), sticky="ew")
        self._botoes_operacao.append(botao)

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
                "IMAGEM  |  JPG -> PNG",
                "Converter JPG para PNG",
                "Converte fotos JPEG para o formato PNG sem perdas e com orientação EXIF corrigida.",
                "Selecionar JPG",
                self.converter_jpg,
            ),
            (
                "IMAGEM  |  PNG -> JPG",
                "Converter PNG para JPG",
                "Transforma imagens PNG em arquivos JPEG compactos aplicando fundo branco na transparência.",
                "Selecionar PNG",
                self.converter_png,
            ),
            (
                "DOCUMENTO  |  IMG -> PDF",
                "Converter Imagens para PDF",
                "Gera um documento PDF a partir de uma ou várias imagens (JPG e PNG), criando páginas em sequência.",
                "Selecionar Imagens",
                self.converter_imagens_pdf,
            ),
            (
                "DOCUMENTO  |  DOCX -> PDF",
                "Converter DOCX para PDF",
                "Transforma documentos do Word (.docx) em arquivos PDF prontos para leitura e impressão.",
                "Selecionar DOCX",
                self.converter_docx_pdf,
            ),
            (
                "DOCUMENTO  |  PDF -> DOCX",
                "Converter PDF para DOCX",
                "Converte arquivos PDF em documentos editáveis do Word (.docx) preservando textos e estrutura.",
                "Selecionar PDF",
                self.converter_pdf_docx,
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
            "Compactação e Extração ZIP",
            "Comprima múltiplos arquivos, pastas inteiras ou extraia pacotes .zip com segurança.",
        )

        grade = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        grade.grid(row=2, column=0, sticky="nsew")
        grade.grid_columnconfigure((0, 1), weight=1)

        opcoes_zip = [
            (
                "ARQUIVOS  |  MÚLTIPLOS",
                "Compactar Arquivos em ZIP",
                "Selecione um ou vários arquivos individuais para gerar um pacote .zip único.",
                "Escolher Arquivos",
                self.compactar_arquivos_zip,
            ),
            (
                "DIRETÓRIO  |  RECURSIVO",
                "Compactar Pasta em ZIP",
                "Comprime uma pasta completa preservando toda a estrutura interna de subpastas.",
                "Escolher Pasta",
                self.compactar_pasta_zip,
            ),
            (
                "EXTRAÇÃO  |  ZIP -> PASTA",
                "Extrair Arquivo ZIP",
                "Descompacta o conteúdo de um arquivo .zip em uma pasta, mantendo as subpastas originais.",
                "Selecionar ZIP",
                self.descompactar_arquivo_zip,
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
        frame.grid_rowconfigure(3, weight=1)

        self._criar_cabecalho_secao(
            frame,
            "Histórico de Operações (Últimos 30 dias)",
            "Arquivos convertidos ou compactados ficam salvos no banco SQLite local por 30 dias para recuperação rápida.",
        )

        barra_topo = ctk.CTkFrame(
            frame, corner_radius=10, fg_color=("gray88", "gray17")
        )
        barra_topo.grid(row=2, column=0, pady=(0, 12), sticky="ew")
        barra_topo.grid_columnconfigure(0, weight=1)

        self.lbl_resumo_historico = ctk.CTkLabel(
            barra_topo,
            text="0 arquivos salvos  |  Espaço utilizado: 0 B",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        )
        self.lbl_resumo_historico.grid(row=0, column=0, padx=16, pady=10, sticky="w")

        self.btn_limpar_historico = ctk.CTkButton(
            barra_topo,
            text=" Limpar Histórico",
            image=self.icones["excluir"],
            compound="left",
            width=150,
            height=32,
            corner_radius=6,
            fg_color=("#dc2626", "#b91c1c"),
            hover_color=("#b91c1c", "#991b1b"),
            text_color="#ffffff",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.limpar_todo_historico,
        )
        self.btn_limpar_historico.grid(row=0, column=1, padx=12, pady=8, sticky="e")

        self.lista_historico_ui = ctk.CTkScrollableFrame(
            frame, corner_radius=12, border_width=1, border_color=("gray78", "gray25")
        )
        self.lista_historico_ui.grid(row=3, column=0, sticky="nsew")
        self.lista_historico_ui.grid_columnconfigure(0, weight=1)

        self._atualizar_lista_historico_ui()
        return frame

    # =========================================================================
    # NAVEGAÇÃO, TEMA E GERENCIAMENTO DO HISTÓRICO (SQLITE)
    # =========================================================================

    def mostrar_secao(self, chave: str):
        if chave == "historico":
            self._atualizar_lista_historico_ui()

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
            "processando": ("#2563eb", "#60a5fa"),
            "sucesso": ("#16a34a", "#4ade80"),
            "erro": ("#dc2626", "#f87171"),
        }
        self.indicador_status.configure(fg_color=cores.get(tipo, cores["neutro"]))
        self.mensagem.configure(text=texto)

    def _alternar_estado_ocupado(self, ocupado: bool):
        estado_botoes = "disabled" if ocupado else "normal"
        for botao in self._botoes_operacao:
            botao.configure(state=estado_botoes)

        if ocupado:
            self.botao_cancelar.configure(state="normal", text=" Cancelar")
            self.botao_cancelar.grid(row=0, column=2, padx=(4, 16), pady=12, sticky="e")
            self.barra_progresso.grid(
                row=1, column=0, columnspan=3, padx=18, pady=(0, 10), sticky="ew"
            )
            self.barra_progresso.start()
        else:
            self.barra_progresso.stop()
            self.barra_progresso.grid_forget()
            self.botao_cancelar.grid_forget()

    def cancelar_operacao_atual(self):
        if self._cancelamento_atual is not None:
            if self._cancelamento_atual.solicitar():
                self.botao_cancelar.configure(state="disabled", text=" Cancelando...")
                self._definir_status("Cancelando operação...", "neutro")

    def _registrar_no_historico(
        self, tipo_operacao: str, origens: tuple[Path, ...], destino: Path
    ):
        try:
            self.repositorio_historico.registrar(tipo_operacao, origens, destino)
        except OSError:
            pass
        self._atualizar_lista_historico_ui()

    def _atualizar_lista_historico_ui(self):
        for widget in self.lista_historico_ui.winfo_children():
            widget.destroy()

        registros = self.repositorio_historico.listar()
        total_bytes = sum(item.tamanho_bytes for item in registros)
        espaco_str = RepositorioHistorico.formatar_tamanho(total_bytes)
        qtd = len(registros)
        sufixo = "arquivo salvo" if qtd == 1 else "arquivos salvos"
        self.lbl_resumo_historico.configure(
            text=f"{qtd} {sufixo}  |  Espaço utilizado no banco: {espaco_str}"
        )
        self.btn_limpar_historico.configure(state="normal" if registros else "disabled")

        if not registros:
            ctk.CTkLabel(
                self.lista_historico_ui,
                text="Nenhuma operação encontrada nos últimos 30 dias.",
                font=ctk.CTkFont(size=13),
                text_color=("gray40", "gray60"),
            ).grid(row=0, column=0, padx=20, pady=36)
            return

        for idx, item in enumerate(registros):
            linha = ctk.CTkFrame(
                self.lista_historico_ui, corner_radius=8, fg_color=("gray86", "gray20")
            )
            linha.grid(row=idx, column=0, padx=10, pady=6, sticky="ew")
            linha.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(
                linha,
                text=item.operacao,
                font=ctk.CTkFont(size=12, weight="bold"),
                width=64,
                anchor="w",
            ).grid(row=0, column=0, padx=(14, 8), pady=10, sticky="w")

            ctk.CTkLabel(
                linha,
                text=f"{item.resumo_origem}  ->  {item.nome_arquivo}",
                font=ctk.CTkFont(size=12),
                anchor="w",
            ).grid(row=0, column=1, padx=8, pady=10, sticky="ew")

            ctk.CTkLabel(
                linha,
                text=f"{item.tamanho_formatado}  |  {item.criado_em}",
                font=ctk.CTkFont(size=11),
                text_color=("gray40", "gray60"),
            ).grid(row=0, column=2, padx=10, pady=10, sticky="e")

            ctk.CTkButton(
                linha,
                text=" Recuperar",
                image=self.icones["recuperar"],
                compound="left",
                width=110,
                height=30,
                corner_radius=6,
                font=ctk.CTkFont(size=12, weight="bold"),
                command=lambda reg=item: self.recuperar_do_historico(reg),
            ).grid(row=0, column=3, padx=(4, 6), pady=8, sticky="e")

            ctk.CTkButton(
                linha,
                text="",
                image=self.icones["excluir"],
                width=34,
                height=30,
                corner_radius=6,
                fg_color=("gray65", "gray30"),
                hover_color=("#dc2626", "#b91c1c"),
                command=lambda reg=item: self.excluir_item_historico(reg),
            ).grid(row=0, column=4, padx=(0, 12), pady=8, sticky="e")

    def excluir_item_historico(self, registro: RegistroHistorico):
        if self._thread_operacao is not None and self._thread_operacao.is_alive():
            return

        if not messagebox.askyesno(
            "Excluir registro",
            f"Deseja remover '{registro.nome_arquivo}' ({registro.tamanho_formatado}) do histórico?",
            parent=self,
        ):
            return

        if self.repositorio_historico.excluir_registro(registro.id):
            self._atualizar_lista_historico_ui()
            self._definir_status(
                f"Registro '{registro.nome_arquivo}' removido do histórico.", "neutro"
            )

    def limpar_todo_historico(self):
        if self._thread_operacao is not None and self._thread_operacao.is_alive():
            return

        if not messagebox.askyesno(
            "Limpar todo o histórico",
            "Tem certeza que deseja apagar todos os arquivos salvos no histórico? Esta ação não pode ser desfeita.",
            parent=self,
        ):
            return

        removidos = self.repositorio_historico.limpar_tudo()
        self._atualizar_lista_historico_ui()
        self._definir_status(
            f"Histórico limpo ({removidos} registros removidos e banco otimizado).",
            "sucesso",
        )

    def recuperar_do_historico(self, registro: RegistroHistorico):
        if self._thread_operacao is not None and self._thread_operacao.is_alive():
            return

        self._definir_status(
            f"Escolhendo local e nome para recuperar {registro.nome_arquivo}...",
            "neutro",
        )
        pasta_original = Path(registro.destino_original).parent
        pasta_inicial = (
            pasta_original if pasta_original.exists() else Path.home()
        )
        extensao = Path(registro.nome_arquivo).suffix or ".dat"
        formato_label = extensao.lstrip(".").upper() or "ARQUIVO"

        destino = self._solicitar_destino_salvar(
            titulo=f"Recuperar {registro.nome_arquivo}",
            pasta_inicial=pasta_inicial,
            nome_sugerido=registro.nome_arquivo,
            formato_destino=formato_label,
            extensao_padrao=extensao,
        )
        if destino is None:
            self._definir_status("Recuperação cancelada.", "neutro")
            return

        try:
            try:
                resultado = self.repositorio_historico.recuperar_arquivo(
                    registro.id, destino
                )
            except DestinoExistenteError:
                if not messagebox.askyesno(
                    "Substituir arquivo",
                    f"Já existe um arquivo chamado {destino.name}. Deseja substituí-lo?",
                    parent=self,
                ):
                    self._definir_status("Recuperação cancelada pelo usuário.", "neutro")
                    return
                resultado = self.repositorio_historico.recuperar_arquivo(
                    registro.id, destino, sobrescrever=True
                )
        except ValueError as erro:
            self._definir_status(str(erro), "erro")
            self._atualizar_lista_historico_ui()
        except OSError:
            self._definir_status(
                f"Não foi possível recuperar {destino.name} no destino escolhido.",
                "erro",
            )
        else:
            self._definir_status(f"Arquivo recuperado em {resultado}", "sucesso")

    # =========================================================================
    # DIÁLOGO DE SALVAMENTO COM OPÇÃO DE RENOMEAR
    # =========================================================================

    def _solicitar_destino_salvar(
        self,
        *,
        titulo: str,
        pasta_inicial: Path,
        nome_sugerido: str,
        formato_destino: str,
        extensao_padrao: str,
    ) -> Path | None:
        extensao_limpa = (
            extensao_padrao
            if extensao_padrao.startswith(".")
            else f".{extensao_padrao}"
        ).lower()

        caminho_escolhido = filedialog.asksaveasfilename(
            parent=self,
            title=titulo,
            initialdir=str(pasta_inicial),
            initialfile=nome_sugerido,
            defaultextension=extensao_limpa,
            filetypes=[(f"Arquivo {formato_destino}", (f"*{extensao_limpa}",))],
            confirmoverwrite=False,
        )
        if not caminho_escolhido:
            return None

        destino = Path(caminho_escolhido)
        if destino.suffix.lower() != extensao_limpa:
            destino = destino.with_suffix(extensao_limpa)
        return destino

    # =========================================================================
    # AÇÕES DE CONVERSÃO, COMPACTAÇÃO E EXTRAÇÃO
    # =========================================================================

    def converter_jpg(self):
        self.converter_imagem(
            self.conversao_jpg_para_png, "JPG", "PNG", ("*.jpg", "*.jpeg")
        )

    def converter_png(self):
        self.converter_imagem(self.conversao_png_para_jpg, "PNG", "JPG", ("*.png",))

    def converter_docx_pdf(self):
        if self._thread_operacao is not None and self._thread_operacao.is_alive():
            return

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
        destino = self._solicitar_destino_salvar(
            titulo="Salvar PDF como",
            pasta_inicial=origem.parent,
            nome_sugerido=f"{origem.stem}.pdf",
            formato_destino="PDF",
            extensao_padrao=".pdf",
        )
        if destino is None:
            self._definir_status("Operação cancelada.", "neutro")
            return

        self._executar_operacao(self.conversao_docx_para_pdf, (origem,), destino, "PDF")

    def converter_pdf_docx(self):
        if self._thread_operacao is not None and self._thread_operacao.is_alive():
            return

        self._definir_status("Selecionando documento PDF...", "neutro")
        arquivo = filedialog.askopenfilename(
            parent=self,
            title="Selecionar documento PDF",
            filetypes=[("Documento PDF", ("*.pdf",))],
        )
        if not arquivo:
            self._definir_status("Operação cancelada.", "neutro")
            return

        origem = Path(arquivo)
        destino = self._solicitar_destino_salvar(
            titulo="Salvar DOCX como",
            pasta_inicial=origem.parent,
            nome_sugerido=f"{origem.stem}.docx",
            formato_destino="DOCX",
            extensao_padrao=".docx",
        )
        if destino is None:
            self._definir_status("Operação cancelada.", "neutro")
            return

        self._executar_operacao(self.conversao_pdf_para_docx, (origem,), destino, "DOCX")

    def converter_imagem(
        self,
        operacao: OperacaoArquivo,
        formato_origem: str,
        formato_destino: str,
        extensoes_origem: tuple[str, ...],
    ):
        if self._thread_operacao is not None and self._thread_operacao.is_alive():
            return

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
        extensao_destino = f".{formato_destino.lower()}"
        destino = self._solicitar_destino_salvar(
            titulo=f"Salvar {formato_destino} como",
            pasta_inicial=origem.parent,
            nome_sugerido=f"{origem.stem}{extensao_destino}",
            formato_destino=formato_destino,
            extensao_padrao=extensao_destino,
        )
        if destino is None:
            self._definir_status("Operação cancelada.", "neutro")
            return

        self._executar_operacao(operacao, (origem,), destino, formato_destino)

    def converter_imagens_pdf(self):
        if self._thread_operacao is not None and self._thread_operacao.is_alive():
            return

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
        nome_pdf = (
            f"{origens[0].stem}.pdf" if len(origens) == 1 else "imagens_convertidas.pdf"
        )
        destino = self._solicitar_destino_salvar(
            titulo="Salvar PDF como",
            pasta_inicial=origens[0].parent,
            nome_sugerido=nome_pdf,
            formato_destino="PDF",
            extensao_padrao=".pdf",
        )
        if destino is None:
            self._definir_status("Operação cancelada.", "neutro")
            return

        self._executar_operacao(self.conversao_imagem_para_pdf, origens, destino, "PDF")

    def compactar_arquivos_zip(self):
        if self._thread_operacao is not None and self._thread_operacao.is_alive():
            return

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
        if self._thread_operacao is not None and self._thread_operacao.is_alive():
            return

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

    def descompactar_arquivo_zip(self):
        if self._thread_operacao is not None and self._thread_operacao.is_alive():
            return

        self._definir_status("Selecionando arquivo ZIP para extrair...", "neutro")
        arquivo = filedialog.askopenfilename(
            parent=self,
            title="Selecionar arquivo ZIP",
            filetypes=[("Arquivo ZIP", ("*.zip",))],
        )
        if not arquivo:
            self._definir_status("Operação cancelada.", "neutro")
            return

        origem = Path(arquivo)
        pasta_pai = filedialog.askdirectory(
            parent=self,
            title="Escolher pasta onde o conteúdo será extraído",
            initialdir=str(origem.parent),
            mustexist=True,
        )
        if not pasta_pai:
            self._definir_status("Operação cancelada.", "neutro")
            return

        dialogo_nome = ctk.CTkInputDialog(
            text=f"Nome da pasta de destino (será criada em {Path(pasta_pai).name}):",
            title="Nome da Pasta Extraída",
        )
        nome_pasta = dialogo_nome.get_input()
        if nome_pasta is None:
            self._definir_status("Operação cancelada.", "neutro")
            return

        nome_limpo = nome_pasta.strip() or origem.stem
        destino = Path(pasta_pai) / nome_limpo
        self._executar_operacao(self.descompactacao_zip, (origem,), destino, "EXTRAÇÃO")

    def _escolher_destino_e_compactar(
        self, origens: tuple[Path, ...], pasta_inicial: Path, nome_sugerido: str
    ):
        destino = self._solicitar_destino_salvar(
            titulo="Salvar arquivo ZIP como",
            pasta_inicial=pasta_inicial,
            nome_sugerido=nome_sugerido,
            formato_destino="ZIP",
            extensao_padrao=".zip",
        )
        if destino is None:
            self._definir_status("Operação cancelada.", "neutro")
            return

        self._executar_operacao(self.compactacao_zip, origens, destino, "ZIP")

    # =========================================================================
    # EXECUÇÃO ASSÍNCRONA COM THREADING E SUPORTE A CANCELAMENTO
    # =========================================================================

    def _executar_operacao(
        self,
        operacao: OperacaoArquivo,
        origens: tuple[Path, ...],
        destino: Path,
        formato_destino: str,
        *,
        sobrescrever: bool = False,
    ):
        if self._thread_operacao is not None and self._thread_operacao.is_alive():
            return

        if not sobrescrever and (destino.exists() or destino.is_symlink()):
            tipo_item = "uma pasta" if destino.is_dir() else "um arquivo"
            if not messagebox.askyesno(
                "Substituir destino",
                f"Já existe {tipo_item} com o nome '{destino.name}'. Deseja substituí-lo?",
                parent=self,
            ):
                self._definir_status("Operação cancelada pelo usuário.", "neutro")
                return
            sobrescrever = True

        cancelamento = CancelamentoOperacao()
        self._cancelamento_atual = cancelamento
        self._alternar_estado_ocupado(True)
        self._definir_status(
            f"Processando {destino.name}... Clique em Cancelar para interromper.",
            "processando",
        )

        def _worker():
            try:
                resultado = self.servico_operacao.executar(
                    operacao,
                    origens,
                    destino,
                    sobrescrever=sobrescrever,
                    cancelamento=cancelamento,
                )
            except DestinoExistenteError:
                self.after(
                    0,
                    lambda: self._tratar_conflito_tardio(
                        operacao, origens, destino, formato_destino
                    ),
                )
            except OperacaoCancelada:
                self.after(0, self._finalizar_cancelamento)
            except ValueError as erro:
                mensagem_erro = str(erro)
                self.after(0, lambda: self._finalizar_erro(mensagem_erro))
            except OSError:
                mensagem_os = (
                    f"Não foi possível salvar o resultado ({formato_destino}) no destino escolhido."
                )
                self.after(0, lambda: self._finalizar_erro(mensagem_os))
            else:
                self.after(
                    0,
                    lambda: self._finalizar_sucesso(
                        formato_destino, origens, resultado
                    ),
                )

        self._thread_operacao = Thread(target=_worker, daemon=True)
        self._thread_operacao.start()

    def _tratar_conflito_tardio(
        self,
        operacao: OperacaoArquivo,
        origens: tuple[Path, ...],
        destino: Path,
        formato_destino: str,
    ):
        self._limpar_estado_execucao()
        if messagebox.askyesno(
            "Substituir destino",
            f"Já existe um item chamado {destino.name}. Deseja substituí-lo?",
            parent=self,
        ):
            self._executar_operacao(
                operacao, origens, destino, formato_destino, sobrescrever=True
            )
        else:
            self._definir_status("Operação cancelada pelo usuário.", "neutro")

    def _finalizar_cancelamento(self):
        self._limpar_estado_execucao()
        self._definir_status("Operação cancelada pelo usuário.", "neutro")

    def _finalizar_erro(self, mensagem_erro: str):
        self._limpar_estado_execucao()
        self._definir_status(mensagem_erro, "erro")

    def _finalizar_sucesso(
        self, formato_destino: str, origens: tuple[Path, ...], resultado: Path
    ):
        self._limpar_estado_execucao()
        self._definir_status(f"{formato_destino} concluído em {resultado}", "sucesso")
        self._registrar_no_historico(formato_destino, origens, resultado)

    def _limpar_estado_execucao(self):
        self._cancelamento_atual = None
        self._thread_operacao = None
        self._alternar_estado_ocupado(False)