import csv
import os
import re
import threading
import uuid
from datetime import datetime
from functools import wraps

from flask import (Flask, jsonify, redirect, render_template, request,
                   session, url_for)

# ---------------------------------------------------------------- config
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "admin123")
SECRET_KEY = os.environ.get("SECRET_KEY", "crm-local-secret")
DATA_DIR = os.environ.get("DATA_DIR", "/data")
CSV_PATH = os.path.join(DATA_DIR, "contatos.csv")
TAGS_PATH = os.path.join(DATA_DIR, "tags.csv")

CAMPOS_CONTATO = ["id", "nome", "sobrenome", "email", "numero",
                  "tags", "observacoes", "data_adicao"]
CAMPOS_TAG = ["id", "nome", "cor"]

# Sistema de cores das tags (as definições visuais ficam no style.css, classes .c-<cor>)
PALETA = ["azul", "ciano", "ambar", "verde", "vermelho", "roxo", "teal", "cinza"]

app = Flask(__name__)
app.secret_key = SECRET_KEY
lock = threading.Lock()


# ---------------------------------------------------------------- CSV Helpers
def init_csv():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, "w", newline="", encoding="utf-8-sig") as f:
            csv.DictWriter(f, fieldnames=CAMPOS_CONTATO).writeheader()
            
    if not os.path.exists(TAGS_PATH):
        gravar_tags([])
    else:
        # migração: o formato antigo (id, nome, tipo) vira (id, nome, cor)
        with open(TAGS_PATH, newline="", encoding="utf-8-sig") as f:
            cabecalho = next(csv.reader(f), [])
        if cabecalho != CAMPOS_TAG:
            with open(TAGS_PATH, newline="", encoding="utf-8-sig") as f:
                antigas = list(csv.DictReader(f))
            novas = []
            for n, t in enumerate(antigas):
                cor = t.get("cor") if t.get("cor") in PALETA else PALETA[n % len(PALETA)]
                novas.append({"id": t["id"], "nome": t["nome"], "cor": cor})
            gravar_tags(novas)


def ler_contatos():
    init_csv()
    with open(CSV_PATH, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def gravar_contatos(linhas):
    tmp = CSV_PATH + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS_CONTATO)
        w.writeheader()
        w.writerows(linhas)
    os.replace(tmp, CSV_PATH)


def ler_tags():
    init_csv()
    with open(TAGS_PATH, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def gravar_tags(linhas):
    tmp = TAGS_PATH + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS_TAG)
        w.writeheader()
        w.writerows(linhas)
    os.replace(tmp, TAGS_PATH)


def espacos(valor):
    """Tira espaços das pontas, junta espaços repetidos (inclui tab, quebra de linha,
    espaço sem quebra e caracteres invisíveis) em um só."""
    valor = re.sub(r"[​‌‍⁠﻿]", "", str(valor or ""))
    return re.sub(r"\s+", " ", valor).strip()


def nome_tag(valor):
    """Nome limpo. Vírgula e ponto e vírgula saem, porque a vírgula separa as tags no CSV."""
    return espacos(re.sub(r"[,;]", " ", str(valor or "")))[:40]


