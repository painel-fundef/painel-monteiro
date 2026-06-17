# Painel de Monitoramento Estratégico — Monteiro & Monteiro

Painel de BI gerado automaticamente a partir da planilha Google Sheets e publicado via GitHub Pages.

---

## Como funciona

```
Planilha Google Sheets
        ↓  (API)
    build.py         ← lê e normaliza os dados
        ↓
  docs/index.html    ← painel HTML autocontido
        ↓  (GitHub Pages)
   URL pública       ← acessível pelo navegador
```

O disparo é **manual**: você clica num botão no GitHub e o painel é atualizado em ~30 segundos.

---

## Configuração (uma vez só)

### 1. Criar o repositório no GitHub

1. Acesse [github.com](https://github.com) → **New repository**
2. Nome sugerido: `painel-monteiro`
3. Marque **Private** (recomendado — o código e os dados ficam privados)
4. Clique em **Create repository**
5. Suba os arquivos deste pacote:
   ```bash
   git init
   git add .
   git commit -m "setup inicial"
   git remote add origin https://github.com/SEU_USUARIO/painel-monteiro.git
   git push -u origin main
   ```

---

### 2. Ativar o GitHub Pages

1. No repositório → **Settings** → **Pages**
2. Em *Source*, selecione **Deploy from a branch**
3. Branch: `main` / Folder: `/docs`
4. Clique em **Save**

Seu painel ficará disponível em:
`https://SEU_USUARIO.github.io/painel-monteiro/`

---

### 3. Criar a Service Account no Google Cloud

1. Acesse [console.cloud.google.com](https://console.cloud.google.com)
2. Crie um projeto (ou use um existente)
3. Menu → **APIs e serviços** → **Biblioteca**
   - Ative a **Google Sheets API**
4. Menu → **APIs e serviços** → **Credenciais**
   - Clique em **Criar credenciais** → **Conta de serviço**
   - Nome: `painel-monteiro` → **Criar e continuar** → **Concluído**
5. Clique na conta de serviço criada → aba **Chaves**
   - **Adicionar chave** → **Criar nova chave** → **JSON** → **Criar**
   - Um arquivo `.json` será baixado — **guarde-o com segurança**

---

### 4. Compartilhar a planilha com a Service Account

1. Abra o arquivo JSON baixado e copie o campo `"client_email"`
   (algo como `painel-monteiro@seu-projeto.iam.gserviceaccount.com`)
2. Abra a planilha Google Sheets
3. Clique em **Compartilhar** e cole o e-mail acima com permissão de **Leitor**

---

### 5. Configurar os Secrets no GitHub

No repositório → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Crie três secrets:

| Nome | Valor |
|------|-------|
| `GOOGLE_SERVICE_ACCOUNT_JSON` | conteúdo completo do arquivo `.json` da Service Account (cole tudo) |
| `SPREADSHEET_ID` | ID da planilha — é a parte da URL entre `/d/` e `/edit`<br>Ex: `https://docs.google.com/spreadsheets/d/**1o3hYd5euWdgNHms-qL6ejlA3gdiLJ2K0UHefvcaVgrE**/edit` |
| `SHEET_NAME` | nome da aba com os dados (ex: `Monitoramento`) |

---

## Como atualizar o painel

1. Abra o repositório no GitHub
2. Clique na aba **Actions**
3. Clique em **Atualizar Painel** (à esquerda)
4. Clique no botão **Run workflow** → **Run workflow**
5. Aguarde ~30 segundos — o painel estará atualizado

---

## Estrutura do repositório

```
painel-monteiro/
├── build.py                          # script principal
├── requirements.txt                  # dependências Python
├── docs/
│   └── index.html                    # painel gerado (não editar manualmente)
└── .github/
    └── workflows/
        └── atualizar-painel.yml      # workflow do GitHub Actions
```

---

## Manutenção

**Adicionar nova coluna à planilha** → edite o dicionário no passo 4 do `build.py` (seção "Montar lista de registros") e adicione o campo correspondente ao template HTML.

**Alterar layout ou cores** → edite a seção `TEMPLATE` no `build.py` e rode o workflow novamente.

**Testar localmente** antes de subir:
```bash
pip install -r requirements.txt
export GOOGLE_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}'
export SPREADSHEET_ID='1o3hYd5...'
export SHEET_NAME='Monitoramento'
python build.py
# abre docs/index.html no navegador
```
