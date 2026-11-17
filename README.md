# scrap
Sistema de Conversão e Compactação de Arquivos em Python
# ⚡ SCRAP — Sistema de Conversão e Compressão de Arquivos

O **SCRAP** (*File Studio & Converter*) é uma aplicação desktop moderna desenvolvida em Python com interface gráfica baseada em **CustomTkinter**. Seu objetivo é reunir, em um único ambiente rápido e seguro, ferramentas de conversão de formatos, compressão de arquivos/imagens, manipulação de documentos PDF e histórico persistente em banco de dados local (**SQLite**) com recuperação de arquivos por até **30 dias**.

---

## ✨ Funcionalidades Principais

### 🔄 1. Conversão de Arquivos
- **JPG → PNG:** Converte imagens JPEG para o formato PNG sem perdas (*lossless*), corrigindo automaticamente a orientação com base nos metadados EXIF.
- **PNG → JPG:** Converte imagens PNG para JPEG aplicando automaticamente preenchimento em fundo branco nas áreas de transparência (canal Alfa).
- **Imagens → PDF:** Agrupa uma ou múltiplas imagens (`.jpg`, `.jpeg`, `.png`) em um único documento PDF sequencial multipáginas.
- **DOCX → PDF:** Converte documentos do Microsoft Word (`.docx`) para PDF. Utiliza o **LibreOffice** em modo *headless* quando disponível para máxima fidelidade visual e conta com *fallback* 100% nativo em Python (`python-docx` + `fpdf2`) caso o LibreOffice não esteja instalado.
- **PDF → DOCX:** Converte arquivos PDF em documentos editáveis do Word (`.docx`), preservando estrutura, tabelas e textos por meio do `pdf2docx` (com *fallback* via `pypdf`).

### 📦 2. Compressão & Pacotes ZIP
- **Comprimir Tamanho de Imagem (JPG / PNG):** Reduz drasticamente o peso em KB/MB de imagens mantendo seu formato original (otimização progressiva para JPEG e quantização inteligente de paleta de 256 cores com transparência para PNG), exibindo a porcentagem de espaço economizado.
- **Compactar Arquivos em ZIP:** Agrupa múltiplos arquivos avulsos em um único pacote `.zip` comprimido (`ZIP_DEFLATED`).
- **Compactar Pasta em ZIP:** Comprime diretórios inteiros recursivamente, preservando toda a árvore de subpastas (incluindo pastas vazias) e bloqueando tentativas acidentais de salvar o `.zip` dentro da própria pasta de origem.
- **Extrair Arquivo ZIP:** Descompacta pacotes `.zip` em uma pasta escolhida pelo usuário com proteção ativa contra ataques de *Path Traversal / Zip Slip*.

### 📄 3. Utilitários de PDF
- **Mesclar PDFs:** Une 2 ou mais arquivos PDF em um único documento contínuo seguindo a ordem selecionada.
- **Dividir PDF em Páginas:** Extrai todas as páginas de um PDF como arquivos independentes (`documento-pagina-001.pdf`, `documento-pagina-002.pdf`, etc.).

### 🕒 4. Histórico Local (SQLite — Retenção de 30 Dias)
- **Persistência Completa (`BLOB`):** Todos os arquivos gerados ficam armazenados no banco local `historico_scrap.db`.
- **Recuperação Rápida:** Mesmo que o usuário apague o arquivo original do computador, basta clicar no botão **Recuperar** na aba de Histórico para salvá-lo novamente em qualquer pasta e com qualquer nome.
- **Expurgo Automático de 30 Dias:** Registros com mais de 30 dias são removidos automaticamente.
- **Gestão de Espaço com `VACUUM`:** Exibe o espaço total consumido no banco e permite excluir itens individualmente ou limpar todo o histórico otimizando o arquivo físico do SQLite no disco.

### 🛡️ 5. Segurança Transacional e Execução Assíncrona
- **Gravação Atômica:** Nenhuma operação escreve diretamente no arquivo final. O `ServicoOperacao` grava primeiro em um diretório temporário (`TemporaryDirectory`) e só substitui o destino ao concluir 100% da tarefa, evitando arquivos corrompidos em caso de falha ou cancelamento.
- **Multithreading e Cancelamento em Tempo Real:** Todas as conversões e compactações rodam em *background* (`threading.Thread`) com barra de progresso animada e botão **Cancelar** (`CancelamentoOperacao`), mantendo a interface fluida e responsiva.

---

## 🏗️ Arquitetura e Estrutura do Projeto

O projeto segue os princípios de **Clean Architecture / Separação de Responsabilidades**, com injeção de dependências configurada a partir do `main.py`:

