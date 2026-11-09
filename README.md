# EcoGestão – APS 7º/8º semestre Ciência da Computação (UNIP)

Tema: **Desenvolvimento de uma aplicação utilizando Web Services**, voltada para a gestão ambiental
de uma organização seguindo a ISO 14001.

O EcoGestão tem duas partes:

- **servidor/**: web service REST em Python + Flask + SQLite. Ele controla os resíduos, o consumo de água e energia e os fornecedores (stakeholders), e gera os relatórios.
- **cliente/**: aplicação web em HTML, CSS e JavaScript que consome o web service.

## Como executar

```bash
pip install -r requirements.txt
cd servidor
python app.py
```

Depois abra http://localhost:5000 no navegador.

Para rodar os testes:

```bash
cd servidor
python test_api.py
```

## Endpoints

| Método | URI | Descrição |
|---|---|---|
| GET | /api/residuos | Lista resíduos (filtro opcional `?tipo=Papel`) |
| GET | /api/residuos/{id} | Busca um resíduo |
| POST | /api/residuos | Cadastra resíduo |
| PUT | /api/residuos/{id} | Altera resíduo |
| DELETE | /api/residuos/{id} | Exclui resíduo |
| GET | /api/consumos | Lista consumos de água/energia |
| POST | /api/consumos | Cadastra consumo |
| DELETE | /api/consumos/{id} | Exclui consumo |
| GET | /api/fornecedores | Lista fornecedores |
| POST | /api/fornecedores | Cadastra fornecedor |
| DELETE | /api/fornecedores/{id} | Exclui fornecedor |
| GET | /api/relatorios/resumo | Indicadores ambientais |
| GET | /api/relatorios/residuos.csv | Exporta resíduos em CSV |

Exemplo de cadastro com cURL:

```bash
curl -X POST http://localhost:5000/api/residuos -H "Content-Type: application/json" -d "{\"tipo\":\"Vidro\",\"quantidade_kg\":12,\"destino\":\"Reciclagem\",\"data\":\"2026-11-05\"}"
```

## Trabalho escrito

O trabalho escrito (normas ABNT) está em `documentacao/`.
