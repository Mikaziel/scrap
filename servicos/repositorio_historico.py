import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from servicos.servico_operacao import DestinoExistenteError

DIAS_RETENCAO = 30
CAMINHO_BANCO_PADRAO = Path(__file__).resolve().parent.parent / "historico_scrap.db"


@dataclass(frozen=True)
class RegistroHistorico:
    id: int
    operacao: str
    resumo_origem: str
    nome_arquivo: str
    destino_original: str
    criado_em: str
    tamanho_bytes: int

    @property
    def tamanho_formatado(self) -> str:
        return RepositorioHistorico.formatar_tamanho(self.tamanho_bytes)


class RepositorioHistorico:
    def __init__(
        self,
        caminho_banco: Path = CAMINHO_BANCO_PADRAO,
        dias_retencao: int = DIAS_RETENCAO,
    ):
        self.caminho_banco = Path(caminho_banco)
        self.dias_retencao = dias_retencao
        self._inicializar_banco()
        self.limpar_expirados()

    def _conectar(self) -> sqlite3.Connection:
        conexao = sqlite3.connect(self.caminho_banco)
        conexao.row_factory = sqlite3.Row
        return conexao

    def _inicializar_banco(self) -> None:
        self.caminho_banco.parent.mkdir(parents=True, exist_ok=True)
        with self._conectar() as conexao:
            conexao.execute(
                """
                CREATE TABLE IF NOT EXISTS historico_operacoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operacao TEXT NOT NULL,
                    resumo_origem TEXT NOT NULL,
                    nome_arquivo TEXT NOT NULL,
                    destino_original TEXT NOT NULL,
                    conteudo BLOB NOT NULL,
                    criado_em_utc TEXT NOT NULL,
                    criado_em_exibicao TEXT NOT NULL
                )
                """
            )

    @staticmethod
    def formatar_tamanho(num_bytes: int) -> str:
        tamanho = float(max(0, num_bytes))
        for unidade in ("B", "KB", "MB", "GB"):
            if tamanho < 1024.0 or unidade == "GB":
                if unidade == "B":
                    return f"{int(tamanho)} B"
                return f"{tamanho:.1f} {unidade}"
            tamanho /= 1024.0
        return "0 B"

    def limpar_expirados(self) -> int:
        limite = datetime.now(timezone.utc) - timedelta(days=self.dias_retencao)
        limite_iso = limite.isoformat()
        with self._conectar() as conexao:
            cursor = conexao.execute(
                "DELETE FROM historico_operacoes WHERE criado_em_utc < ?",
                (limite_iso,),
            )
            removidos = cursor.rowcount

        if removidos > 0:
            self._compactar_banco()
        return removidos

    def _compactar_banco(self) -> None:
        try:
            with sqlite3.connect(self.caminho_banco, isolation_level=None) as conexao:
                conexao.execute("VACUUM")
        except sqlite3.Error:
            pass

    def registrar(
        self,
        operacao: str,
        origens: tuple[Path, ...],
        arquivo_gerado: Path,
    ) -> int:
        self.limpar_expirados()
        conteudo = arquivo_gerado.read_bytes()
        agora_utc = datetime.now(timezone.utc)
        agora_local = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        resumo_origem = (
            origens[0].name
            if len(origens) == 1
            else f"{len(origens)} arquivos selecionados"
        )

        with self._conectar() as conexao:
            cursor = conexao.execute(
                """
                INSERT INTO historico_operacoes (
                    operacao,
                    resumo_origem,
                    nome_arquivo,
                    destino_original,
                    conteudo,
                    criado_em_utc,
                    criado_em_exibicao
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    operacao,
                    resumo_origem,
                    arquivo_gerado.name,
                    str(arquivo_gerado),
                    sqlite3.Binary(conteudo),
                    agora_utc.isoformat(),
                    agora_local,
                ),
            )
            return int(cursor.lastrowid)

    def listar(self) -> list[RegistroHistorico]:
        self.limpar_expirados()
        with self._conectar() as conexao:
            linhas = conexao.execute(
                """
                SELECT
                    id,
                    operacao,
                    resumo_origem,
                    nome_arquivo,
                    destino_original,
                    criado_em_exibicao,
                    LENGTH(conteudo) AS tamanho_bytes
                FROM historico_operacoes
                ORDER BY id DESC
                """
            ).fetchall()

        return [
            RegistroHistorico(
                id=linha["id"],
                operacao=linha["operacao"],
                resumo_origem=linha["resumo_origem"],
                nome_arquivo=linha["nome_arquivo"],
                destino_original=linha["destino_original"],
                criado_em=linha["criado_em_exibicao"],
                tamanho_bytes=int(linha["tamanho_bytes"] or 0),
            )
            for linha in linhas
        ]

    def excluir_registro(self, registro_id: int) -> bool:
        with self._conectar() as conexao:
            cursor = conexao.execute(
                "DELETE FROM historico_operacoes WHERE id = ?",
                (registro_id,),
            )
            excluiu = cursor.rowcount > 0

        if excluiu:
            self._compactar_banco()
        return excluiu

    def limpar_tudo(self) -> int:
        with self._conectar() as conexao:
            cursor = conexao.execute("DELETE FROM historico_operacoes")
            removidos = cursor.rowcount

        if removidos > 0:
            self._compactar_banco()
        return removidos

    def recuperar_arquivo(
        self,
        registro_id: int,
        destino: Path,
        *,
        sobrescrever: bool = False,
    ) -> Path:
        self.limpar_expirados()
        if destino.is_dir():
            raise ValueError("Escolha um nome de arquivo para salvar a recuperação.")

        if not sobrescrever and (destino.exists() or destino.is_symlink()):
            raise DestinoExistenteError(destino)

        with self._conectar() as conexao:
            linha = conexao.execute(
                "SELECT conteudo FROM historico_operacoes WHERE id = ?",
                (registro_id,),
            ).fetchone()

        if linha is None:
            raise ValueError(
                "Este registro não está mais disponível no banco (pode ter expirado o prazo de 30 dias)."
            )

        dados: bytes = bytes(linha["conteudo"])

        destino.parent.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(dir=destino.parent) as pasta_temporaria:
            arquivo_temporario = Path(pasta_temporaria) / destino.name
            arquivo_temporario.write_bytes(dados)

            if not sobrescrever:
                try:
                    with destino.open("xb"):
                        pass
                except FileExistsError as erro:
                    raise DestinoExistenteError(destino) from erro

            try:
                arquivo_temporario.replace(destino)
            except OSError:
                if not sobrescrever:
                    destino.unlink(missing_ok=True)
                raise

        return destino