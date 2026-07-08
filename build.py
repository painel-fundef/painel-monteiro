"""
build.py — Painel de Monitoramento Estratégico · Monteiro & Monteiro
Lê a planilha Google Sheets e gera docs/index.html

Variáveis de ambiente (GitHub Secrets):
  GOOGLE_SERVICE_ACCOUNT_JSON  – JSON da Service Account
  SPREADSHEET_ID               – ID da planilha
  SHEET_NAME                   – nome da aba (padrão: Monitoramento)
"""

import json, os, unicodedata
from datetime import datetime, timezone

import gspread
from google.oauth2.service_account import Credentials

# ── 1. Autenticação ───────────────────────────────────────────────────────────

SA_JSON       = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]
SPREADSHEET_ID = os.environ["SPREADSHEET_ID"]
SHEET_NAME    = os.environ.get("SHEET_NAME", "Monitoramento")

creds  = Credentials.from_service_account_info(
    json.loads(SA_JSON),
    scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
)
client = gspread.authorize(creds)
sheet  = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)
rows   = sheet.get_all_records(default_blank="")

# ── 2. Normalização de nomes ──────────────────────────────────────────────────

def strip(s): return str(s).strip()

def parse_value(s):
    s = strip(s)
    if not s: return 0.0
    s = s.replace("R$","").replace(".","").replace(",",".").strip()
    try: return float(s)
    except: return 0.0

def ascii_key(s):
    s = strip(s)
    s = "".join(c for c in unicodedata.normalize("NFD",s) if unicodedata.category(c)!="Mn")
    return " ".join(s.upper().split())

def build_canon_map(values):
    best = {}
    for v in values:
        v = strip(v)
        if not v: continue
        k = ascii_key(v)
        acc = sum(1 for c in unicodedata.normalize("NFD",v) if unicodedata.category(c)=="Mn")
        sc  = (acc, sum(1 for c in v if c.islower()))
        if k not in best or sc > best[k][1]: best[k] = (v,sc)
    return {k:val[0] for k,val in best.items()}

def canon(s, cmap):
    s = strip(s)
    return cmap.get(ascii_key(s), s) if s else ""

def titlecase(s):
    if not s: return ""
    small = {"de","da","do","das","dos","e"}
    return " ".join(w.lower() if w.lower() in small and i>0 else w.capitalize()
                    for i,w in enumerate(s.split()))

cmap_resp = build_canon_map([r.get("Magistrado Responsável","") for r in rows])
cmap_piso = build_canon_map([r.get("Magistrado de Piso","")    for r in rows])

# ── 3. Montar registros ───────────────────────────────────────────────────────

records = []
for r in rows:
    records.append({
        "proc":        strip(r.get("Processo","")),
        "parte":       strip(r.get("Nome das Partes","")),
        "trib":        strip(r.get("Tribunal Responsável","")),
        "grau":        strip(r.get("Localização do Processo","")),
        "vara":        strip(r.get("Vara de Origem","")),
        "turma":       strip(r.get("Turma","")),
        "piso":        titlecase(canon(r.get("Magistrado de Piso",""),    cmap_piso)),
        "relator":     titlecase(canon(r.get("Magistrado Responsável",""), cmap_resp)),
        "pautado":     strip(r.get("Processo Pautado?","")),
        "tipoSessao":  strip(r.get("Tipo da Sessão","")),
        "dataSessao":  strip(r.get("Data da Sessão","")),
        "resultado":   strip(r.get("Resultado do Julgamento","")),
        "situacao":    strip(r.get("Situação do Processo","")),
        "tipoAcao":    strip(r.get("Tipo da Ação","")),
        "materia":     strip(r.get("Matéria","")),
        "objetivo":    strip(r.get("Objetivo Atual","")),
        "envolvimento":strip(r.get("Envolvimento da Monteiro","")),
        "setor":       strip(r.get("Setor Responsável","")),
        "filial":      strip(r.get("Filial Responsável","")),
        "respMatriz":  strip(r.get("Responsável Matriz","")),
        "respFilial":  strip(r.get("Responsável na Filial","")),
        "valEnv":      parse_value(r.get("Valores Envolvidos","")),
        "valCont":     parse_value(r.get("Valores a Contingenciar","")),
        # ── campos da nova aba ───────────────────────────────────────────────
        "pendencia":   strip(r.get("Pendências","")),
        "dataAndamento": strip(r.get("Data do Último Andamento","")),
        "ultimoAndamento": strip(r.get("Último Andamento","")),
    })

data_json  = json.dumps(records, ensure_ascii=False)
updated_at = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
print(f"✓ {len(records)} processos lidos · {updated_at}")

# ── 4. Template HTML ──────────────────────────────────────────────────────────

