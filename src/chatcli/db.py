import sqlite3
from datetime import datetime

from chatcli import config


def conectar():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    criar_tabelas(conn)
    return conn


def criar_tabelas(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS conversas (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo    TEXT NOT NULL,
            criada_em TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS mensagens (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            conversa_id    INTEGER NOT NULL REFERENCES conversas(id),
            role           TEXT NOT NULL CHECK (role IN ('user', 'model')),
            texto          TEXT NOT NULL,
            modelo         TEXT,
            tokens_entrada INTEGER,
            tokens_saida   INTEGER,
            criada_em      TEXT NOT NULL
        );
    """)


def _agora():
    return datetime.now().isoformat(timespec="seconds")


def nova_conversa(conn, titulo):
    with conn:
        cur = conn.execute(
            "INSERT INTO conversas (titulo, criada_em) VALUES (?, ?)",
            (titulo, _agora()),
        )
    return cur.lastrowid


def salvar_mensagem(conn, conversa_id, role, texto,
                    modelo=None, tokens_entrada=None, tokens_saida=None):
    with conn:
        conn.execute(
            """INSERT INTO mensagens
               (conversa_id, role, texto, modelo, tokens_entrada, tokens_saida, criada_em)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (conversa_id, role, texto, modelo, tokens_entrada, tokens_saida, _agora()),
        )


def listar_conversas(conn, limite=20):
    return conn.execute(
        """SELECT c.id, c.titulo, c.criada_em, COUNT(m.id) AS total_mensagens
           FROM conversas c
           LEFT JOIN mensagens m ON m.conversa_id = c.id
           GROUP BY c.id
           ORDER BY c.id DESC
           LIMIT ?""",
        (limite,),
    ).fetchall()


def carregar_historico(conn, conversa_id):
    linhas = conn.execute(
        "SELECT role, texto FROM mensagens WHERE conversa_id = ? ORDER BY id",
        (conversa_id,),
    ).fetchall()
    return [{"role": l["role"], "parts": [{"text": l["texto"]}]} for l in linhas]