# banco.py - acesso ao banco de dados SQLite do EcoGestao
import sqlite3
import os

CAMINHO_BANCO = os.path.join(os.path.dirname(__file__), "ecogestao.db")


def conectar():
    conexao = sqlite3.connect(CAMINHO_BANCO)
    conexao.row_factory = sqlite3.Row  # permite acessar as colunas pelo nome
    return conexao


def criar_tabelas():
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fornecedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cnpj TEXT NOT NULL,
            tipo TEXT NOT NULL,
            certificado_iso14001 INTEGER NOT NULL DEFAULT 0
        )""")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS residuos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            quantidade_kg REAL NOT NULL,
            destino TEXT NOT NULL,
            data TEXT NOT NULL,
            fornecedor_id INTEGER,
            FOREIGN KEY (fornecedor_id) REFERENCES fornecedores (id)
        )""")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS consumos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recurso TEXT NOT NULL,
            quantidade REAL NOT NULL,
            mes TEXT NOT NULL
        )""")

    conexao.commit()

    # se o banco estiver vazio coloca alguns dados de exemplo
    total = cursor.execute("SELECT COUNT(*) FROM fornecedores").fetchone()[0]
    if total == 0:
        inserir_dados_exemplo(cursor)
        conexao.commit()

    conexao.close()


def inserir_dados_exemplo(cursor):
    fornecedores = [
        ("Recicla Mais Ltda", "12.345.678/0001-90", "Coleta de reciclaveis", 1),
        ("Verde Transportes", "98.765.432/0001-10", "Transporte de residuos", 0),
        ("EcoAterro SA", "11.222.333/0001-44", "Aterro sanitario", 1),
    ]
    cursor.executemany(
        "INSERT INTO fornecedores (nome, cnpj, tipo, certificado_iso14001) VALUES (?, ?, ?, ?)",
        fornecedores)

    residuos = [
        ("Papel", 120.5, "Reciclagem", "2026-09-05", 1),
        ("Plastico", 80.0, "Reciclagem", "2026-09-12", 1),
        ("Organico", 200.0, "Compostagem", "2026-09-20", None),
        ("Eletronico", 15.0, "Reciclagem", "2026-10-02", 1),
        ("Rejeito", 95.0, "Aterro", "2026-10-10", 3),
        ("Papel", 100.0, "Reciclagem", "2026-10-18", 1),
    ]
    cursor.executemany(
        "INSERT INTO residuos (tipo, quantidade_kg, destino, data, fornecedor_id) VALUES (?, ?, ?, ?, ?)",
        residuos)

    consumos = [
        ("Agua", 35.0, "2026-08"), ("Energia", 4200.0, "2026-08"),
        ("Agua", 32.5, "2026-09"), ("Energia", 3900.0, "2026-09"),
        ("Agua", 30.0, "2026-10"), ("Energia", 3650.0, "2026-10"),
    ]
    cursor.executemany(
        "INSERT INTO consumos (recurso, quantidade, mes) VALUES (?, ?, ?)", consumos)