TEMPLATE = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Painel de Monitoramento Estratégico — Monteiro &amp; Monteiro</title>
<style>
  :root{
    --ink:#10211b;--paper:#f1f5f2;--card:#ffffff;--line:#cfdcd4;
    --jade:#0d9466;--jade-d:#066046;--jade-l:#d6f3e6;
    --brass:#e08a16;--brass-l:#fdeccb;
    --rust:#e0452c;--rust-l:#fbddd5;
    --slate:#5a6f67;--shadow:rgba(13,148,102,.10);
  }
  *{box-sizing:border-box;margin:0;padding:0}
  body{background:var(--paper);color:var(--ink);
    font-family:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;
    line-height:1.45;-webkit-font-smoothing:antialiased}
  .wrap{max-width:1280px;margin:0 auto;padding:28px 22px 80px}
  .mono{font-family:"SFMono-Regular",Menlo,Consolas,monospace}
  header.top{display:flex;justify-content:space-between;align-items:flex-end;
    border-bottom:2px solid var(--ink);padding-bottom:14px;margin-bottom:8px;gap:16px;flex-wrap:wrap}
  .brand h1{font-size:25px;letter-spacing:.2px;font-weight:600}
  .brand .sub{font-size:12.5px;color:var(--slate);text-transform:uppercase;letter-spacing:2.5px;margin-top:3px}
  .stamp{font-size:11px;color:var(--slate);text-align:right;line-height:1.6;text-transform:uppercase;letter-spacing:1px}
  .tabs{display:flex;gap:4px;margin:20px 0 0;border-bottom:1px solid var(--line)}
  .tab{font-family:inherit;font-size:13px;letter-spacing:.6px;padding:10px 18px;border:none;background:none;
    color:var(--slate);cursor:pointer;border-bottom:2px solid transparent;margin-bottom:-1px;text-transform:uppercase}
  .tab.active{color:var(--jade-d);border-bottom-color:var(--jade);font-weight:600}
  .tab:hover{color:var(--jade-d)}
  .kpis{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin:22px 0 8px}
  .kpi{background:var(--card);border:1px solid var(--line);border-radius:3px;padding:14px 15px;position:relative;overflow:hidden}
  .kpi::before{content:"";position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--jade)}
  .kpi.alert::before{background:var(--rust)}.kpi.brass::before{background:var(--brass)}
  .kpi .lab{font-size:10.5px;text-transform:uppercase;letter-spacing:1.4px;color:var(--slate)}
  .kpi .num{font-size:26px;font-weight:600;margin-top:7px;line-height:1}
  .kpi .note{font-size:11px;color:var(--slate);margin-top:5px}
  .kpi .num.sm{font-size:18px}
  .filterbar{display:flex;gap:9px;flex-wrap:wrap;align-items:center;margin:22px 0 6px;
    padding:13px 14px;background:var(--jade-l);border:1px solid #cfe0d9;border-radius:3px}
  .filterbar .ft{font-size:10.5px;text-transform:uppercase;letter-spacing:1.4px;color:var(--jade-d);font-weight:600}
  select,input[type=search]{font-family:inherit;font-size:13px;padding:6px 9px;border:1px solid var(--line);
    background:var(--card);border-radius:3px;color:var(--ink);min-width:120px}
  input[type=search]{min-width:200px;flex:1}
  .clearbtn{font-family:inherit;font-size:12px;padding:6px 13px;border:1px solid var(--jade);
    background:var(--jade);color:#fff;border-radius:3px;cursor:pointer}
  .clearbtn:hover{background:var(--jade-d)}
  .grid{display:grid;grid-template-columns:repeat(12,1fr);gap:16px;margin-top:22px}
  .panel{background:var(--card);border:1px solid var(--line);border-radius:3px;padding:15px 16px;box-shadow:0 1px 0 var(--shadow)}
  .panel h2{font-size:12.5px;text-transform:uppercase;letter-spacing:1.6px;color:var(--jade-d);
    border-bottom:1px solid var(--line);padding-bottom:9px;margin-bottom:12px;
    display:flex;justify-content:space-between;align-items:baseline;gap:8px}
  .panel h2 .tot{font-size:11px;color:var(--slate);letter-spacing:.5px;text-transform:none;font-weight:400;white-space:nowrap}
  .col3{grid-column:span 3}.col4{grid-column:span 4}.col5{grid-column:span 5}
  .col6{grid-column:span 6}.col7{grid-column:span 7}.col8{grid-column:span 8}.col12{grid-column:span 12}
  .bars{display:flex;flex-direction:column;gap:7px}
  .bar{display:grid;grid-template-columns:118px 1fr 42px;align-items:center;gap:9px;cursor:pointer;padding:2px 3px;border-radius:3px}
  .bar:hover{background:var(--jade-l)}.bar.active{background:var(--brass-l)}
  .bar .bl{font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .bar .track{height:14px;background:#ece6da;border-radius:2px;overflow:hidden}
  .bar .fill{height:100%;background:var(--jade);border-radius:2px;transition:width .35s ease}
  .bar:nth-child(even) .fill{background:#2c8470}
  .bar .bv{font-size:11.5px;text-align:right;color:var(--slate);font-variant-numeric:tabular-nums}
  .donut-wrap{display:flex;align-items:center;gap:16px}
  .legend{display:flex;flex-direction:column;gap:6px;flex:1}
  .legend .li{display:flex;align-items:center;gap:8px;font-size:12px;cursor:pointer;padding:2px 4px;border-radius:3px}
  .legend .li:hover{background:var(--jade-l)}.legend .li.active{background:var(--brass-l)}
  .legend .sw{width:11px;height:11px;border-radius:2px;flex-shrink:0}
  .legend .lv{margin-left:auto;color:var(--slate);font-variant-numeric:tabular-nums}
  .toprisk{display:flex;flex-direction:column}
  .rr{display:grid;grid-template-columns:1fr auto;gap:10px;padding:8px 4px;border-bottom:1px dotted var(--line);cursor:pointer}
  .rr:last-child{border-bottom:none}.rr:hover{background:var(--jade-l)}
  .rr .rn{font-size:12.5px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .rr .rm{font-size:10.5px;color:var(--slate);text-transform:uppercase;letter-spacing:.6px}
  .rr .rv{font-size:13px;font-weight:600;color:var(--jade-d);text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
  .rr.cont .rv{color:var(--rust)}
  .rank{display:flex;flex-direction:column}
  .rkrow{display:grid;grid-template-columns:20px 1fr auto;gap:10px;align-items:center;padding:8px 5px;border-bottom:1px dotted var(--line);cursor:pointer}
  .rkrow:last-child{border-bottom:none}.rkrow:hover{background:var(--jade-l)}.rkrow.active{background:var(--brass-l)}
  .rkrow .rkn{font-size:13px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .rkrow .rksub{font-size:10.5px;color:var(--slate);margin-top:1px}
  .rkrow .rkidx{font-size:11px;color:var(--brass);font-weight:600;text-align:center}
  .rkrow .rkmeta{text-align:right;white-space:nowrap}
  .rkrow .rkn-proc{font-size:14px;font-weight:600;color:var(--jade-d)}
  .rkrow .rkn-val{font-size:10.5px;color:var(--slate)}
  .minictx{font-size:11px;color:var(--slate);margin-bottom:10px;line-height:1.5}
  .conc-note{background:var(--brass-l);border:1px solid #e6d3a8;border-radius:3px;padding:11px 13px;font-size:12px;line-height:1.55;margin-bottom:4px}
  .conc-note b{color:var(--brass)}
  .tree{display:flex;flex-direction:column;gap:2px}
  .trib-row{display:grid;grid-template-columns:16px 1fr 80px auto;gap:9px;align-items:center;padding:8px 6px;cursor:pointer;border-bottom:1px solid var(--line)}
  .trib-row:hover{background:var(--jade-l)}
  .trib-row .tw{font-size:11px;color:var(--slate);transition:transform .2s;display:inline-block}
  .trib-row.open .tw{transform:rotate(90deg)}
  .trib-row .tname{font-size:14px;font-weight:600;color:var(--jade-d)}
  .trib-row .tbadge{font-size:11px;color:var(--slate);text-align:right;white-space:nowrap}
  .trib-row .tbadge b{color:var(--ink);font-size:13px}
  .tchildren{display:none;padding:2px 0 8px 26px;background:rgba(31,111,92,.03)}
  .tnode.open .tchildren{display:block}
  .vara-row{display:grid;grid-template-columns:14px 1fr auto;gap:8px;align-items:center;padding:6px 5px;cursor:pointer;border-bottom:1px dotted var(--line)}
  .vara-row:hover{background:var(--jade-l)}
  .vara-row .vw{font-size:10px;color:var(--slate);transition:transform .2s;display:inline-block}
  .vara-row.open .vw{transform:rotate(90deg)}
  .vara-row .vname{font-size:12.5px;font-weight:600}
  .vara-row .vbadge{font-size:10.5px;color:var(--slate);white-space:nowrap}
  .vchildren{display:none;padding:3px 0 6px 22px}
  .vara-node.open .vchildren{display:block}
  .proc-leaf{display:grid;grid-template-columns:1fr auto;gap:8px;padding:4px 5px;cursor:pointer;border-bottom:1px dotted #ece6da}
  .proc-leaf:hover{background:var(--brass-l)}
  .proc-leaf .pln{font-size:12px}.proc-leaf .plm{font-size:10px;color:var(--slate);margin-top:1px}
  .proc-leaf .plv{font-size:11px;color:var(--jade-d);white-space:nowrap;text-align:right}
  .sit-wrap{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
  .sit-card{border-radius:4px;padding:14px 16px;display:flex;align-items:center;gap:14px;cursor:pointer;border:2px solid transparent;transition:border-color .2s}
  .sit-card:hover{border-color:currentColor}.sit-card.active{border-color:currentColor;box-shadow:0 0 0 3px rgba(0,0,0,.07)}
  .sit-card.fav{background:#d6f3e6;color:#066046}.sit-card.desf{background:#fbddd5;color:#b83218}.sit-card.nd{background:#f1f5f2;color:#5a6f67}
  .sit-icon{font-size:28px;line-height:1;flex-shrink:0}
  .sit-body .sit-label{font-size:11px;text-transform:uppercase;letter-spacing:1.4px;font-weight:600;opacity:.8}
  .sit-body .sit-num{font-size:32px;font-weight:700;line-height:1;margin-top:3px}
  .sit-body .sit-pct{font-size:11px;opacity:.7;margin-top:3px}
  .agenda{display:flex;flex-direction:column;gap:9px}
  .agenda.agenda-row{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:10px}
  .ag{display:grid;grid-template-columns:54px 1fr;gap:12px;align-items:center;padding:9px;border:1px solid var(--line);border-radius:3px;background:var(--paper);cursor:pointer}
  .ag:hover{border-color:var(--jade)}
  .ag .date{text-align:center;border-right:1px solid var(--line);padding-right:8px}
  .ag .date .d{font-size:19px;font-weight:600;line-height:1;color:var(--jade-d)}
  .ag .date .m{font-size:9.5px;text-transform:uppercase;letter-spacing:1px;color:var(--slate);margin-top:2px}
  .ag .ai .an{font-size:13px;font-weight:600}.ag .ai .am{font-size:11px;color:var(--slate);margin-top:2px}
  .ag .tag{display:inline-block;font-size:9.5px;text-transform:uppercase;letter-spacing:.8px;padding:1px 6px;border-radius:2px;margin-top:4px}
  .tag.virt{background:var(--jade-l);color:var(--jade-d)}.tag.pres{background:var(--brass-l);color:var(--brass)}

  /* ── Aba Andamentos ────────────────────────────── */
  .pend-cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px;margin-bottom:4px}
  .pend-chip{border-radius:4px;padding:11px 14px;cursor:pointer;border:2px solid transparent;
    background:var(--brass-l);color:#7a4a00;transition:border-color .15s}
  .pend-chip:hover{border-color:var(--brass)}.pend-chip.active{border-color:var(--brass);box-shadow:0 0 0 3px rgba(224,138,22,.15)}
  .pend-chip .pc-label{font-size:10.5px;text-transform:uppercase;letter-spacing:1.2px;font-weight:600;opacity:.8}
  .pend-chip .pc-num{font-size:24px;font-weight:700;line-height:1;margin-top:4px}
  .pend-timeline{display:flex;flex-direction:column;gap:0}
  .pt-row{display:grid;grid-template-columns:90px 160px 1fr auto;gap:12px;align-items:start;
    padding:10px 8px;border-bottom:1px solid var(--line);cursor:pointer}
  .pt-row:hover{background:var(--jade-l)}
  .pt-row .pt-date{font-size:11px;color:var(--slate);font-variant-numeric:tabular-nums;padding-top:2px;white-space:nowrap}
  .pt-row .pt-pend{display:inline-block;font-size:10.5px;font-weight:600;padding:2px 8px;
    border-radius:10px;background:var(--brass-l);color:#7a4a00;white-space:nowrap}
  .pt-row .pt-body .pt-parte{font-size:13px;font-weight:600}
  .pt-row .pt-body .pt-and{font-size:11.5px;color:var(--slate);margin-top:3px;line-height:1.4}
  .pt-row .pt-body .pt-meta{font-size:10.5px;color:var(--slate);margin-top:4px;opacity:.8}
  .pt-row .pt-val{font-size:12px;font-weight:600;color:var(--jade-d);text-align:right;white-space:nowrap;font-variant-numeric:tabular-nums}

  .tablewrap{margin-top:22px;background:var(--card);border:1px solid var(--line);border-radius:3px;overflow:hidden}
  .tablewrap .th{display:flex;justify-content:space-between;align-items:center;padding:13px 16px;border-bottom:1px solid var(--line)}
  .tablewrap .th h2{font-size:12.5px;text-transform:uppercase;letter-spacing:1.6px;color:var(--jade-d)}
  .tablewrap .th .cnt{font-size:11.5px;color:var(--slate)}
  .scroll{max-height:560px;overflow:auto}
  table{width:100%;border-collapse:collapse;font-size:12px}
  thead th{position:sticky;top:0;background:var(--jade-d);color:#f6f3ec;text-align:left;
    padding:8px 11px;font-weight:500;font-size:10.5px;text-transform:uppercase;letter-spacing:.8px;white-space:nowrap;cursor:pointer;user-select:none}
  thead th:hover{background:var(--jade)}
  thead th .ar{opacity:.5;font-size:9px}
  tbody td{padding:7px 11px;border-bottom:1px solid #efe9dd;vertical-align:top}
  tbody tr:hover{background:var(--jade-l)}
  tbody tr:nth-child(even){background:rgba(0,0,0,.012)}
  tbody tr:nth-child(even):hover{background:var(--jade-l)}
  .pnome{font-weight:600;max-width:200px}
  .pmono{font-size:10.5px;color:var(--slate);white-space:nowrap}
  .pill{display:inline-block;font-size:10px;padding:1.5px 7px;border-radius:10px;white-space:nowrap}
  .pill.pub{background:#d6f3e6;color:#066046}.pill.trib{background:#fdeccb;color:#b06a08}
  .pill.civ{background:#d8eef5;color:#1f6d8a}.pill.imp{background:#fbddd5;color:#b83218}.pill.ele{background:#ece0f7;color:#6a3aa8}
  .pill.pend{background:var(--brass-l);color:#7a4a00}
  .vcell{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
  .vcell.cont{color:var(--rust);font-weight:600}
  .empty{padding:40px;text-align:center;color:var(--slate);font-size:13.5px}
  .pautada-dot{width:7px;height:7px;border-radius:50%;background:var(--brass);display:inline-block;margin-right:5px}
  footer{margin-top:30px;padding-top:14px;border-top:1px solid var(--line);
    font-size:11px;color:var(--slate);display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px}
  .view{display:none}.view.active{display:block}
  @media(max-width:1000px){
    .kpis{grid-template-columns:repeat(2,1fr)}
    .col3,.col4,.col5,.col6,.col7,.col8{grid-column:span 12}
    .pmono,.hide-sm{display:none}
    .pt-row{grid-template-columns:1fr auto}
  }
  @media(prefers-reduced-motion:reduce){*{transition:none!important}}
</style>
</head>
<body>
<div class="wrap">
  <header class="top">
    <div class="brand">
      <h1>Painel de Monitoramento Estratégico</h1>
      <div class="sub">Monteiro &amp; Monteiro · Carteira Processual</div>
    </div>
    <div class="stamp" id="stamp"></div>
  </header>

  <div class="tabs">
    <button class="tab active" data-view="geral">Visão geral</button>
    <button class="tab" data-view="foro">Foro &amp; magistratura</button>
    <button class="tab" data-view="andamentos">Andamentos &amp; pendências</button>
  </div>

  <div class="filterbar">
    <span class="ft">Filtros</span>
    <select id="f-trib"></select>
    <select id="f-setor"></select>
    <select id="f-filial"></select>
    <select id="f-grau"></select>
    <select id="f-env"></select>
    <select id="f-tipo"></select>
    <input type="search" id="f-busca" placeholder="Buscar parte, matéria, magistrado, andamento…">
    <button class="clearbtn" id="clear">Limpar</button>
  </div>

  <!-- VISÃO GERAL -->
  <div class="view active" id="view-geral">
    <section class="kpis" id="kpis"></section>
    <div class="grid">
      <div class="panel col12"><h2>Situação dos processos <span class="tot" id="t-sit"></span></h2><div class="sit-wrap" id="c-sit"></div></div>
      <div class="panel col12"><h2>Próximas sessões / pauta <span class="tot" id="t-pauta"></span></h2><div class="agenda agenda-row" id="c-agenda"></div></div>
      <div class="panel col4"><h2>Por tribunal <span class="tot" id="t-trib"></span></h2><div class="bars" id="c-trib"></div></div>
      <div class="panel col4"><h2>Por setor <span class="tot" id="t-setor"></span></h2><div class="donut-wrap"><canvas id="donut" width="120" height="120"></canvas><div class="legend" id="c-setor"></div></div></div>
      <div class="panel col4"><h2>Por filial <span class="tot" id="t-filial"></span></h2><div class="bars" id="c-filial"></div></div>
      <div class="panel col5"><h2>Envolvimento da Monteiro</h2><div class="bars" id="c-env"></div></div>
      <div class="panel col4"><h2>Tipos de ação <span class="tot" id="t-tipo"></span></h2><div class="bars" id="c-tipo"></div></div>
      <div class="panel col3"><h2>Por grau</h2><div class="bars" id="c-grau"></div></div>
      <div class="panel col7"><h2>Maiores valores envolvidos <span class="tot">Top 8</span></h2><div class="toprisk" id="c-topval"></div></div>
      <div class="panel col12"><h2>Risco a contingenciar <span class="tot" id="t-cont"></span></h2><div class="toprisk" id="c-cont"></div></div>
    </div>
  </div>

  <!-- FORO & MAGISTRATURA -->
  <div class="view" id="view-foro">
    <section class="kpis" id="kpis-foro"></section>
    <div class="grid">
      <div class="panel col12"><h2>Concentração de carteira <span class="tot">onde a exposição se acumula</span></h2><div class="conc-note" id="conc-note"></div></div>
      <div class="panel col6"><h2>Relatores / magistrados responsáveis <span class="tot" id="t-relator"></span></h2><div class="minictx">Quem decide hoje. Clique para filtrar.</div><div class="rank" id="c-relator"></div></div>
      <div class="panel col6"><h2>Magistrados de piso (origem) <span class="tot" id="t-piso"></span></h2><div class="minictx">Juízo de origem.</div><div class="rank" id="c-piso"></div></div>
      <div class="panel col6"><h2>Varas de origem <span class="tot" id="t-vara"></span></h2><div class="minictx">Concentração por juízo de origem.</div><div class="rank" id="c-vara"></div></div>
      <div class="panel col6"><h2>Turmas / órgãos colegiados <span class="tot" id="t-turma"></span></h2><div class="minictx">Órgãos fracionários.</div><div class="rank" id="c-turma"></div></div>
      <div class="panel col8"><h2>Cadeia de foro por tribunal <span class="tot">clique p/ expandir</span></h2><div class="tree" id="c-tree"></div></div>
      <div class="panel col4"><h2>Partes em múltiplas instâncias <span class="tot" id="t-multi"></span></h2><div class="minictx">Mesma parte em mais de um tribunal.</div><div class="rank" id="c-multi"></div></div>
    </div>
  </div>

  <!-- ANDAMENTOS & PENDÊNCIAS -->
  <div class="view" id="view-andamentos">
    <section class="kpis" id="kpis-and"></section>
    <div class="grid">
      <div class="panel col12">
        <h2>Tipo de pendência <span class="tot" id="t-pend"></span></h2>
        <div class="pend-cards" id="c-pend-chips"></div>
      </div>
      <div class="panel col12">
        <h2>Processos com pendência <span class="tot" id="t-and-lista"></span></h2>
        <div class="minictx">Ordenados por data do último andamento (mais recente primeiro). Clique para buscar o processo.</div>
        <div class="pend-timeline" id="c-timeline"></div>
      </div>
    </div>
  </div>

  <!-- TABELA COMPARTILHADA -->
  <div class="tablewrap">
    <div class="th"><h2 id="table-title">Processos</h2><span class="cnt" id="tcount"></span></div>
    <div class="scroll"><table><thead><tr id="thead-row"></tr></thead><tbody id="tbody"></tbody></table></div>
  </div>

  <footer>
    <span>Fonte: Google Sheets · atualizado automaticamente via GitHub Actions</span>
    <span id="fstamp"></span>
  </footer>
</div>

<script>
const DATA = __DATA__;
const UPDATED_AT = "__UPDATED_AT__";

const BRL=v=>v.toLocaleString('pt-BR',{style:'currency',currency:'BRL',maximumFractionDigits:0});
const BRLk=v=>{if(v>=1e9)return 'R$ '+(v/1e9).toLocaleString('pt-BR',{maximumFractionDigits:2})+' bi';if(v>=1e6)return 'R$ '+(v/1e6).toLocaleString('pt-BR',{maximumFractionDigits:1})+' mi';if(v>=1e3)return 'R$ '+(v/1e3).toLocaleString('pt-BR',{maximumFractionDigits:0})+' mil';return BRL(v);};
const SETOR_CLASS={'Público':'pub','Tributário':'trib','Cível':'civ','Improbidade':'imp','Eleitoral':'ele'};
const SETOR_COLOR={'Público':'#0d9466','Tributário':'#e08a16','Cível':'#2f8fb0','Improbidade':'#e0452c','Eleitoral':'#8a4fc4','—':'#aab8b1'};
const MONTHS=['JAN','FEV','MAR','ABR','MAI','JUN','JUL','AGO','SET','OUT','NOV','DEZ'];
const MAP={'Cumprimento de Sentença':'Cumprimento de Sentença','Cumprimento de Sentença - SUS':'Cumprimento de Sentença','Cumprimento de Sentença - FUNDEF DIFERENÇA':'Cumprimento de Sentença','Cumprimento Provisório de Sentença':'Cumprimento de Sentença','Agravo de Instrumento':'Agravo de Instrumento','Mandado de Segurança':'Mandado de Segurança','Ação Ordinária':'Ação Ordinária','Ação Ordinária - Rateio FUNDEF/FUNDEB':'Ação Ordinária','Ação Rescisória':'Ação Rescisória','Ação Popular':'Ação Popular','Ação Civil Pública':'Ação Civil Pública','Ação Civil Originária':'Ação Civil Pública','Execução de Título Extrajudicial':'Execução','Execução contra a fazenda pública':'Execução','Execução Fiscal':'Execução','Ação de Execução por Título Extrajudicial':'Execução','Liquidação de Sentença':'Liquidação','Liquidação por Arbitramento':'Liquidação','Embargos à Execução':'Embargos à Execução','Produção Antecipada de Provas':'Produção Antecipada de Provas','Ação Declaratória':'Ação Declaratória','Ação Declaratória de Nulidade':'Ação Declaratória','Ação de Cobrança de Honorários':'Ação de Cobrança','Ação de Cobrança':'Ação de Cobrança','Ação de cobrança':'Ação de Cobrança','Arbitramento de Honorários':'Ação de Cobrança','Tutela Provisória Antecedente':'Tutela / Medida Cautelar','-':'Outros','Petição Cível':'Outros','Consulta':'Outros','Consignação em Pagamento':'Outros','Aumento abusivo do IPTU':'Outros','Ação Anulatória de Ato Administrativo':'Outros','Ação de Repetição de Indébito':'Outros'};

let view='geral';
let filters={trib:'',setor:'',filial:'',grau:'',env:'',busca:'',relator:'',piso:'',vara:'',turma:'',tipo:'',situacao:'',pendencia:''};
let sortK='valEnv',sortDir=-1;

const n=s=>{s=(s==null?'':String(s)).trim();return s===''?'—':s;};
const isPendente=r=>r.pendencia&&r.pendencia.toLowerCase()!=='não'&&r.pendencia!=='';

function matchRow(r){
  if(filters.trib&&r.trib!==filters.trib)return false;
  if(filters.setor&&n(r.setor)!==filters.setor)return false;
  if(filters.filial&&n(r.filial)!==filters.filial)return false;
  if(filters.grau&&r.grau!==filters.grau)return false;
  if(filters.env&&n(r.envolvimento)!==filters.env)return false;
  if(filters.tipo&&(MAP[r.tipoAcao]||r.tipoAcao)!==filters.tipo)return false;
  if(filters.situacao!==''&&r.situacao!==filters.situacao)return false;
  if(filters.pendencia&&r.pendencia!==filters.pendencia)return false;
  if(filters.busca){
    const q=filters.busca.toLowerCase();
    const hay=(r.parte+' '+r.materia+' '+r.proc+' '+r.relator+' '+r.piso+' '+r.vara+' '+r.turma+' '+r.tipoAcao+' '+r.objetivo+' '+r.ultimoAndamento+' '+r.pendencia).toLowerCase();
    if(!hay.includes(q))return false;
  }
  return true;
}
const filtered=()=>DATA.filter(matchRow);

function countBy(rows,key){const m={};rows.forEach(r=>{const k=n(r[key]);m[k]=(m[k]||0)+1;});return Object.entries(m).sort((a,b)=>b[1]-a[1]);}
function aggFor(rows,key){const m={};rows.forEach(r=>{const k=n(r[key]);if(k==='—')return;if(!m[k])m[k]={nproc:0,val:0,valc:0};m[k].nproc++;m[k].val+=r.valEnv;m[k].valc+=r.valCont;});return Object.entries(m).sort((a,b)=>b[1].nproc-a[1].nproc||b[1].val-a[1].val);}
const focusProc=p=>{filters.busca=p;document.getElementById('f-busca').value=p;render();};

/* ── VISÃO GERAL ─────────────────────────────── */
function renderKPIs(rows){
  const env=rows.reduce((s,r)=>s+r.valEnv,0),cont=rows.reduce((s,r)=>s+r.valCont,0);
  const pend=rows.filter(isPendente).length;
  const hon=rows.filter(r=>n(r.envolvimento)==='Disputa de Honorários').length;
  document.getElementById('kpis').innerHTML=`
    <div class="kpi"><div class="lab">Processos</div><div class="num">${rows.length}</div><div class="note">na seleção atual</div></div>
    <div class="kpi brass"><div class="lab">Valor envolvido</div><div class="num sm">${BRLk(env)}</div><div class="note">${rows.filter(r=>r.valEnv>0).length} c/ valor lançado</div></div>
    <div class="kpi alert"><div class="lab">A contingenciar</div><div class="num sm">${BRLk(cont)}</div><div class="note">${rows.filter(r=>r.valCont>0).length} de risco</div></div>
    <div class="kpi brass"><div class="lab">Com pendência</div><div class="num">${pend}</div><div class="note">requerem ação</div></div>
    <div class="kpi"><div class="lab">Disputa de honorários</div><div class="num">${hon}</div><div class="note">frente de recuperação</div></div>`;
}
function bars(cid,tid,rows,key,fk){
  const d=countBy(rows,key),max=Math.max(1,...d.map(x=>x[1]));
  const c=document.getElementById(cid);
  c.innerHTML=d.map(([k,v])=>`<div class="bar ${filters[fk]===k?'active':''}" data-fk="${fk}" data-fv="${encodeURIComponent(k)}"><span class="bl" title="${k}">${k}</span><span class="track"><span class="fill" style="width:${v/max*100}%"></span></span><span class="bv">${v}</span></div>`).join('');
  if(tid)document.getElementById(tid).textContent=d.length+' grupos';
  c.onclick=e=>{const b=e.target.closest('.bar');if(b)toggleFilter(b.dataset.fk,decodeURIComponent(b.dataset.fv));};
}
function donut(rows){
  const d=countBy(rows,'setor'),tot=d.reduce((s,x)=>s+x[1],0)||1;
  const ctx=document.getElementById('donut').getContext('2d');ctx.clearRect(0,0,120,120);
  let a=-Math.PI/2;
  d.forEach(([k,v])=>{const sl=v/tot*Math.PI*2;ctx.beginPath();ctx.moveTo(60,60);ctx.arc(60,60,54,a,a+sl);ctx.closePath();ctx.fillStyle=SETOR_COLOR[k]||'#aab8b1';ctx.fill();a+=sl;});
  ctx.beginPath();ctx.arc(60,60,30,0,Math.PI*2);ctx.fillStyle='#fff';ctx.fill();
  ctx.fillStyle='#10211b';ctx.font='600 19px Georgia';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText(rows.length,60,57);
  ctx.fillStyle='#5a6f67';ctx.font='9px Georgia';ctx.fillText('TOTAL',60,72);
  const lg=document.getElementById('c-setor');
  lg.innerHTML=d.map(([k,v])=>`<div class="li ${filters.setor===k?'active':''}" data-fv="${encodeURIComponent(k)}"><span class="sw" style="background:${SETOR_COLOR[k]||'#aab8b1'}"></span>${k}<span class="lv">${v}</span></div>`).join('');
  document.getElementById('t-setor').textContent=d.length+' setores';
  lg.onclick=e=>{const li=e.target.closest('.li');if(li)toggleFilter('setor',decodeURIComponent(li.dataset.fv));};
}
function tipoAcao(rows){
  const m={};rows.forEach(r=>{const k=MAP[r.tipoAcao]||r.tipoAcao||'—';m[k]=(m[k]||0)+1;});
  const d=Object.entries(m).sort((a,b)=>b[1]-a[1]),max=Math.max(1,...d.map(x=>x[1]));
  document.getElementById('t-tipo').textContent=d.length+' tipos';
  const c=document.getElementById('c-tipo');
  c.innerHTML=d.map(([k,v])=>`<div class="bar ${filters.tipo===k?'active':''}" data-fk="tipo" data-fv="${encodeURIComponent(k)}" style="grid-template-columns:140px 1fr 36px"><span class="bl" title="${k}">${k}</span><span class="track"><span class="fill" style="width:${v/max*100}%"></span></span><span class="bv">${v}</span></div>`).join('');
  c.onclick=e=>{const b=e.target.closest('.bar');if(b)toggleFilter(b.dataset.fk,decodeURIComponent(b.dataset.fv));};
}
function topVal(rows){
  const t=[...rows].filter(r=>r.valEnv>0).sort((a,b)=>b.valEnv-a.valEnv).slice(0,8);
  const c=document.getElementById('c-topval');
  c.innerHTML=t.length?t.map(r=>`<div class="rr" data-p="${encodeURIComponent(r.proc)}"><div><div class="rn" title="${r.parte}">${r.parte}</div><div class="rm">${r.trib} · ${r.materia||r.tipoAcao||'—'}</div></div><div class="rv">${BRLk(r.valEnv)}</div></div>`).join(''):'<div class="empty">Sem valores lançados.</div>';
  c.onclick=e=>{const row=e.target.closest('.rr');if(row)focusProc(decodeURIComponent(row.dataset.p));};
}
function contRisk(rows){
  const t=[...rows].filter(r=>r.valCont>0).sort((a,b)=>b.valCont-a.valCont);
  document.getElementById('t-cont').textContent=t.length?BRL(t.reduce((s,r)=>s+r.valCont,0)):'';
  const c=document.getElementById('c-cont');
  c.innerHTML=t.length?t.map(r=>`<div class="rr cont" data-p="${encodeURIComponent(r.proc)}"><div><div class="rn" title="${r.parte}">${r.parte}</div><div class="rm">${r.trib} · ${r.tipoAcao||'—'}</div></div><div class="rv">${BRL(r.valCont)}</div></div>`).join(''):'<div class="empty">Nenhum valor a contingenciar.</div>';
  c.onclick=e=>{const row=e.target.closest('.rr');if(row)focusProc(decodeURIComponent(row.dataset.p));};
}
function situacao(rows){
  const fav=rows.filter(r=>r.situacao==='Favorável'),desf=rows.filter(r=>r.situacao==='Desfavorável'),nd=rows.filter(r=>r.situacao!=='Favorável'&&r.situacao!=='Desfavorável');
  const tot=rows.length||1,pct=v=>`${Math.round(v/tot*100)}%`;
  document.getElementById('t-sit').textContent=`${fav.length+desf.length} classificados de ${tot}`;
  const c=document.getElementById('c-sit');
  c.innerHTML=`
    <div class="sit-card fav ${filters.situacao==='Favorável'?'active':''}" data-sit="Fav%C3%B3ravel"><div class="sit-icon">✓</div><div class="sit-body"><div class="sit-label">Favorável</div><div class="sit-num">${fav.length}</div><div class="sit-pct">${pct(fav.length)} da carteira</div></div></div>
    <div class="sit-card desf ${filters.situacao==='Desfavorável'?'active':''}" data-sit="Desfavor%C3%A1vel"><div class="sit-icon">✕</div><div class="sit-body"><div class="sit-label">Desfavorável</div><div class="sit-num">${desf.length}</div><div class="sit-pct">${pct(desf.length)} da carteira</div></div></div>
    <div class="sit-card nd" data-sit=""><div class="sit-icon">·</div><div class="sit-body"><div class="sit-label">Não classificado</div><div class="sit-num">${nd.length}</div><div class="sit-pct">${pct(nd.length)} da carteira</div></div></div>`;
  c.onclick=e=>{const card=e.target.closest('.sit-card');if(card)toggleFilter('situacao',decodeURIComponent(card.dataset.sit));};
}
function agenda(rows){
  const p=rows.filter(r=>r.pautado==='Sim'&&r.dataSessao).sort((a,b)=>{const A=a.dataSessao.split('/').reverse().join(''),B=b.dataSessao.split('/').reverse().join('');return A<B?-1:1;});
  document.getElementById('t-pauta').textContent=p.length?p.length+' marcados':'';
  const c=document.getElementById('c-agenda');
  c.innerHTML=p.length?p.map(r=>{const[d,m]=r.dataSessao.split('/');const tg=r.tipoSessao==='Presencial'?'pres':'virt';
    return `<div class="ag" data-p="${encodeURIComponent(r.proc)}"><div class="date"><div class="d">${d}</div><div class="m">${MONTHS[parseInt(m)-1]||''}</div></div><div class="ai"><div class="an">${r.parte}</div><div class="am">${r.trib} · ${r.turma||''} · ${r.relator||''}</div><span class="tag ${tg}">${r.tipoSessao||'—'}</span></div></div>`;}).join(''):'<div class="empty">Nenhuma sessão pautada.</div>';
  c.onclick=e=>{const ag=e.target.closest('.ag');if(ag)focusProc(decodeURIComponent(ag.dataset.p));};
}

/* ── FORO & MAGISTRATURA ─────────────────────── */
function renderKPIsForo(rows){
  const uRel=new Set(rows.filter(r=>n(r.relator)!=='—').map(r=>r.relator)).size;
  const uPiso=new Set(rows.filter(r=>n(r.piso)!=='—').map(r=>r.piso)).size;
  const uVara=new Set(rows.filter(r=>n(r.vara)!=='—').map(r=>r.vara)).size;
  const uTurma=new Set(rows.filter(r=>n(r.turma)!=='—').map(r=>r.turma)).size;
  document.getElementById('kpis-foro').innerHTML=`
    <div class="kpi"><div class="lab">Tribunais</div><div class="num">${new Set(rows.map(r=>r.trib)).size}</div><div class="note">na seleção</div></div>
    <div class="kpi"><div class="lab">Relatores / juízos</div><div class="num">${uRel}</div><div class="note">magistrados responsáveis</div></div>
    <div class="kpi brass"><div class="lab">Magistrados de piso</div><div class="num">${uPiso}</div><div class="note">juízos de origem</div></div>
    <div class="kpi"><div class="lab">Varas de origem</div><div class="num">${uVara}</div><div class="note">distintas</div></div>
    <div class="kpi brass"><div class="lab">Turmas / colegiados</div><div class="num">${uTurma}</div><div class="note">órgãos fracionários</div></div>`;
}
function rankList(cid,tid,rows,key,fk){
  const agg=aggFor(rows,key);
  if(tid)document.getElementById(tid).textContent=agg.length+' distintos';
  const c=document.getElementById(cid);
  if(!agg.length){c.innerHTML='<div class="empty">Sem dados.</div>';return;}
  c.innerHTML=agg.slice(0,12).map(([k,o],i)=>{const val=o.val>0?BRLk(o.val):(o.valc>0?BRLk(o.valc)+' cont.':'—');
    return `<div class="rkrow ${filters[fk]===k?'active':''}" data-fk="${fk}" data-fv="${encodeURIComponent(k)}"><span class="rkidx">${i+1}</span><span><span class="rkn" title="${k}">${k}</span></span><span class="rkmeta"><span class="rkn-proc">${o.nproc}</span> <span class="rksub">proc.</span><br><span class="rkn-val">${val}</span></span></div>`;}).join('');
  c.onclick=e=>{const row=e.target.closest('.rkrow');if(row)toggleFilter(row.dataset.fk,decodeURIComponent(row.dataset.fv));};
}
function concentration(rows){
  const rel=aggFor(rows,'relator'),piso=aggFor(rows,'piso');
  const topRel=rel[0],topPiso=piso[0],byVal=[...rel].sort((a,b)=>b[1].val-a[1].val)[0];
  const parts=[];
  if(topRel)parts.push(`<b>${topRel[0]}</b> é o relator/juízo com mais feitos ativos (<b>${topRel[1].nproc}</b> processos).`);
  if(byVal&&byVal[1].val>0)parts.push(`A maior exposição financeira está com <b>${byVal[0]}</b>: ${BRLk(byVal[1].val)} em ${byVal[1].nproc} processo(s).`);
  if(topPiso)parts.push(`Na origem, <b>${topPiso[0]}</b> concentra ${topPiso[1].nproc} feitos de 1º grau.`);
  const sjdf=rows.filter(r=>/SJDF/i.test(r.vara)).length;
  if(sjdf)parts.push(`<b>${sjdf}</b> processos tramitam em varas da SJDF (Brasília).`);
  document.getElementById('conc-note').innerHTML=parts.join(' ');
}
function buildTree(rows){
  const tribs={};
  rows.forEach(r=>{const t=r.trib;if(!tribs[t])tribs[t]={n:0,val:0,varas:{}};tribs[t].n++;tribs[t].val+=r.valEnv;
    const vk=n(r.vara)==='—'?'— sem vara cadastrada':r.vara;
    if(!tribs[t].varas[vk])tribs[t].varas[vk]={n:0,val:0,procs:[]};
    tribs[t].varas[vk].n++;tribs[t].varas[vk].val+=r.valEnv;tribs[t].varas[vk].procs.push(r);});
  const c=document.getElementById('c-tree');
  c.innerHTML=Object.entries(tribs).sort((a,b)=>b[1].n-a[1].n).map(([t,o])=>{
    const varas=Object.entries(o.varas).sort((a,b)=>b[1].n-a[1].n);
    const varasHTML=varas.map(([vk,vo])=>{
      const leaves=[...vo.procs].sort((a,b)=>b.valEnv-a.valEnv).map(r=>{
        const mag=n(r.piso)!=='—'?r.piso:(n(r.relator)!=='—'?r.relator+' (rel.)':'—');
        return `<div class="proc-leaf" data-p="${encodeURIComponent(r.proc)}"><div><div class="pln">${r.parte}</div><div class="plm">${r.grau.replace(' GRAU','°')} · ${mag} · ${r.materia||r.tipoAcao||'—'}</div></div><div class="plv">${r.valEnv>0?BRLk(r.valEnv):'—'}</div></div>`;}).join('');
      return `<div class="vara-node"><div class="vara-row"><span class="vw">▶</span><span class="vname" title="${vk}">${vk}</span><span class="vbadge">${vo.n} proc${vo.val>0?' · '+BRLk(vo.val):''}</span></div><div class="vchildren">${leaves}</div></div>`;}).join('');
    return `<div class="tnode"><div class="trib-row"><span class="tw">▶</span><span class="tname">${t}</span><span style="font-size:11px;color:var(--slate)">${varas.length} vara(s)</span><span class="tbadge"><b>${o.n}</b> proc${o.val>0?' · '+BRLk(o.val):''}</span></div><div class="tchildren">${varasHTML}</div></div>`;}).join('');
  c.querySelectorAll('.trib-row').forEach(tr=>tr.onclick=()=>{tr.classList.toggle('open');tr.parentElement.classList.toggle('open');});
  c.querySelectorAll('.vara-row').forEach(vr=>vr.onclick=e=>{e.stopPropagation();vr.classList.toggle('open');vr.parentElement.classList.toggle('open');});
  c.onclick=e=>{const pl=e.target.closest('.proc-leaf');if(pl){e.stopPropagation();focusProc(decodeURIComponent(pl.dataset.p));}};
}
function multiInstance(rows){
  const m={};rows.forEach(r=>{(m[r.parte]=m[r.parte]||[]).push(r);});
  const multi=Object.entries(m).map(([k,v])=>[k,v,new Set(v.map(x=>x.trib))]).filter(x=>x[2].size>1).sort((a,b)=>b[2].size-a[2].size||b[1].length-a[1].length);
  document.getElementById('t-multi').textContent=multi.length+' partes';
  const c=document.getElementById('c-multi');
  if(!multi.length){c.innerHTML='<div class="empty">Nenhuma parte em múltiplos tribunais.</div>';return;}
  c.innerHTML=multi.slice(0,14).map(([k,v,ts])=>{const val=v.reduce((s,r)=>s+r.valEnv,0);
    return `<div class="rkrow" data-p="${encodeURIComponent(k)}"><span class="rkidx">${[...ts].length}</span><span><span class="rkn" title="${k}">${k}</span><div class="rksub">${[...ts].sort().join(' · ')}</div></span><span class="rkmeta"><span class="rkn-proc">${v.length}</span> <span class="rksub">proc.</span>${val>0?'<br><span class="rkn-val">'+BRLk(val)+'</span>':''}</span></div>`;}).join('');
  c.onclick=e=>{const row=e.target.closest('.rkrow');if(row)focusProc(decodeURIComponent(row.dataset.p));};
}

/* ── ANDAMENTOS & PENDÊNCIAS ─────────────────── */
function parseDateBR(s){
  if(!s)return null;
  const[d,m,y]=s.split('/');
  if(!d||!m||!y)return null;
  return new Date(+y,+m-1,+d);
}
function renderKPIsAnd(rows){
  const pend=rows.filter(isPendente);
  const tipos=new Set(pend.map(r=>r.pendencia)).size;
  const comData=pend.filter(r=>r.dataAndamento).length;
  const comAnd=pend.filter(r=>r.ultimoAndamento).length;
  document.getElementById('kpis-and').innerHTML=`
    <div class="kpi brass"><div class="lab">Processos com pendência</div><div class="num">${pend.length}</div><div class="note">de ${rows.length} na seleção</div></div>
    <div class="kpi"><div class="lab">Tipos de pendência</div><div class="num">${tipos}</div><div class="note">categorias distintas</div></div>
    <div class="kpi"><div class="lab">Com data de andamento</div><div class="num">${comData}</div><div class="note">têm data registrada</div></div>
    <div class="kpi"><div class="lab">Com último andamento</div><div class="num">${comAnd}</div><div class="note">têm texto registrado</div></div>
    <div class="kpi alert"><div class="lab">Sem data de andamento</div><div class="num">${pend.length-comData}</div><div class="note">cadastro incompleto</div></div>`;
}
function pendChips(rows){
  const pend=rows.filter(isPendente);
  const m={};pend.forEach(r=>{m[r.pendencia]=(m[r.pendencia]||0)+1;});
  const d=Object.entries(m).sort((a,b)=>b[1]-a[1]);
  document.getElementById('t-pend').textContent=d.length+' tipos';
  const c=document.getElementById('c-pend-chips');
  c.innerHTML=d.map(([k,v])=>`<div class="pend-chip ${filters.pendencia===k?'active':''}" data-pv="${encodeURIComponent(k)}">
    <div class="pc-label">${k}</div><div class="pc-num">${v}</div></div>`).join('');
  c.onclick=e=>{const ch=e.target.closest('.pend-chip');if(ch)toggleFilter('pendencia',decodeURIComponent(ch.dataset.pv));};
}
function timeline(rows){
  const pend=[...rows.filter(isPendente)].sort((a,b)=>{
    const da=parseDateBR(a.dataAndamento),db=parseDateBR(b.dataAndamento);
    if(da&&db)return db-da;
    if(da)return -1;if(db)return 1;return 0;
  });
  document.getElementById('t-and-lista').textContent=pend.length+' processos';
  const c=document.getElementById('c-timeline');
  if(!pend.length){c.innerHTML='<div class="empty">Nenhum processo com pendência nesta seleção.</div>';return;}
  c.innerHTML=pend.map(r=>`
    <div class="pt-row" data-p="${encodeURIComponent(r.proc)}">
      <div class="pt-date">${r.dataAndamento||'—'}</div>
      <div><span class="pt-pend">${r.pendencia}</span></div>
      <div class="pt-body">
        <div class="pt-parte">${r.parte}</div>
        <div class="pt-and">${r.ultimoAndamento||'—'}</div>
        <div class="pt-meta">${r.trib} · ${r.materia||r.tipoAcao||'—'} · ${n(r.relator)!=='—'?r.relator:'sem relator'}</div>
      </div>
      <div class="pt-val">${r.valEnv>0?BRLk(r.valEnv):'—'}</div>
    </div>`).join('');
  c.onclick=e=>{const row=e.target.closest('.pt-row');if(row)focusProc(decodeURIComponent(row.dataset.p));};
}

/* ── TABELA ──────────────────────────────────── */
const COLS_GERAL=[['parte','Parte / Processo'],['trib','Trib.'],['grau','Grau','hide-sm'],['setor','Setor'],['situacao','Situação'],['materia','Matéria','hide-sm'],['envolvimento','Envolvimento','hide-sm'],['filial','Filial','hide-sm'],['valEnv','Valor env.','vcell']];
const COLS_FORO=[['parte','Parte / Processo'],['trib','Trib.'],['vara','Vara de origem','hide-sm'],['piso','Mag. de piso'],['turma','Turma','hide-sm'],['relator','Relator / responsável'],['valEnv','Valor env.','vcell']];
const COLS_AND=[['parte','Parte / Processo'],['pendencia','Pendência'],['dataAndamento','Data andamento'],['ultimoAndamento','Último andamento'],['trib','Trib.','hide-sm'],['relator','Responsável','hide-sm'],['valEnv','Valor env.','vcell']];

function buildHead(){
  const cols=view==='foro'?COLS_FORO:view==='andamentos'?COLS_AND:COLS_GERAL;
  document.getElementById('thead-row').innerHTML=cols.map(c=>`<th data-k="${c[0]}" class="${c[2]||''}">${c[1]} <span class="ar"></span></th>`).join('');
  document.querySelectorAll('thead th').forEach(th=>{th.onclick=()=>{const k=th.dataset.k;if(sortK===k)sortDir*=-1;else{sortK=k;sortDir=(k==='valEnv')?-1:1;}render();};});
}
function table(rows){
  const cols=view==='foro'?COLS_FORO:view==='andamentos'?COLS_AND:COLS_GERAL;
  // na aba andamentos mostrar só pendentes
  const src=view==='andamentos'?rows.filter(isPendente):rows;
  const sorted=[...src].sort((a,b)=>{let x=a[sortK],y=b[sortK];if(typeof x==='number')return(x-y)*sortDir;x=(x||'').toString().toLowerCase();y=(y||'').toString().toLowerCase();return x<y?-sortDir:x>y?sortDir:0;});
  document.getElementById('tcount').textContent=`${sorted.length} de ${DATA.length}`;
  document.querySelectorAll('thead th .ar').forEach(a=>a.textContent='');
  const ah=document.querySelector(`thead th[data-k="${sortK}"] .ar`);if(ah)ah.textContent=sortDir<0?'▾':'▴';
  const tb=document.getElementById('tbody');
  if(!sorted.length){tb.innerHTML=`<tr><td colspan="${cols.length}"><div class="empty">Nenhum processo corresponde aos filtros.</div></td></tr>`;return;}
  tb.innerHTML=sorted.map(r=>{
    const dot=r.pautado==='Sim'?'<span class="pautada-dot" title="Pautado"></span>':'';
    const cells=cols.map(c=>{const k=c[0],cls=c[2]||'';
      if(k==='parte')return `<td class="pnome ${cls}">${dot}${r.parte}<div class="pmono mono">${r.proc}</div></td>`;
      if(k==='setor'){const sc=SETOR_CLASS[n(r.setor)]||'civ';return `<td class="${cls}"><span class="pill ${sc}">${n(r.setor)}</span></td>`;}
      if(k==='pendencia')return `<td class="${cls}"><span class="pill pend">${n(r.pendencia)}</span></td>`;
      if(k==='grau')return `<td class="${cls}">${r.grau.replace(' GRAU','°')}</td>`;
      if(k==='situacao'){if(r.situacao==='Favorável')return `<td><span style="color:#066046;font-weight:600">✓ Favorável</span></td>`;if(r.situacao==='Desfavorável')return `<td><span style="color:#b83218;font-weight:600">✕ Desfavorável</span></td>`;return `<td><span style="color:#5a6f67">—</span></td>`;}
      if(k==='valEnv')return `<td class="vcell ${r.valCont>0?'cont':''}">${r.valEnv>0?BRLk(r.valEnv):(r.valCont>0?BRLk(r.valCont):'—')}</td>`;
      if(k==='ultimoAndamento')return `<td class="${cls}" style="max-width:280px;font-size:11.5px;line-height:1.4">${n(r.ultimoAndamento)}</td>`;
      return `<td class="${cls}">${n(r[k])}</td>`;
    }).join('');
    return `<tr>${cells}</tr>`;
  }).join('');
}

/* ── FILTROS ─────────────────────────────────── */
function toggleFilter(k,v){filters[k]=filters[k]===v?'':v;syncSelects();render();}
function syncSelects(){
  const M={trib:'f-trib',setor:'f-setor',filial:'f-filial',grau:'f-grau',env:'f-env'};
  Object.keys(M).forEach(k=>{const el=document.getElementById(M[k]);if(el)el.value=filters[k];});
  const ft=document.getElementById('f-tipo');if(ft)ft.value=filters.tipo;
}

/* ── RENDER ──────────────────────────────────── */
function render(){
  const rows=filtered();
  if(view==='geral'){
    renderKPIs(rows);situacao(rows);agenda(rows);
    bars('c-trib','t-trib',rows,'trib','trib');donut(rows);bars('c-filial','t-filial',rows,'filial','filial');
    bars('c-env',null,rows,'envolvimento','env');tipoAcao(rows);bars('c-grau',null,rows,'grau','grau');
    topVal(rows);contRisk(rows);
    document.getElementById('table-title').textContent='Processos';
    sortK='valEnv';
  }else if(view==='foro'){
    renderKPIsForo(rows);concentration(rows);
    rankList('c-relator','t-relator',rows,'relator','relator');
    rankList('c-piso','t-piso',rows,'piso','piso');
    rankList('c-vara','t-vara',rows,'vara','vara');
    rankList('c-turma','t-turma',rows,'turma','turma');
    buildTree(rows);multiInstance(rows);
    document.getElementById('table-title').textContent='Processos · foro e magistratura';
  }else{
    renderKPIsAnd(rows);pendChips(rows);timeline(rows);
    document.getElementById('table-title').textContent='Processos com pendência';
  }
  table(rows);
}

/* ── INIT ────────────────────────────────────── */
(function(){
  const mk=(id,key,label)=>{const sel=document.getElementById(id);const opts=countBy(DATA,key);sel.innerHTML=`<option value="">${label}</option>`+opts.map(([k,v])=>`<option value="${k.replace(/"/g,'&quot;')}">${k} (${v})</option>`).join('');};
  mk('f-trib','trib','Tribunal');mk('f-setor','setor','Setor');mk('f-filial','filial','Filial');mk('f-grau','grau','Grau');mk('f-env','envolvimento','Envolvimento');
  (()=>{const sel=document.getElementById('f-tipo');const m={};DATA.forEach(r=>{const k=MAP[r.tipoAcao]||r.tipoAcao||'—';m[k]=(m[k]||0)+1;});const opts=Object.entries(m).sort((a,b)=>b[1]-a[1]);sel.innerHTML='<option value="">Tipo de ação</option>'+opts.map(([k,v])=>`<option value="${k.replace(/"/g,'&quot;')}">${k} (${v})</option>`).join('');sel.onchange=e=>{filters.tipo=e.target.value;render();};})();
  const M={'f-trib':'trib','f-setor':'setor','f-filial':'filial','f-grau':'grau','f-env':'env'};
  Object.keys(M).forEach(id=>document.getElementById(id).onchange=e=>{filters[M[id]]=e.target.value;render();});
  document.getElementById('f-busca').oninput=e=>{filters.busca=e.target.value;render();};
  document.getElementById('clear').onclick=()=>{
    filters={trib:'',setor:'',filial:'',grau:'',env:'',busca:'',relator:'',piso:'',vara:'',turma:'',tipo:'',situacao:'',pendencia:''};
    document.querySelectorAll('select').forEach(s=>s.value='');document.getElementById('f-busca').value='';render();
  };
  document.querySelectorAll('.tab').forEach(t=>t.onclick=()=>{
    view=t.dataset.view;
    document.querySelectorAll('.tab').forEach(x=>x.classList.toggle('active',x===t));
    ['geral','foro','andamentos'].forEach(v=>document.getElementById('view-'+v).classList.toggle('active',v===view));
    sortK=view==='andamentos'?'dataAndamento':'valEnv';sortDir=-1;buildHead();render();
  });
  const now=new Date(),ds=now.toLocaleDateString('pt-BR',{day:'2-digit',month:'long',year:'numeric'});
  document.getElementById('stamp').innerHTML=`Atualizado em<br>${UPDATED_AT}`;
  document.getElementById('fstamp').textContent=DATA.length+' processos · '+UPDATED_AT;
  buildHead();render();
})();
</script>
</body>
</html>"""

# ── 5. Gravar ─────────────────────────────────────────────────────────────────

output = TEMPLATE.replace("__DATA__", data_json).replace("__UPDATED_AT__", updated_at)
os.makedirs("docs", exist_ok=True)
with open("docs/index.html","w",encoding="utf-8") as f: f.write(output)
print(f"✓ docs/index.html gerado ({len(output):,} bytes)")
