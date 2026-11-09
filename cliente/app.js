// app.js - cliente que consome o web service do EcoGestao
// se a pagina foi aberta direto do arquivo usa o servidor local, senao usa o mesmo endereco
const API = location.protocol === "file:" ? "http://localhost:5000/api" : "/api";
document.getElementById("linkCsv").href = API + "/relatorios/residuos.csv";

// funcao generica para chamar o web service
async function chamarApi(caminho, metodo = "GET", corpo = null) {
    const opcoes = { method: metodo, headers: { "Content-Type": "application/json" } };
    if (corpo) opcoes.body = JSON.stringify(corpo);
    try {
        const resposta = await fetch(API + caminho, opcoes);
        const dados = await resposta.json();
        if (!resposta.ok) {
            mostrarMensagem(dados.erro || "Erro na requisição", true);
            return null;
        }
        return dados;
    } catch (e) {
        mostrarMensagem("Não foi possível conectar ao servidor. Ele está ligado?", true);
        return null;
    }
}

function mostrarMensagem(texto, ehErro = false) {
    const div = document.getElementById("mensagem");
    div.textContent = texto;
    div.className = ehErro ? "erro" : "sucesso";
    setTimeout(() => { div.textContent = ""; div.className = ""; }, 4000);
}

function mostrarTela(id) {
    document.querySelectorAll(".tela").forEach(t => t.style.display = "none");
    document.getElementById(id).style.display = "block";
    if (id === "painel") carregarPainel();
    if (id === "residuos") { carregarFornecedoresSelect(); carregarResiduos(); }
    if (id === "consumos") carregarConsumos();
    if (id === "fornecedores") carregarFornecedores();
}

// evita que textos digitados pelo usuario sejam interpretados como HTML
function escapar(texto) {
    const div = document.createElement("div");
    div.textContent = texto;
    return div.innerHTML;
}

function formatarData(data) {
    const p = data.split("-");
    return p.length === 3 ? `${p[2]}/${p[1]}/${p[0]}` : `${p[1]}/${p[0]}`;
}

// ---------- painel ----------
async function carregarPainel() {
    const r = await chamarApi("/relatorios/resumo");
    if (!r) return;
    document.getElementById("totalResiduos").textContent = r.total_residuos_kg.toFixed(1);
    document.getElementById("percReaproveitado").textContent = r.percentual_reaproveitado + "%";
    const v = r.variacao_consumo_percentual;
    document.getElementById("varAgua").textContent = v.Agua !== undefined ? v.Agua + "%" : "-";
    document.getElementById("varEnergia").textContent = v.Energia !== undefined ? v.Energia + "%" : "-";
    document.getElementById("fornCertificados").textContent =
        r.fornecedores_certificados + " de " + r.fornecedores_total;

    // grafico de barras simples feito com div
    const maior = Math.max(...r.residuos_por_tipo.map(x => x.total), 1);
    document.getElementById("grafico").innerHTML = r.residuos_por_tipo.map(x => `
        <div class="barra-linha">
            <span class="rotulo">${x.tipo}</span>
            <div class="barra" style="width:${x.total / maior * 70}%"></div>
            <span>${x.total.toFixed(1)}</span>
        </div>`).join("");
}

// ---------- residuos ----------
let residuosCarregados = [];

async function carregarResiduos() {
    const filtro = document.getElementById("filtroTipo").value;
    const lista = await chamarApi("/residuos" + (filtro ? "?tipo=" + filtro : ""));
    if (!lista) return;
    residuosCarregados = lista;
    document.getElementById("tabelaResiduos").innerHTML = lista.map(r => `
        <tr>
            <td>${formatarData(r.data)}</td><td>${r.tipo}</td><td>${r.quantidade_kg}</td>
            <td>${r.destino}</td><td>${escapar(r.fornecedor || "-")}</td>
            <td><button onclick="editarResiduo(${r.id})">Editar</button>
                <button onclick="excluir('/residuos/${r.id}', carregarResiduos)">Excluir</button></td>
        </tr>`).join("");
}

