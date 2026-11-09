# app.py - Web Service REST do sistema EcoGestao (APS 7/8 semestre)
# Tema: gestao ambiental de uma organizacao seguindo a ISO 14001
import csv
import io
from datetime import datetime

from flask import Flask, jsonify, request, Response, send_from_directory

import banco

app = Flask(__name__, static_folder="../cliente", static_url_path="")

TIPOS_RESIDUO = ["Papel", "Plastico", "Vidro", "Metal", "Organico", "Eletronico", "Rejeito"]
DESTINOS = ["Reciclagem", "Compostagem", "Aterro", "Incineracao", "Reuso"]
RECURSOS = ["Agua", "Energia"]


# ---------- funcoes auxiliares ----------

def erro(mensagem, status=400):
    return jsonify({"erro": mensagem}), status


def data_valida(texto, formato):
    try:
        datetime.strptime(texto, formato)
        return True
    except (ValueError, TypeError):
        return False


def numero_positivo(valor):
    try:
        return float(valor) > 0
    except (ValueError, TypeError):
        return False


@app.after_request
def liberar_cors(resposta):
    # permite que um cliente em outro endereco consuma o web service
    resposta.headers["Access-Control-Allow-Origin"] = "*"
    resposta.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resposta.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE"
    return resposta


@app.errorhandler(404)
def nao_encontrado(e):
    return erro("Recurso nao encontrado", 404)


@app.errorhandler(500)
def erro_interno(e):
    return erro("Erro interno no servidor", 500)


@app.route("/")
def inicio():
    return send_from_directory(app.static_folder, "index.html")


# ---------- fornecedores (stakeholders) ----------

@app.route("/api/fornecedores", methods=["GET"])
def listar_fornecedores():
    con = banco.conectar()
    linhas = con.execute("SELECT * FROM fornecedores ORDER BY nome").fetchall()
    con.close()
    return jsonify([dict(l) for l in linhas])


@app.route("/api/fornecedores", methods=["POST"])
def cadastrar_fornecedor():
    dados = request.get_json(silent=True)
    if not dados:
        return erro("Envie os dados em formato JSON")
    if not dados.get("nome") or not dados.get("cnpj") or not dados.get("tipo"):
        return erro("Os campos nome, cnpj e tipo sao obrigatorios")

    certificado = 1 if dados.get("certificado_iso14001") else 0
    con = banco.conectar()
    cur = con.execute(
        "INSERT INTO fornecedores (nome, cnpj, tipo, certificado_iso14001) VALUES (?, ?, ?, ?)",
        (dados["nome"], dados["cnpj"], dados["tipo"], certificado))
    con.commit()
    novo_id = cur.lastrowid
    con.close()
    return jsonify({"id": novo_id, "mensagem": "Fornecedor cadastrado"}), 201


@app.route("/api/fornecedores/<int:id>", methods=["DELETE"])
def excluir_fornecedor(id):
    con = banco.conectar()
    usado = con.execute("SELECT COUNT(*) FROM residuos WHERE fornecedor_id = ?", (id,)).fetchone()[0]
    if usado > 0:
        con.close()
        return erro("Fornecedor possui residuos vinculados e nao pode ser excluido", 409)
    cur = con.execute("DELETE FROM fornecedores WHERE id = ?", (id,))
    con.commit()
    con.close()
    if cur.rowcount == 0:
        return erro("Fornecedor nao encontrado", 404)
    return jsonify({"mensagem": "Fornecedor excluido"})


# ---------- residuos ----------

def validar_residuo(dados):
    if not dados:
        return "Envie os dados em formato JSON"
    if dados.get("tipo") not in TIPOS_RESIDUO:
        return "Tipo de residuo invalido. Use: " + ", ".join(TIPOS_RESIDUO)
    if dados.get("destino") not in DESTINOS:
        return "Destino invalido. Use: " + ", ".join(DESTINOS)
    if not numero_positivo(dados.get("quantidade_kg")):
        return "A quantidade deve ser um numero maior que zero"
    if not data_valida(dados.get("data"), "%Y-%m-%d"):
        return "Data invalida, use o formato AAAA-MM-DD"
    return None


