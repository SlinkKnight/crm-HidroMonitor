import csv
import os
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

TAGS_PADRAO = [
    {"id": "t1", "nome": "Investidor", "tipo": "perfil"},
    {"id": "t2", "nome": "Cliente", "tipo": "perfil"},
    {"id": "t3", "nome": "Incorporadora/Administradora", "tipo": "perfil"},
    {"id": "t4", "nome": "Lançamento Q1", "tipo": "campanha"},
    {"id": "t5", "nome": "Outreach 2026", "tipo": "campanha"}
]

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
        with open(TAGS_PATH, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=["id", "nome", "tipo"])
            w.writeheader()
            w.writerows(TAGS_PADRAO)


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
        w = csv.DictWriter(f, fieldnames=["id", "nome", "tipo"])
        w.writeheader()
        w.writerows(linhas)
    os.replace(tmp, TAGS_PATH)


def limpar_contato(dados):
    out = {}
    for c in ["nome", "sobrenome", "email", "numero", "observacoes", "tags"]:
        if c in dados:
            out[c] = str(dados.get(c) or "").strip()
    if not out.get("nome"):
        return None, "Campo obrigatório: nome"
    return out, None


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
    return render_template("index.html")


# ---------------------------------------------------------------- API (Sem verificação de chave)
@app.get("/api/contatos")
def listar_contatos():
    itens = ler_contatos()
    q = (request.args.get("q") or "").lower()

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
    dados, erro = limpar_contato(request.get_json(silent=True) or request.form)
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
    return jsonify(ler_tags())


@app.post("/api/tags")
def criar_tag():
    payload = request.get_json(silent=True) or request.form
    nome = str(payload.get("nome") or "").strip()
    tipo = str(payload.get("tipo") or "").strip().lower()

    if not nome or tipo not in ["perfil", "campanha"]:
        return jsonify(erro="Nome obrigatório e tipo deve ser 'perfil' ou 'campanha'"), 400

    with lock:
        tags = ler_tags()
        if any(t["nome"].lower() == nome.lower() for t in tags):
            return jsonify(erro="Tag já existe"), 400

        nova = {"id": "t" + uuid.uuid4().hex[:6], "nome": nome, "tipo": tipo}
        tags.append(nova)
        gravar_tags(tags)

    return jsonify(nova), 201


@app.get("/api/export.csv")
def exportar():
    init_csv()
    with open(CSV_PATH, encoding="utf-8-sig") as f:
        conteudo = f.read()
    return app.response_class(
        conteudo, mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=contatos.csv"})


if __name__ == "__main__":
    init_csv()
    app.run(host="0.0.0.0", port=8080)