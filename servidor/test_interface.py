# test_interface.py - testes de ponta a ponta: abre o cliente no navegador e usa o sistema
# como um usuario faria. Precisa do Playwright (pip install playwright) e do Microsoft Edge
# ou Google Chrome instalado. Rodar com: python test_interface.py
import os
import threading
import unittest

from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright, expect

import banco

banco.CAMINHO_BANCO = os.path.join(os.path.dirname(__file__), "teste_interface.db")
import app as servidor  # noqa: E402

PORTA = 5001
URL = "http://localhost:%d/" % PORTA


class TesteInterface(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.web = make_server("localhost", PORTA, servidor.app)
        threading.Thread(target=cls.web.serve_forever, daemon=True).start()
        cls.pw = sync_playwright().start()
        try:
            cls.navegador = cls.pw.chromium.launch(channel="msedge")
        except Exception:
            cls.navegador = cls.pw.chromium.launch(channel="chrome")

    @classmethod
    def tearDownClass(cls):
        cls.navegador.close()
        cls.pw.stop()
        cls.web.shutdown()
        if os.path.exists(banco.CAMINHO_BANCO):
            os.remove(banco.CAMINHO_BANCO)

    def setUp(self):
        # cada teste comeca com o banco de exemplo novo
        if os.path.exists(banco.CAMINHO_BANCO):
            os.remove(banco.CAMINHO_BANCO)
        banco.criar_tabelas()
        self.pagina = self.navegador.new_page()
        self.pagina.on("dialog", lambda d: d.accept())  # confirma as exclusoes

    def tearDown(self):
        self.pagina.close()

    def abrir(self, tela):
        self.pagina.goto(URL + "#" + tela)

    def test_painel_mostra_indicadores(self):
        self.abrir("painel")
        expect(self.pagina.locator("#totalResiduos")).to_have_text("610.5")
        expect(self.pagina.locator("#percReaproveitado")).to_have_text("84.4%")
        expect(self.pagina.locator("#varAgua")).to_have_text("-14.3%")
        expect(self.pagina.locator("#varEnergia")).to_have_text("-13.1%")
        expect(self.pagina.locator("#fornCertificados")).to_have_text("2 de 3")
        expect(self.pagina.locator(".barra-linha")).to_have_count(5)

    def test_exportar_csv(self):
        self.abrir("painel")
        with self.pagina.expect_download() as d:
            self.pagina.click("#linkCsv")
        with open(d.value.path(), encoding="utf-8") as f:
            linhas = f.read().strip().splitlines()
        self.assertEqual(linhas[0], "ID;Data;Tipo;Quantidade (kg);Destino;Fornecedor")
        self.assertEqual(len(linhas), 7)

    def test_crud_residuo(self):
        p = self.pagina
        self.abrir("residuos")
        linhas = p.locator("#tabelaResiduos tr")
        expect(linhas).to_have_count(6)

        # cadastrar
        p.select_option("#tipo", "Vidro")
        p.fill("#quantidade", "12")
        p.select_option("#destino", "Reciclagem")
        p.fill("#data", "2026-11-05")
        p.select_option("#fornecedorResiduo", label="Recicla Mais Ltda")
        p.click("#formResiduo button[type=submit]")
        expect(p.locator("#mensagem")).to_have_text("Residuo cadastrado")
        expect(linhas).to_have_count(7)

        # filtrar
        p.select_option("#filtroTipo", "Vidro")
        expect(linhas).to_have_count(1)
        expect(linhas.first).to_contain_text("05/11/2026")
        expect(linhas.first).to_contain_text("Recicla Mais Ltda")

        # editar
        linhas.first.get_by_text("Editar").click()
        expect(p.locator("#quantidade")).to_have_value("12")
        p.fill("#quantidade", "20")
        p.click("#formResiduo button[type=submit]")
        expect(p.locator("#mensagem")).to_have_text("Residuo alterado")
        expect(linhas.first).to_contain_text("20")

        # excluir
        linhas.first.get_by_text("Excluir").click()
        expect(p.locator("#mensagem")).to_have_text("Residuo excluido")
        expect(linhas).to_have_count(0)

    def test_nome_com_apostrofo_e_html(self):
        p = self.pagina
        self.abrir("fornecedores")
        p.fill("#nomeForn", "D'Agua <b>Coleta</b>")
        p.fill("#cnpj", "1")
        p.fill("#tipoForn", "Coleta")
        p.click("#formFornecedor button[type=submit]")
        expect(p.locator("#tabelaFornecedores")).to_contain_text("D'Agua <b>Coleta</b>")

        self.abrir("residuos")
        p.reload()
        p.select_option("#fornecedorResiduo", label="D'Agua <b>Coleta</b>")
        p.fill("#quantidade", "3")
        p.fill("#data", "2026-11-06")
        p.click("#formResiduo button[type=submit]")
        expect(p.locator("#mensagem")).to_have_text("Residuo cadastrado")
        linha = p.locator("#tabelaResiduos tr").first
        linha.get_by_text("Editar").click()
        expect(p.locator("#quantidade")).to_have_value("3")

    def test_erro_de_validacao_aparece_na_tela(self):
        p = self.pagina
        self.abrir("residuos")
        p.fill("#data", "2026-11-05")
        p.click("#formResiduo button[type=submit]")  # sem quantidade
        expect(p.locator("#mensagem")).to_have_class("erro")
        expect(p.locator("#mensagem")).to_contain_text("quantidade")

    def test_consumo_e_duplicidade(self):
        p = self.pagina
        self.abrir("consumos")
        expect(p.locator("#tabelaConsumos tr")).to_have_count(6)
        p.select_option("#recurso", "Agua")
        p.fill("#qtdConsumo", "28")
        p.fill("#mes", "2026-11")
        p.click("#formConsumo button[type=submit]")
        expect(p.locator("#mensagem")).to_have_text("Consumo cadastrado")
        expect(p.locator("#tabelaConsumos tr")).to_have_count(7)
        expect(p.locator("#tabelaConsumos tr").first).to_contain_text("11/2026")

        # o mesmo mes de novo deve dar erro
        p.select_option("#recurso", "Agua")
        p.fill("#qtdConsumo", "30")
        p.fill("#mes", "2026-11")
        p.click("#formConsumo button[type=submit]")
        expect(p.locator("#mensagem")).to_contain_text("Ja existe consumo")
        expect(p.locator("#tabelaConsumos tr")).to_have_count(7)

    def test_fornecedores(self):
        p = self.pagina
        self.abrir("fornecedores")
        linhas = p.locator("#tabelaFornecedores tr")
        expect(linhas).to_have_count(3)

        p.fill("#nomeForn", "Coleta Azul")
        p.fill("#cnpj", "22.333.444/0001-55")
        p.fill("#tipoForn", "Coleta de oleo")
        p.check("#certificado")
        p.click("#formFornecedor button[type=submit]")
        expect(p.locator("#mensagem")).to_have_text("Fornecedor cadastrado")
        expect(linhas).to_have_count(4)
        nova = linhas.filter(has_text="Coleta Azul")
        expect(nova).to_contain_text("Sim")

        # fornecedor com residuos nao pode ser excluido
        linhas.filter(has_text="Recicla Mais Ltda").get_by_text("Excluir").click()
        expect(p.locator("#mensagem")).to_contain_text("nao pode ser excluido")
        expect(linhas).to_have_count(4)

        nova.get_by_text("Excluir").click()
        expect(p.locator("#mensagem")).to_have_text("Fornecedor excluido")
        expect(linhas).to_have_count(3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