def campo_limpo(chave, valor):
    """Normaliza um campo de contato."""
    if chave == "email":                       # e-mail não tem espaço nenhum
        return re.sub(r"\s+", "", espacos(valor)).lower()
    if chave == "observacoes":                 # mantém quebras de linha, limpa cada linha
        texto = re.sub(r"[​‌‍⁠﻿]", "", str(valor or ""))
        linhas = [re.sub(r"[ \t ]+", " ", l).strip()
                  for l in texto.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
        return "\n".join(linhas).strip()
    if chave == "tags":
        return ",".join(lista_tags(valor))
    return espacos(valor)                      # nome, sobrenome, numero


def lista_tags(valor):
    """Aceita 'a,b' ou ['a','b'] e devolve lista sem repetidas."""
    if isinstance(valor, (list, tuple)):
        itens = valor
    else:
        itens = str(valor or "").split(",")
    saida = []
    for i in itens:
        n = nome_tag(i)
        if n and n.lower() not in [s.lower() for s in saida]:
            saida.append(n)
    return saida


def limpar_contato(dados, parcial=False):
    """Normaliza os campos recebidos. parcial=True (PUT/PATCH) só exige nome se ele vier."""
    if not hasattr(dados, "get"):
        return None, "Corpo da requisição inválido"
    out = {}
    for c in ["nome", "sobrenome", "email", "numero", "observacoes", "tags"]:
        if c in dados:
            out[c] = campo_limpo(c, dados.get(c))
    if (not parcial or "nome" in out) and not out.get("nome"):
        return None, "Campo obrigatório: nome"
    return out, None


def limpar_dados_antigos():
    """Roda na subida: normaliza contatos já salvos (espaços sobrando etc.)."""
    contatos = ler_contatos()
    novos = [{**c, **{k: campo_limpo(k, c.get(k)) for k in
                      ["nome", "sobrenome", "email", "numero", "observacoes", "tags"]}}
             for c in contatos]
    if novos != contatos:
        gravar_contatos(novos)


# ---------------------------------------------------------------- auth
def logado():
    return session.get("ok") is True


def precisa_login(f):
    @wraps(f)
    def w(*a, **k):
        if not logado():
            return redirect(url_for("login"))
        return f(*a, **k)
    return w


# ---------------------------------------------------------------- Páginas
@app.route("/login", methods=["GET", "POST"])
def login():
    erro = None
    if request.method == "POST":
        if (request.form.get("usuario") == ADMIN_USER
                and request.form.get("senha") == ADMIN_PASS):
            session["ok"] = True
            return redirect(url_for("index"))
        erro = "Usuário ou senha incorretos."
    return render_template("login.html", erro=erro)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@precisa_login
def index():
    return render_template("index.html", paleta=PALETA)


# ---------------------------------------------------------------- API (Sem verificação de chave)
@app.get("/api/contatos")
def listar_contatos():
    itens = ler_contatos()
    q = espacos(request.args.get("q")).lower()

    if q:
        itens = [i for i in itens if q in " ".join(i.values()).lower()]

    return jsonify(itens)


@app.get("/api/contatos/<cid>")
def obter_contato(cid):
    for i in ler_contatos():
        if i["id"] == cid:
            return jsonify(i)
    return jsonify(erro="não encontrado"), 404


@app.post("/api/contatos")
def criar_contato():
    dados, erro = limpar_contato(request.get_json(silent=True) or request.form)
    if erro:
        return jsonify(erro=erro), 400
    novo = {c: "" for c in CAMPOS_CONTATO}
    novo.update(dados)
    novo["id"] = uuid.uuid4().hex[:8]
    novo["data_adicao"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with lock:
        linhas = ler_contatos()
        linhas.append(novo)
        gravar_contatos(linhas)
    return jsonify(novo), 201


@app.route("/api/contatos/<cid>", methods=["PUT", "PATCH"])
def atualizar_contato(cid):
    dados, erro = limpar_contato(request.get_json(silent=True) or request.form, parcial=True)
    if erro:
        return jsonify(erro=erro), 400
    with lock:
        linhas = ler_contatos()
        for i in linhas:
            if i["id"] == cid:
                i.update(dados)
                gravar_contatos(linhas)
                return jsonify(i)
    return jsonify(erro="não encontrado"), 404


@app.delete("/api/contatos/<cid>")
def apagar_contato(cid):
    with lock:
        linhas = ler_contatos()
        novas = [i for i in linhas if i["id"] != cid]
        if len(novas) == len(linhas):
            return jsonify(erro="não encontrado"), 404
        gravar_contatos(novas)
    return jsonify(ok=True)


# ---------------------------------------------------------------- API de Tags
@app.get("/api/tags")
def listar_tags():
    contatos = ler_contatos()
    tags = ler_tags()
    for t in tags:
        t["contatos"] = sum(
            1 for c in contatos
            if t["nome"].lower() in [x.lower() for x in lista_tags(c.get("tags"))])
    return jsonify(tags)


@app.post("/api/tags")
def criar_tag():
    payload = request.get_json(silent=True) or request.form
    nome = nome_tag(payload.get("nome"))
    cor = str(payload.get("cor") or "").strip().lower()

    if not nome:
        return jsonify(erro="Nome obrigatório"), 400
    if cor and cor not in PALETA:
        return jsonify(erro="cor deve ser: " + ", ".join(PALETA)), 400

    with lock:
        tags = ler_tags()
        if any(t["nome"].lower() == nome.lower() for t in tags):
            return jsonify(erro="Tag já existe"), 400

        nova = {"id": "t" + uuid.uuid4().hex[:6], "nome": nome,
                "cor": cor or PALETA[len(tags) % len(PALETA)]}
        tags.append(nova)
        gravar_tags(tags)

    return jsonify(nova), 201


@app.route("/api/tags/<tid>", methods=["PUT", "PATCH"])
def alterar_tag(tid):
    """Troca a cor da tag."""
    payload = request.get_json(silent=True) or request.form
    cor = str(payload.get("cor") or "").strip().lower()
    if cor not in PALETA:
        return jsonify(erro="cor deve ser: " + ", ".join(PALETA)), 400
    with lock:
        tags = ler_tags()
        for t in tags:
            if t["id"] == tid:
                t["cor"] = cor
                gravar_tags(tags)
                return jsonify(t)
    return jsonify(erro="não encontrada"), 404


@app.delete("/api/tags/<tid>")
def apagar_tag(tid):
    """Apaga a tag e tira ela de todos os contatos que a usavam."""
    with lock:
        tags = ler_tags()
        alvo = next((t for t in tags if t["id"] == tid), None)
        if not alvo:
            return jsonify(erro="não encontrada"), 404
        contatos = ler_contatos()
        for c in contatos:
            c["tags"] = ",".join(
                n for n in lista_tags(c.get("tags"))
                if n.lower() != alvo["nome"].lower())
        gravar_contatos(contatos)
        gravar_tags([t for t in tags if t["id"] != tid])
    return jsonify(ok=True)


@app.get("/api/export.csv")
def exportar():
    init_csv()
    with open(CSV_PATH, encoding="utf-8-sig") as f:
        conteudo = f.read()
    return app.response_class(
        conteudo, mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=contatos.csv"})


init_csv()  # cria/migra os arquivos também quando rodando via gunicorn
limpar_dados_antigos()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)