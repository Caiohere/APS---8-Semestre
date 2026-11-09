# test_api.py - testes simples do web service (rodar com: python test_api.py)
import os
import unittest

import banco

banco.CAMINHO_BANCO = os.path.join(os.path.dirname(__file__), "teste.db")
import app as servidor  # noqa: E402


class TesteApi(unittest.TestCase):

    def setUp(self):
        if os.path.exists(banco.CAMINHO_BANCO):
            os.remove(banco.CAMINHO_BANCO)
        banco.criar_tabelas()
        self.cliente = servidor.app.test_client()

    def tearDown(self):
        if os.path.exists(banco.CAMINHO_BANCO):
            os.remove(banco.CAMINHO_BANCO)

    def test_listar_residuos(self):
        resp = self.cliente.get("/api/residuos")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.get_json()), 6)

    def test_cadastrar_residuo_valido(self):
        resp = self.cliente.post("/api/residuos", json={
            "tipo": "Vidro", "quantidade_kg": 10, "destino": "Reciclagem", "data": "2026-11-01"})
        self.assertEqual(resp.status_code, 201)

    def test_cadastrar_residuo_invalido(self):
        resp = self.cliente.post("/api/residuos", json={
            "tipo": "Vidro", "quantidade_kg": -5, "destino": "Reciclagem", "data": "2026-11-01"})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("erro", resp.get_json())

    def test_residuo_inexistente(self):
        self.assertEqual(self.cliente.get("/api/residuos/999").status_code, 404)

    def test_consumo_duplicado(self):
        resp = self.cliente.post("/api/consumos", json={
            "recurso": "Agua", "quantidade": 20, "mes": "2026-10"})
        self.assertEqual(resp.status_code, 409)

    def test_nao_exclui_fornecedor_com_residuo(self):
        self.assertEqual(self.cliente.delete("/api/fornecedores/1").status_code, 409)

    def test_filtrar_por_tipo(self):
        dados = self.cliente.get("/api/residuos?tipo=Papel").get_json()
        self.assertEqual(len(dados), 2)
        self.assertTrue(all(r["tipo"] == "Papel" for r in dados))

    def test_alterar_e_excluir_residuo(self):
        novo = {"tipo": "Metal", "quantidade_kg": 7.5, "destino": "Reuso", "data": "2026-10-20"}
        self.assertEqual(self.cliente.put("/api/residuos/1", json=novo).status_code, 200)
        self.assertEqual(self.cliente.get("/api/residuos/1").get_json()["tipo"], "Metal")
        self.assertEqual(self.cliente.delete("/api/residuos/1").status_code, 200)
        self.assertEqual(self.cliente.delete("/api/residuos/1").status_code, 404)
        self.assertEqual(self.cliente.put("/api/residuos/1", json=novo).status_code, 404)

    def test_dados_invalidos(self):
        base = {"tipo": "Papel", "quantidade_kg": 1, "destino": "Reciclagem", "data": "2026-10-20"}
        for campo, valor in (("tipo", "Areia"), ("destino", "Rio"), ("quantidade_kg", "abc"),
                             ("data", "20/10/2026")):
            dados = dict(base, **{campo: valor})
            self.assertEqual(self.cliente.post("/api/residuos", json=dados).status_code, 400, campo)
        resp = self.cliente.post("/api/residuos", json=dict(base, fornecedor_id=99))
        self.assertEqual(resp.status_code, 400)
        resp = self.cliente.post("/api/residuos", data="nao e json", content_type="text/plain")
        self.assertEqual(resp.status_code, 400)
        resp = self.cliente.post("/api/fornecedores", json={"nome": "X"})
        self.assertEqual(resp.status_code, 400)
        resp = self.cliente.post("/api/consumos", json={"recurso": "Gas", "quantidade": 1, "mes": "2026-11"})
        self.assertEqual(resp.status_code, 400)

    def test_consumo_e_fornecedor_novos(self):
        resp = self.cliente.post("/api/consumos", json={"recurso": "Energia", "quantidade": 3500, "mes": "2026-11"})
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(self.cliente.delete("/api/consumos/%d" % resp.get_json()["id"]).status_code, 200)
        resp = self.cliente.post("/api/fornecedores", json={
            "nome": "Nova", "cnpj": "1", "tipo": "Coleta", "certificado_iso14001": True})
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(self.cliente.delete("/api/fornecedores/%d" % resp.get_json()["id"]).status_code, 200)

    def test_exportar_csv(self):
        resp = self.cliente.get("/api/relatorios/residuos.csv")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/csv", resp.content_type)
        self.assertEqual(len(resp.data.decode().strip().splitlines()), 7)

    def test_rota_inexistente(self):
        resp = self.cliente.get("/api/nao-existe")
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.get_json()["erro"], "Recurso nao encontrado")

    def test_relatorio(self):
        dados = self.cliente.get("/api/relatorios/resumo").get_json()
        self.assertEqual(dados["total_residuos_kg"], 610.5)
        self.assertEqual(dados["fornecedores_certificados"], 2)


if __name__ == "__main__":
    unittest.main()
