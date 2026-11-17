# scrap
Sistema de Conversão e Compactação de Arquivos em Python
# ⚡ SCRAP — Sistema de Conversão e Compressão de Arquivos

O **SCRAP** (*File Studio & Converter*) é uma aplicação desktop em Python com interface gráfica em **CustomTkinter**. Reúne conversão e compressão de imagens, compactação e extração de ZIP, conversão entre DOCX e PDF e utilitários de PDF. O histórico local usa **SQLite** e permite recuperar arquivos por até **30 dias**.

---

## ✨ Funcionalidades Principais

### 🔄 1. Conversão de Arquivos
- **JPG → PNG:** Converte imagens JPEG para o formato PNG sem perdas (*lossless*), corrigindo automaticamente a orientação com base nos metadados EXIF.
- **PNG → JPG:** Converte imagens PNG para JPEG aplicando automaticamente preenchimento em fundo branco nas áreas de transparência (canal Alfa).
- **Imagens → PDF:** Agrupa imagens (`.jpg`, `.jpeg`, `.png`) em um PDF, com uma página por imagem. Ao selecionar várias imagens, é possível conferir e ajustar a ordem antes de salvar.
- **DOCX → PDF:** Usa o **LibreOffice** em modo *headless* quando disponível. O modo alternativo usa `python-docx` e `fpdf2` para converter texto e tabelas simples. Nesse modo, as imagens são omitidas e o layout pode mudar.
- **PDF → DOCX:** Valida o PDF com `pypdf` e gera um documento editável com `pdf2docx`. A conversão requer texto selecionável, e a preservação de imagens, tabelas e formatação depende do layout do PDF.

### 📦 2. Compressão & Pacotes ZIP
- **Comprimir Tamanho de Imagem (JPG / PNG):** Regrava JPEGs em modo progressivo e otimiza PNGs, reduzindo a paleta quando aplicável e preservando a transparência. A interface mostra o tamanho antes e depois. O ganho depende do arquivo, e a saída pode ficar maior quando a imagem já é compacta.
- **Compactar Arquivos em ZIP:** Agrupa múltiplos arquivos avulsos em um único pacote `.zip` comprimido (`ZIP_DEFLATED`).
- **Compactar Pasta em ZIP:** Comprime diretórios inteiros recursivamente, preservando toda a árvore de subpastas (incluindo pastas vazias) e bloqueando tentativas acidentais de salvar o `.zip` dentro da própria pasta de origem.
- **Extrair Arquivo ZIP:** Descompacta pacotes `.zip` em uma pasta escolhida pelo usuário com proteção ativa contra ataques de *Path Traversal / Zip Slip*.

### 📄 3. Utilitários de PDF
- **Mesclar PDFs:** Une dois ou mais PDFs em um só documento. A janela de ordenação permite mover os arquivos com **Subir** e **Descer** antes de salvar.
- **Dividir PDF em Páginas:** Salva cada página como um PDF separado na pasta escolhida (`documento-pagina-001.pdf`, `documento-pagina-002.pdf`, etc.).

### 🕒 4. Histórico Local (SQLite — Retenção de 30 Dias)
- **Persistência Completa (`BLOB`):** O banco local `db/historico_scrap.db` guarda os arquivos gerados. Para divisões de PDF, guarda um ZIP com as páginas separadas. Para extrações, guarda o ZIP de entrada.
- **Recuperação Rápida:** Clique em **Recuperar** e escolha o nome e o local de saída. Nos registros antigos de PDF dividido, o SCRAP refaz a divisão a partir do PDF armazenado e entrega as páginas em ZIP.
- **Expurgo Automático de 30 Dias:** O SCRAP remove registros com mais de 30 dias ao iniciar ou acessar o histórico.
- **Gestão de Espaço com `VACUUM`:** A interface mostra a soma dos tamanhos dos arquivos armazenados. É possível excluir um registro ou limpar o histórico. O SQLite executa `VACUUM` para liberar espaço após essas exclusões.

### 🛡️ 5. Segurança Transacional e Execução Assíncrona
- O **`ServicoOperacao`** gera o resultado em um diretório temporário (`TemporaryDirectory`) antes de movê-lo para o destino escolhido. Quando o destino já existe, a interface pede confirmação.
- A **execução em segundo plano** (`threading.Thread`) abrange conversões, compressões e utilitários de PDF. A barra animada indica que há trabalho em andamento, e o botão **Cancelar** permite solicitar a interrupção antes de gravar o resultado no destino.

---

## 🏗️ Arquitetura e Estrutura do Projeto

O projeto separa a **interface**, as **regras de negócio** e a **persistência**. O `main.py` instancia as dependências da janela. As operações herdam de `OperacaoArquivo`, e o `ServicoOperacao` chama o método `executar` da operação recebida, usando polimorfismo.