async function carregarFornecedoresSelect() {
    const lista = await chamarApi("/fornecedores");
    if (!lista) return;
    document.getElementById("fornecedorResiduo").innerHTML = '<option value="">Sem fornecedor</option>' +
        lista.map(f => `<option value="${f.id}">${escapar(f.nome)}</option>`).join("");
}

function editarResiduo(id) {
    const r = residuosCarregados.find(x => x.id === id);
    document.getElementById("residuoId").value = r.id;
    document.getElementById("tipo").value = r.tipo;
    document.getElementById("quantidade").value = r.quantidade_kg;
    document.getElementById("destino").value = r.destino;
    document.getElementById("data").value = r.data;
    document.getElementById("fornecedorResiduo").value = r.fornecedor_id || "";
}

document.getElementById("formResiduo").addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = document.getElementById("residuoId").value;
    const dados = {
        tipo: document.getElementById("tipo").value,
        quantidade_kg: document.getElementById("quantidade").value,
        destino: document.getElementById("destino").value,
        data: document.getElementById("data").value,
        fornecedor_id: document.getElementById("fornecedorResiduo").value || null
    };
    const r = id ? await chamarApi("/residuos/" + id, "PUT", dados)
                 : await chamarApi("/residuos", "POST", dados);
    if (r) {
        mostrarMensagem(r.mensagem);
        e.target.reset();
        document.getElementById("residuoId").value = "";
        carregarResiduos();
    }
});

// ---------- consumos ----------
async function carregarConsumos() {
    const lista = await chamarApi("/consumos");
    if (!lista) return;
    document.getElementById("tabelaConsumos").innerHTML = lista.map(c => `
        <tr>
            <td>${formatarData(c.mes)}</td><td>${c.recurso}</td>
            <td>${c.quantidade} ${c.recurso === "Agua" ? "m³" : "kWh"}</td>
            <td><button onclick="excluir('/consumos/${c.id}', carregarConsumos)">Excluir</button></td>
        </tr>`).join("");
}

document.getElementById("formConsumo").addEventListener("submit", async (e) => {
    e.preventDefault();
    const r = await chamarApi("/consumos", "POST", {
        recurso: document.getElementById("recurso").value,
        quantidade: document.getElementById("qtdConsumo").value,
        mes: document.getElementById("mes").value
    });
    if (r) { mostrarMensagem(r.mensagem); e.target.reset(); carregarConsumos(); }
});

// ---------- fornecedores ----------
async function carregarFornecedores() {
    const lista = await chamarApi("/fornecedores");
    if (!lista) return;
    document.getElementById("tabelaFornecedores").innerHTML = lista.map(f => `
        <tr>
            <td>${escapar(f.nome)}</td><td>${escapar(f.cnpj)}</td><td>${escapar(f.tipo)}</td>
            <td>${f.certificado_iso14001 ? "Sim" : "Não"}</td>
            <td><button onclick="excluir('/fornecedores/${f.id}', carregarFornecedores)">Excluir</button></td>
        </tr>`).join("");
}

document.getElementById("formFornecedor").addEventListener("submit", async (e) => {
    e.preventDefault();
    const r = await chamarApi("/fornecedores", "POST", {
        nome: document.getElementById("nomeForn").value,
        cnpj: document.getElementById("cnpj").value,
        tipo: document.getElementById("tipoForn").value,
        certificado_iso14001: document.getElementById("certificado").checked
    });
    if (r) { mostrarMensagem(r.mensagem); e.target.reset(); carregarFornecedores(); }
});

// exclusao generica usada pelas tres telas
async function excluir(caminho, recarregar) {
    if (!confirm("Deseja realmente excluir este registro?")) return;
    const r = await chamarApi(caminho, "DELETE");
    if (r) { mostrarMensagem(r.mensagem); recarregar(); }
}

// abre a tela indicada no endereco (ex: index.html#residuos) ou o painel
mostrarTela(location.hash.slice(1) || "painel");
