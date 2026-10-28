# HidroMonitor • CRM

Painel de contatos em Flask, com os dados guardados em arquivos CSV e empacotado em Docker para rodar no servidor local.

- [Subir o sistema](#subir-o-sistema)
- [Arquivos de dados](#arquivos-de-dados)
- [Tags](#tags)
- [Limpeza automática dos dados](#limpeza-automática-dos-dados)
- [Uso do painel](#uso-do-painel)
- [Marca e fonte](#marca-e-fonte)
- [API](#api)
- [Notas de mudanças](#notas-de-mudanças)
- [Segurança](#segurança)

---

## Subir o sistema

```bash
docker compose up -d --build
```

Acesse `http://IP-DO-SERVIDOR:8080`.

Login padrão: `admin` / `admin123`. A senha é em texto plano, definida no `docker-compose.yml`:

```yaml
environment:
  ADMIN_USER: admin
  ADMIN_PASS: admin123
  SECRET_KEY: crm-local-secret
volumes:
  - ./data:/data
```

Para atualizar arquivos do projeto, copie por cima e rode o comando acima de novo. Os dados em `./data` não são apagados.

---

## Arquivos de dados

Ficam na pasta `./data` do servidor, em UTF-8 com BOM (abrem direto no Excel).

**`contatos.csv`**

| Coluna | Conteúdo |
|---|---|
| `id` | 8 caracteres, gerado automaticamente |
| `nome`, `sobrenome` | texto |
| `email` | minúsculo, sem espaços |
| `numero` | texto, como foi enviado |
| `tags` | nomes das tags separados por vírgula, ex.: `Cliente,Black Friday` |
| `observacoes` | texto, pode ter quebras de linha |
| `data_adicao` | `AAAA-MM-DD HH:MM:SS`, gerada automaticamente |

**`tags.csv`**

| Coluna | Conteúdo |
|---|---|
| `id` | `t` + 6 caracteres |
| `nome` | até 40 caracteres, único (sem diferenciar maiúscula de minúscula) |
| `cor` | uma das 8 cores da paleta |

---

## Tags

Existe **uma lista única de tags**. Não há mais separação entre perfil e campanha. Use o nome para distinguir (ex.: `Investidor`, `Black Friday 2026`).

### Cores

Cada tag tem uma cor, escolhida ao criar e que pode ser trocada depois:

| Chave | Aparência |
|---|---|
| `azul` | azul profundo da marca |
| `ciano` | azul fluxo da marca |
| `ambar` | âmbar da marca |
| `verde` | verde |
| `vermelho` | vermelho |
| `roxo` | roxo |
| `teal` | azul-esverdeado |
| `cinza` | cinza (também usada quando a tag de um contato não existe no catálogo) |

Se a cor não for informada ao criar, o sistema usa a próxima da lista, em rodízio.

### Gerenciar tags (botão "Gerenciar Tags")

- **Criar:** nome + cor.
- **Trocar a cor:** clique em um dos círculos na linha da tag.
- **Excluir:** botão "Excluir" na linha da tag. A confirmação mostra de quantos contatos ela será removida. A exclusão apaga a tag do catálogo **e** de todos os contatos que a usavam. Não dá para desfazer.

### Regras

- Vírgula e ponto e vírgula são trocados por espaço no nome, porque a vírgula separa as tags dentro do CSV.
- Espaços repetidos ou nas pontas são removidos.
- Duas tags com o mesmo nome, mesmo com maiúsculas diferentes, não podem existir.
- **Atenção (API):** uma tag citada em um contato **não é criada automaticamente** no catálogo. Para ter cor e aparecer na lista de seleção do painel, crie antes com `POST /api/tags`. Tags que existem só no contato aparecem em cinza na tabela e somem do contato se ele for salvo pelo formulário do painel.

---

## Limpeza automática dos dados

Todo texto que entra pela **API ou pelo painel** passa pela mesma limpeza no servidor:

| Campo | O que é feito | Exemplo |
|---|---|---|
| `nome`, `sobrenome`, `numero` | tira espaços das pontas e junta espaços repetidos em um só | `"  Ana   Maria "` → `"Ana Maria"` |
| `email` | remove **todos** os espaços e põe em minúsculo | `" ANA @X.com "` → `"ana@x.com"` |
| `tags` | limpa cada nome, tira repetidas, ignora vazias | `"Cliente , cliente,  VIP "` → `"Cliente,VIP"` |
| `observacoes` | limpa cada linha, mantém as quebras de linha | `"  a  \n   b "` → `"a\nb"` |
| `q` (busca) | tira espaços das pontas e repetidos | `"  ana  "` → `"ana"` |

Também são removidos espaço sem quebra (`U+00A0`), tabulação e caracteres invisíveis (`U+200B`, `U+FEFF` etc.), que costumam vir de textos copiados.

**Dados antigos:** na subida do servidor, os contatos já salvos passam pela mesma limpeza, e o `contatos.csv` é reescrito só se algo mudar.

---

## Uso do painel

### Telefone

O campo **Número** formata enquanto você digita:

| Digitado | Resultado |
|---|---|
| `51999990000` (11 dígitos) | `(51) 99999-0000` |
| `5133334444` (10 dígitos) | `(51) 3333-4444` |
| `+5551999990000` | `+55 (51) 99999-0000` |
| `+` com outro país | só mantém os dígitos, sem formatar |

O `+55` só é reconhecido quando você digita o `+`, porque 55 também é DDD do Rio Grande do Sul. A formatação é do painel. Contatos criados pela API ficam como foram enviados e aparecem formatados na tela.

### Teclado (formulário de contato)

| Tecla | Ação |
|---|---|
| `Enter` | vai para o próximo campo |
| `Ctrl+Enter` | salva o contato (de qualquer campo, inclusive observações) |
| `Tab` / `Shift+Tab` | navega entre campos |
| `Espaço` | marca/desmarca a tag em foco |
| `Esc` | fecha a janela aberta |

Nas observações o `Enter` continua quebrando linha.

---

## Marca e fonte

O texto "HidroMonitor • CRM" usa a **XXII Geom Bold**. O arquivo da fonte não vem no projeto (é licenciada). Para ativar, copie-o para `static/fonts/` com um destes nomes e reconstrua o container:

`XXIIGeom-Bold.woff2` · `XXIIGeom-Bold.woff` · `XXIIGeom-Bold.otf` · `XXIIGeom-Bold.ttf`

Sem o arquivo, é usada a Poppins Bold, que já está em `static/fonts/`. Se a XXII Geom estiver instalada no computador de quem abre o painel, ela também é usada.

A logo é `static/logoHidromonitor.png`.

---

## API

- Base: `http://IP-DO-SERVIDOR:8080`
- **Sem chave e sem login.** Veja [Segurança](#segurança).
- Envie e receba **JSON** (`Content-Type: application/json`). Formulário (`application/x-www-form-urlencoded`) também é aceito.
- Erros voltam como `{"erro": "mensagem"}` com o status HTTP correspondente.
- Todos os textos recebem a [limpeza automática](#limpeza-automática-dos-dados).

### Contatos

Objeto retornado:

```json
{
  "id": "a1b2c3d4",
  "nome": "Maria",
  "sobrenome": "Silva",
  "email": "maria@x.com",
  "numero": "(51) 99999-0000",
  "tags": "Cliente,Black Friday 2026",
  "observacoes": "Indicação do João",
  "data_adicao": "2026-10-28 15:31:43"
}
```

> `tags` volta como **texto separado por vírgula**. Para enviar, aceita texto (`"A,B"`) ou lista (`["A","B"]`).

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/contatos` | Lista todos. Parâmetro opcional `?q=` busca em todos os campos, inclusive tags |
| `GET` | `/api/contatos/<id>` | Um contato (`404` se não existir) |
| `POST` | `/api/contatos` | Cria. `nome` é obrigatório. Retorna `201` com o contato |
| `PUT` ou `PATCH` | `/api/contatos/<id>` | Altera **só os campos enviados**. `nome`, se enviado, não pode ficar vazio |
| `DELETE` | `/api/contatos/<id>` | Remove. Retorna `{"ok": true}` |
| `GET` | `/api/export.csv` | Baixa o `contatos.csv` |

Campos aceitos no `POST`/`PUT`: `nome`, `sobrenome`, `email`, `numero`, `tags`, `observacoes`. `id` e `data_adicao` são sempre gerados pelo sistema.

### Tags

Objeto retornado:

```json
{ "id": "t1a2b3c", "nome": "Cliente", "cor": "verde", "contatos": 12 }
```

`contatos` é a quantidade de contatos que usam a tag (só aparece na listagem).

| Método | Rota | Corpo | Descrição |
|---|---|---|---|
| `GET` | `/api/tags` | — | Lista as tags, com a contagem de contatos |
| `POST` | `/api/tags` | `{"nome": "...", "cor": "verde"}` | Cria. `nome` obrigatório; `cor` opcional. `400` se a tag já existe ou a cor é inválida. Retorna `201` |
| `PUT` ou `PATCH` | `/api/tags/<id>` | `{"cor": "roxo"}` | Troca a cor (`404` se não existir) |
| `DELETE` | `/api/tags/<id>` | — | Apaga a tag **e** tira ela de todos os contatos |

Cores válidas: `azul`, `ciano`, `ambar`, `verde`, `vermelho`, `roxo`, `teal`, `cinza`.

### Exemplos

```bash
# listar / buscar
curl http://localhost:8080/api/contatos
curl "http://localhost:8080/api/contatos?q=black%20friday"

# criar a tag e depois o contato
curl -X POST http://localhost:8080/api/tags \
  -H "Content-Type: application/json" \
  -d '{"nome":"Black Friday 2026","cor":"ambar"}'

curl -X POST http://localhost:8080/api/contatos \
  -H "Content-Type: application/json" \
  -d '{"nome":"Maria","sobrenome":"Silva","email":"maria@x.com",
       "numero":"51999990000","tags":["Black Friday 2026"],"observacoes":"Indicação"}'

# alterar só o e-mail e as tags
curl -X PATCH http://localhost:8080/api/contatos/a1b2c3d4 \
  -H "Content-Type: application/json" \
  -d '{"email":"novo@x.com","tags":"Cliente,Black Friday 2026"}'

# trocar a cor de uma tag / apagar uma tag
curl -X PUT http://localhost:8080/api/tags/t1a2b3c -H "Content-Type: application/json" -d '{"cor":"roxo"}'
curl -X DELETE http://localhost:8080/api/tags/t1a2b3c
```

### Códigos de resposta

| Status | Quando |
|---|---|
| `200` | Sucesso (leitura, alteração, exclusão) |
| `201` | Criado |
| `400` | Dados inválidos (nome vazio, cor inválida, tag duplicada, corpo malformado) |
| `404` | Contato ou tag não encontrado |

---

## Notas de mudanças

Mudanças em relação às versões anteriores. Quem tem algum script ou integração usando a API deve ler a lista de itens que quebram compatibilidade.

### Versão atual (28/10/2026)

**API**
- Texto de entrada limpo no servidor (espaços repetidos/das pontas, e-mail sem espaços e em minúsculo, tags sem repetição). Veja [Limpeza automática](#limpeza-automática-dos-dados).
- A busca `?q=` também ignora espaços sobrando.
- `PUT`/`PATCH` em `/api/contatos/<id>` agora aceita **atualização parcial**. Antes exigia `nome` em toda chamada.
- Corpo da requisição que não seja um objeto (ex.: `[1,2]`) retorna `400` em vez de erro interno.
- Contatos já salvos são limpos uma vez na subida do servidor.

**Painel**
- Campos nome, sobrenome e e-mail são limpos ao sair do campo.

### Versão anterior (27/10/2026)

**Tags**
- **Unificação:** removida a separação perfil/campanha. O campo `tipo` não existe mais.
- **Cor:** cada tag tem uma `cor` (8 opções). O `tags.csv` passou de `id, nome, tipo` para `id, nome, cor`. Arquivos antigos são convertidos sozinhos na primeira subida, com cores atribuídas em rodízio. Os contatos não são alterados.
- **Exclusão:** novo botão "Excluir" no gerenciador. Apaga a tag e a remove de todos os contatos.
- **Trocar cor:** na linha da tag, no gerenciador.
- Nome de tag sem vírgula e ponto e vírgula, com no máximo 40 caracteres.

**API — mudanças que quebram compatibilidade**

| Antes | Agora |
|---|---|
| `POST /api/tags` com `{"nome","tipo"}` (`tipo`: `perfil` ou `campanha`) | `{"nome","cor"}`. O campo `tipo` é ignorado |
| Tag retornada como `{id, nome, tipo}` | `{id, nome, cor}` (+ `contatos` na listagem) |
| — | Novos: `PUT`/`PATCH /api/tags/<id>` e `DELETE /api/tags/<id>` |
| `GET /api/contatos?categoria=...`, `?perfil=...`, `?campanha=...` | Removidos. Use `?q=` (busca também nas tags) |
| Contato com campo `categoria` | Campo `tags` (texto separado por vírgula) |

**Painel**
- Filtros por aba/categoria removidos. A busca cobre nome, e-mail, número, observações e tags.
- Tags exibidas com a cor escolhida; no formulário do contato, como chips coloridos.

### Versões anteriores

- **API sem chave:** o cabeçalho `X-API-Key` e o parâmetro `?key=` foram removidos. As rotas `/api/*` ficam abertas.
- **Marca:** logo e texto "HidroMonitor • CRM" no topo e na tela de login (reescrita, com painel da marca ao lado do formulário), com a fonte XXII Geom Bold.
- **Acessibilidade e atalhos:** `Enter` pula de campo, `Ctrl+Enter` salva, `Esc` fecha janelas, foco visível nas tags. Telefone formatado ao digitar.
- **Correção:** o caminho da logo usava barra invertida (`static\logo...`), que não funciona no Docker/Linux. Agora usa `url_for`.
- **Inicialização:** os arquivos CSV são criados/migrados também quando rodando via gunicorn (Docker).

---

## Segurança

- A **API não pede chave nem login**: qualquer máquina que alcance a porta 8080 consegue ler, alterar e apagar contatos e tags. Use apenas em rede local fechada.
- A senha do painel é em texto plano e o tráfego é HTTP.
- Não exponha a porta 8080 na internet. Se precisar, coloque um proxy com HTTPS e controle de acesso na frente.
- Faça cópia periódica da pasta `./data`. É nela que está tudo.