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

    def test_relatorio(self):
        dados = self.cliente.get("/api/relatorios/resumo").get_json()
        self.assertEqual(dados["total_residuos_kg"], 610.5)
        self.assertEqual(dados["fornecedores_certificados"], 2)


if __name__ == "__main__":
    unittest.main()
