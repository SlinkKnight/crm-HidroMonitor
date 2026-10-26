# HidroMonitor • CRM

Sistema de CRM leve e integrado desenvolvido em Flask para gerenciamento de contatos, estruturado com um sistema dinâmico de **Tags** (divididas entre perfis e campanhas) e identidade visual personalizada.

---

## 🚀 Como Executar

### Localmente (Python)
1. Instale as dependências:
   ```bash
   pip install Flask
   ```
2. Inicie a aplicação:
   ```bash
   python app.py
   ```
3. Acesse no navegador: `http://localhost:8080` (O login padrão de acesso à interface web é o usuário configurado no ambiente, por padrão `admin` / `admin123`).

### Via Docker Compose
1. Inicie o container:
   ```bash
   docker compose up -d
   ```
2. A aplicação estará disponível em `http://localhost:8080`. Os arquivos de dados (`contatos.csv` e `tags.csv`) ficarão salvos no diretório `./data`.

---

## 📡 Documentação da API (Sem Chave)

A API REST opera de forma pública sem a exigência de chaves de autenticação (`API_KEY` ou `X-API-Key`), facilitando integrações e automações diretas.

### 1. Contatos

#### Listar Contatos
Retorna a lista completa de contatos cadastrados. Suporta filtro opcional por termo de busca geral.
* **URL:** `/api/contatos`
* **Método:** `GET`
* **Parâmetros de Query (Opcional):**
  * `q` (string): Termo para buscar em qualquer campo (nome, e-mail, telefone, tags, etc.).
* **Exemplo de Requisição:**
  ```bash
  curl http://localhost:8080/api/contatos?q=Investidor
  ```

#### Obter Contato por ID
* **URL:** `/api/contatos/<id>`
* **Método:** `GET`

#### Criar Contato
Adiciona um novo contato à base de dados.
* **URL:** `/api/contatos`
* **Método:** `POST`
* **Content-Type:** `application/json`
* **Corpo da Requisição (Exemplo):**
  ```json
  {
    "nome": "Carlos",
    "sobrenome": "Silva",
    "email": "carlos@email.com",
    "numero": "(51) 99999-9999",
    "tags": "Investidor,Lançamento Q1",
    "observacoes": "Interessado na proposta comercial."
  }
  ```

#### Atualizar Contato
* **URL:** `/api/contatos/<id>`
* **Método:** `PUT` / `PATCH`
* **Content-Type:** `application/json`
* **Corpo da Requisição:** Campos que deseja atualizar (mesmo formato do `POST`).

#### Excluir Contato
* **URL:** `/api/contatos/<id>`
* **Método:** `DELETE`

---

### 2. Gerenciamento de Tags

#### Listar Tags
Retorna todas as tags cadastradas (separadas por tipo: `perfil` ou `campanha`).
* **URL:** `/api/tags`
* **Método:** `GET`

#### Criar Nova Tag
* **URL:** `/api/tags`
* **Método:** `POST`
* **Content-Type:** `application/json`
* **Corpo da Requisição:**
  ```json
  {
    "nome": "VIP",
    "tipo": "perfil"
  }
  ```
  *(Nota: O campo `tipo` aceita estritamente `perfil` ou `campanha`)*.

---

### 3. Utilitários

#### Exportar CSV
Baixa o arquivo CSV contendo todos os contatos do CRM.
* **URL:** `/api/export.csv`
* **Método:** `GET`