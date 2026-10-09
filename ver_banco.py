import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "chat.db"

conn = sqlite3.connect(DB_PATH)

print("=== CONVERSAS ===")
for linha in conn.execute("SELECT id, titulo, criada_em FROM conversas"):
    print(linha)

print("\n=== MENSAGENS ===")
for linha in conn.execute(
    "SELECT id, conversa_id, role, substr(texto, 1, 50), modelo, tokens_entrada, tokens_saida "
    "FROM mensagens"
):
    print(linha)

conn.close()