@app.route("/api/residuos", methods=["GET"])
def listar_residuos():
    sql = """SELECT r.*, f.nome AS fornecedor FROM residuos r
             LEFT JOIN fornecedores f ON f.id = r.fornecedor_id"""
    parametros = []
    tipo = request.args.get("tipo")  # filtro opcional ?tipo=Papel
    if tipo:
        sql += " WHERE r.tipo = ?"
        parametros.append(tipo)
    sql += " ORDER BY r.data DESC"

    con = banco.conectar()
    linhas = con.execute(sql, parametros).fetchall()
    con.close()
    return jsonify([dict(l) for l in linhas])


@app.route("/api/residuos/<int:id>", methods=["GET"])
def buscar_residuo(id):
    con = banco.conectar()
    linha = con.execute("SELECT * FROM residuos WHERE id = ?", (id,)).fetchone()
    con.close()
    if linha is None:
        return erro("Residuo nao encontrado", 404)
    return jsonify(dict(linha))


@app.route("/api/residuos", methods=["POST"])
def cadastrar_residuo():
    dados = request.get_json(silent=True)
    problema = validar_residuo(dados)
    if problema:
        return erro(problema)

    con = banco.conectar()
    cur = con.execute(
        "INSERT INTO residuos (tipo, quantidade_kg, destino, data, fornecedor_id) VALUES (?, ?, ?, ?, ?)",
        (dados["tipo"], float(dados["quantidade_kg"]), dados["destino"], dados["data"],
         dados.get("fornecedor_id") or None))
    con.commit()
    novo_id = cur.lastrowid
    con.close()
    return jsonify({"id": novo_id, "mensagem": "Residuo cadastrado"}), 201


@app.route("/api/residuos/<int:id>", methods=["PUT"])
def alterar_residuo(id):
    dados = request.get_json(silent=True)
    problema = validar_residuo(dados)
    if problema:
        return erro(problema)

    con = banco.conectar()
    cur = con.execute(
        "UPDATE residuos SET tipo = ?, quantidade_kg = ?, destino = ?, data = ?, fornecedor_id = ? WHERE id = ?",
        (dados["tipo"], float(dados["quantidade_kg"]), dados["destino"], dados["data"],
         dados.get("fornecedor_id") or None, id))
    con.commit()
    con.close()
    if cur.rowcount == 0:
        return erro("Residuo nao encontrado", 404)
    return jsonify({"mensagem": "Residuo alterado"})


@app.route("/api/residuos/<int:id>", methods=["DELETE"])
def excluir_residuo(id):
    con = banco.conectar()
    cur = con.execute("DELETE FROM residuos WHERE id = ?", (id,))
    con.commit()
    con.close()
    if cur.rowcount == 0:
        return erro("Residuo nao encontrado", 404)
    return jsonify({"mensagem": "Residuo excluido"})


# ---------- consumo de agua e energia ----------

@app.route("/api/consumos", methods=["GET"])
def listar_consumos():
    con = banco.conectar()
    linhas = con.execute("SELECT * FROM consumos ORDER BY mes DESC, recurso").fetchall()
    con.close()
    return jsonify([dict(l) for l in linhas])