```text
scrap/
├── main.py                           # Ponto de entrada e injeção de dependências
├── requirement.txt                   # Dependências Python do projeto
├── README.md                         # Documentação do sistema
├── .gitignore                        # Regras para ignorar arquivos locais
├── interface/                        # Camada de Apresentação (UI em CustomTkinter)
│   ├── janela_principal.py           # Dashboard principal, cards, threads e diálogos
│   ├── icones.py                     # Gerador e carregador automático de ícones PNG (Light/Dark)
│   └── icons/                        # Ícones PNG usados pela interface
├── servicos/                         # Camada de Aplicação e Persistência
│   ├── servico_operacao.py           # Execução das operações e publicação dos resultados
│   └── repositorio_historico.py      # Histórico, recuperação e retenção em SQLite
├── operacoes/                        # Camada de Domínio / Regras de Negócio
│   ├── operacao_arquivo.py           # Classe base abstrata (Contrato OperacaoArquivo)
│   ├── cancelamento.py               # Controle thread-safe de cancelamento (CancelamentoOperacao)
│   ├── conversao_imagem.py           # Conversão bidirecional JPG <-> PNG
│   ├── compressao_imagem.py          # Otimização de peso (KB/MB) para JPG e PNG
│   ├── conversao_pdf.py              # Conversão de 1 ou N imagens para PDF
│   ├── conversao_docx_pdf.py         # Conversão com LibreOffice ou modo alternativo em Python
│   ├── conversao_pdf_docx.py         # Validação com pypdf e conversão com pdf2docx
│   ├── compactacao_zip.py            # Compactação de múltiplos arquivos e pastas recursivas
│   ├── descompactacao_zip.py         # Extração segura de pacotes ZIP (proteção Zip Slip)
│   └── utilitarios_pdf.py            # Mesclagem e divisão de páginas PDF
├── db/                               # Pasta criada ao iniciar o SCRAP
│   └── historico_scrap.db             # Banco SQLite local, ignorado pelo Git
└── sandbox/                          # Pasta local de amostras para testes manuais, ignorada pelo Git
```

---

## 📋 Pré-requisitos

- **Python:** recomenda-se **3.11** ou superior. O projeto foi testado com Python 3.14 no macOS.
- **Tkinter:** pacote gráfico padrão do Python.
  - *No Windows e macOS:* confirme que a sua instalação inclui o Tkinter com `python -m tkinter`.
  - *No Linux (Ubuntu/Debian):* caso não esteja instalado, instale com `sudo apt-get install -y python3-tk`.
- **LibreOffice (Opcional):** recomendado para manter imagens e formatação em `DOCX → PDF`. Quando o SCRAP não encontra o LibreOffice, usa o modo alternativo em Python.

---

## 🚀 Passo a Passo para Executar o Sistema

### 1. Clonar o repositório
```bash
git clone https://github.com/Mikaziel/scrap.git
cd scrap
```

### 2. Criar e ativar um ambiente virtual (Recomendado)

**No Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**No Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Instalar as dependências do projeto
Com o ambiente virtual ativo, instale as dependências listadas em `requirement.txt`.

```bash
python -m pip install -r requirement.txt
```

*Dependências em `requirement.txt`*
```text
customtkinter==6.0.0
Pillow==12.3.0
python-docx
fpdf2
pdf2docx
pypdf
```

### 4. (Opcional — Linux / DevContainer) Instalar o LibreOffice Writer
No Ubuntu ou Debian, inclusive em um contêiner configurado localmente, use este comando para instalar o LibreOffice Writer.

```bash
sudo apt-get update && sudo apt-get install -y --no-install-recommends libreoffice-writer fonts-dejavu
```

### 5. Iniciar a aplicação
Execute o arquivo principal na raiz do projeto:

```bash
python main.py
```

---

## 🖥️ Como Usar o Sistema

1. **Escolha a Categoria na Barra Lateral:**
   - Clique em **Conversão**, **Compressão & ZIP**, **Utilitários PDF** ou **Histórico (30 dias)**.
2. **Selecione a Operação Desejada:**
   - Clique no botão do cartão correspondente. Ao converter várias imagens para PDF ou mesclar PDFs, ajuste a ordem com **Subir** e **Descer** e clique em **Continuar**.
3. **Escolha o Destino e Nomeie o Arquivo:**
   - Escolha onde salvar e mantenha o nome sugerido ou digite outro. Para dividir um PDF ou extrair um ZIP, escolha a pasta que vai receber os arquivos.
   - Quando já existe um arquivo ou uma pasta com o nome escolhido no destino, o SCRAP pede confirmação para substituir.
4. **Acompanhe ou Cancele a Execução:**
   - Durante o processamento, a barra inferior mostra uma animação e o botão **Cancelar**.
5. **Recupere Arquivos do Histórico:**
   - Na aba **Histórico (30 dias)**, use **Recuperar** para salvar novamente um arquivo. Em um registro de PDF dividido, o arquivo recuperado é um ZIP com os PDFs de cada página. A aba também permite excluir registros ou usar **Limpar Histórico**.

---

## 🧪 Executando os Testes Automatizados

A validação das operações é feita pela interface com amostras locais na pasta `sandbox/`. Para testar recuperação, exclusão ou expiração de registros, use um banco SQLite descartável.

Para verificar as dependências e a importação do aplicativo pelo terminal, execute estes comandos na raiz do projeto.

```bash
python -m pip check
python -c "import main"
```

---

## 🔧 Como Adicionar Novas Operações no Futuro

Graças ao padrão *Strategy* utilizado no projeto, adicionar um novo conversor requer apenas 3 passos simples:

1. **Criar a classe da operação em `operacoes/`:**
   Herdar de `OperacaoArquivo` e implementar o método `executar(self, origens: tuple[Path, ...], destino: Path, *, cancelamento: CancelamentoOperacao | None = None) -> None`.
2. **Registrar o Card na `JanelaPrincipal` (`interface/janela_principal.py`):**
   Adicionar uma nova tupla `(badge, titulo, descricao, texto_botao, comando)` na lista da seção correspondente.
3. **Injetar no `main.py`:**
   Passar a instância da nova operação ao inicializar `JanelaPrincipal(...)`.