```text
scrap/
├── main.py                           # Ponto de entrada e injeção de dependências
├── requirement.txt                   # Dependências Python do projeto
├── README.md                         # Documentação do sistema
├── .gitignore                        # Arquivos ignorados pelo Git (__pycache__, *.db, etc.)
├── .devcontainer/
│   └── devcontainer.json             # Configuração do ambiente containerizado (VS Code)
├── interface/                        # Camada de Apresentação (UI em CustomTkinter)
│   ├── janela_principal.py           # Dashboard principal, cards, threads e diálogos
│   ├── icones.py                     # Gerador e carregador automático de ícones PNG (Light/Dark)
│   └── icones/                       # Pasta gerada automaticamente com os assets visuais
├── servicos/                         # Camada de Aplicação e Persistência
│   ├── servico_operacao.py           # Orquestrador atômico (arquivos temporários e sobrescrita)
│   └── repositorio_historico.py      # Persistência SQLite (BLOB, expurgo de 30 dias e VACUUM)
├── operacoes/                        # Camada de Domínio / Regras de Negócio
│   ├── operacao_arquivo.py           # Classe base abstrata (Contrato OperacaoArquivo)
│   ├── cancelamento.py               # Controle thread-safe de cancelamento (CancelamentoOperacao)
│   ├── conversao_imagem.py           # Conversão bidirecional JPG <-> PNG
│   ├── compressao_imagem.py          # Otimização de peso (KB/MB) para JPG e PNG
│   ├── conversao_pdf.py              # Conversão de 1 ou N imagens para PDF
│   ├── conversao_docx_pdf.py         # Conversão de DOCX para PDF (LibreOffice + Fallback Python)
│   ├── conversao_pdf_docx.py         # Conversão de PDF para DOCX (pdf2docx + Fallback pypdf)
│   ├── compactacao_zip.py            # Compactação de múltiplos arquivos e pastas recursivas
│   ├── descompactacao_zip.py         # Extração segura de pacotes ZIP (proteção Zip Slip)
│   └── utilitarios_pdf.py            # Mesclagem e divisão de páginas PDF
├── sandbox/                          # Arquivos de exemplo para testes manuais
└── tests/                            # Suíte de testes automatizados (unittest)
    ├── __init__.py
    ├── test_operacoes.py
    └── test_servicos_e_historico.py
```

---

## 📋 Pré-requisitos

- **Python:** versão **3.10** ou superior (testado em Python 3.12+).
- **Tkinter:** pacote gráfico padrão do Python.
  - *No Windows e macOS:* já vem incluso no instalador oficial do Python.
  - *No Linux (Ubuntu/Debian):* caso não esteja instalado, instale com `sudo apt-get install -y python3-tk`.
- **LibreOffice (Opcional):** recomendado para conversão de `DOCX → PDF` com fidelidade idêntica ao documento original. Caso não esteja instalado, o SCRAP utiliza automaticamente seu conversor interno em Python.

---

## 🚀 Passo a Passo para Executar o Sistema

### 1. Clonar o repositório
```bash
git clone <URL_DO_SEU_REPOSITORIO>
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
Certifique-se de que o arquivo `requirement.txt` contém os pacotes necessários e execute:

```bash
pip install -r requirement.txt
```

*(Conteúdo esperado do `requirement.txt`:)*
```text
customtkinter
Pillow
python-docx
fpdf2
pdf2docx
pypdf
```

### 4. (Opcional — Linux / DevContainer) Instalar o LibreOffice Writer
Se estiver rodando em um container Linux ou Ubuntu/Debian e desejar habilitar o motor do LibreOffice para a conversão de `DOCX → PDF`:

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
   - Clique no botão de ação do cartão correspondente (ex: *Selecionar JPG*, *Escolher Pasta*, *Selecionar PDFs*).
3. **Escolha o Destino e Nomeie o Arquivo:**
   - Na janela de salvamento, navegue até a pasta desejada e mantenha o nome sugerido ou digite um novo nome para o arquivo de saída.
   - Se o arquivo já existir no destino, o sistema perguntará de forma segura se você deseja substituí-lo.
4. **Acompanhe ou Cancele a Execução:**
   - A barra inferior mostrará o indicador azul de processamento, a barra de progresso animada e o botão vermelho **Cancelar** caso queira interromper uma operação longa.
5. **Recupere Arquivos do Histórico:**
   - Acesse a aba **Histórico (30 dias)** para visualizar o tamanho de cada arquivo gerado, baixar novamente qualquer item clicando em **Recuperar**, excluir registros individuais ou clicar em **Limpar Histórico**.

---

## 🧪 Executando os Testes Automatizados

O projeto conta com uma suíte de testes unitários e de integração baseada no módulo nativo `unittest`, que valida conversões, compressão, proteção contra *Zip Slip*, cancelamento de operações e o ciclo de vida de 30 dias no banco SQLite usando diretórios temporários isolados.

Para rodar todos os testes, execute na raiz do projeto:

```bash
python -m unittest discover -s tests -v
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