@app.route("/api/consumos", methods=["POST"])
def cadastrar_consumo():
    dados = request.get_json(silent=True)
    if not dados:
        return erro("Envie os dados em formato JSON")
    if dados.get("recurso") not in RECURSOS:
        return erro("Recurso invalido. Use: Agua ou Energia")
    if not numero_positivo(dados.get("quantidade")):
        return erro("A quantidade deve ser um numero maior que zero")
    if not data_valida(dados.get("mes"), "%Y-%m"):
        return erro("Mes invalido, use o formato AAAA-MM")

    con = banco.conectar()
    existe = con.execute("SELECT id FROM consumos WHERE recurso = ? AND mes = ?",
                         (dados["recurso"], dados["mes"])).fetchone()
    if existe:
        con.close()
        return erro("Ja existe consumo de " + dados["recurso"] + " para este mes", 409)
    cur = con.execute("INSERT INTO consumos (recurso, quantidade, mes) VALUES (?, ?, ?)",
                      (dados["recurso"], float(dados["quantidade"]), dados["mes"]))
    con.commit()
    novo_id = cur.lastrowid
    con.close()
    return jsonify({"id": novo_id, "mensagem": "Consumo cadastrado"}), 201


@app.route("/api/consumos/<int:id>", methods=["DELETE"])
def excluir_consumo(id):
    con = banco.conectar()
    cur = con.execute("DELETE FROM consumos WHERE id = ?", (id,))
    con.commit()
    con.close()
    if cur.rowcount == 0:
        return erro("Consumo nao encontrado", 404)
    return jsonify({"mensagem": "Consumo excluido"})


# ---------- relatorios ----------

@app.route("/api/relatorios/resumo", methods=["GET"])
def relatorio_resumo():
    con = banco.conectar()
    por_tipo = con.execute(
        "SELECT tipo, SUM(quantidade_kg) AS total FROM residuos GROUP BY tipo ORDER BY total DESC").fetchall()
    por_destino = con.execute(
        "SELECT destino, SUM(quantidade_kg) AS total FROM residuos GROUP BY destino").fetchall()
    total = con.execute("SELECT COALESCE(SUM(quantidade_kg), 0) FROM residuos").fetchone()[0]
    consumos = con.execute("SELECT recurso, mes, quantidade FROM consumos ORDER BY mes").fetchall()
    forn = con.execute(
        "SELECT COUNT(*), COALESCE(SUM(certificado_iso14001), 0) FROM fornecedores").fetchone()
    con.close()

    # residuos que nao foram para aterro/incineracao sao considerados reaproveitados
    reaproveitado = sum(d["total"] for d in por_destino
                        if d["destino"] in ("Reciclagem", "Compostagem", "Reuso"))
    percentual = round(reaproveitado / total * 100, 1) if total > 0 else 0

    # variacao do consumo entre o primeiro e o ultimo mes cadastrado
    variacao = {}
    for recurso in RECURSOS:
        valores = [c["quantidade"] for c in consumos if c["recurso"] == recurso]
        if len(valores) >= 2:
            variacao[recurso] = round((valores[-1] - valores[0]) / valores[0] * 100, 1)

    return jsonify({
        "total_residuos_kg": total,
        "percentual_reaproveitado": percentual,
        "residuos_por_tipo": [dict(l) for l in por_tipo],
        "residuos_por_destino": [dict(l) for l in por_destino],
        "variacao_consumo_percentual": variacao,
        "fornecedores_total": forn[0],
        "fornecedores_certificados": forn[1],
    })


@app.route("/api/relatorios/residuos.csv", methods=["GET"])
def exportar_csv():
    con = banco.conectar()
    linhas = con.execute("""SELECT r.id, r.data, r.tipo, r.quantidade_kg, r.destino, f.nome
                            FROM residuos r LEFT JOIN fornecedores f ON f.id = r.fornecedor_id
                            ORDER BY r.data""").fetchall()
    con.close()

    saida = io.StringIO()
    escritor = csv.writer(saida, delimiter=";")
    escritor.writerow(["ID", "Data", "Tipo", "Quantidade (kg)", "Destino", "Fornecedor"])
    for l in linhas:
        escritor.writerow([l[0], l[1], l[2], l[3], l[4], l[5] or ""])
    return Response(saida.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=residuos.csv"})


if __name__ == "__main__":
    banco.criar_tabelas()
    app.run(host="0.0.0.0", port=5000, debug=True)
