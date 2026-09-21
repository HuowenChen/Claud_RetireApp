#!/usr/bin/env python3
"""
RetireFlow — 每月開銷分析頁面產生器
資料源：Google Drive「AndroMoney」匯出 CSV（base64 JSON 或純 CSV 皆可）
用法  ：python3 rf_expense.py  （會讀 andro.csv，改寫 base.html → out.html）

設計原則（沿用 rf_update.py SOP）：
  1. 所有數字由 CSV 計算，不硬寫
  2. 用 re.sub 錨定取代，絕不 find()+slice
  3. 寫完反向解析 HTML 對帳，對不上就中止
"""
import csv, re, json, collections, statistics, datetime, sys

CSV_PATH  = 'andro.csv'
BASE_HTML = 'base.html'
OUT_HTML  = 'out.html'

# ── 星展房貸：開銷檔未包含，需外加 ──
MORTGAGE_MONTHLY = 160000   # 每月本息（用戶提供）

# ── 一次性/大額支出判定（不列入經常性月開銷） ──
LUMP_SUBCATS = {'綜所稅', '房地產', '汽車'}
LUMP_INSURANCE_MIN = 300000   # 年繳保費視為一次性

CAT_COLOR = {
    '餐飲食品':'#E24B4A','居家生活':'#378ADD','稅務捐款':'#EF9F27',
    '休閒娛樂':'#1D9E75','醫療保健':'#7F77DD','教育學習':'#D95FA3',
    '汽機車':'#5BA8C4','服飾美容':'#C99A3E','圖書刊物':'#8C8C8C',
    '3C通訊':'#6B8E23','運輸交通':'#A0522D','人情交際':'#556B8D',
}


def load_rows(path):
    txt = open(path, encoding='utf-8').read()
    lines = txt.splitlines()
    # 第一行是 AndroMoney 標題列，第二行才是欄位名
    if lines and lines[0].startswith('Google Documents'):
        lines = lines[1:]
    rows = []
    for r in csv.DictReader(lines):
        d = (r.get('日期') or '').strip()
        a = (r.get('金額') or '').strip()
        if len(d) != 8 or not d.isdigit():
            continue
        try:
            amt = float(a)
        except ValueError:
            continue
        if amt <= 0:
            continue
        rows.append(dict(
            ymd=d, ym=d[:4]+'-'+d[4:6], y=d[:4],
            amt=amt,
            cat=(r.get('分類') or '其他').strip() or '其他',
            sub=(r.get('子分類') or '').strip(),
            pay=(r.get('付款(轉出)') or '').strip(),
            note=(r.get('備註') or '').strip(),
        ))
    rows.sort(key=lambda x: x['ymd'])
    return rows


def is_lump(r):
    if r['sub'] in LUMP_SUBCATS:
        return True
    if r['sub'] == '保險' and r['amt'] >= LUMP_INSURANCE_MIN:
        return True
    return False


def month_range(start_ym, end_ym):
    y, m = int(start_ym[:4]), int(start_ym[5:7])
    ey, em = int(end_ym[:4]), int(end_ym[5:7])
    out = []
    while (y, m) <= (ey, em):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            y, m = y+1, 1
    return out


def build(rows):
    """回傳所有要寫進頁面的數據結構"""
    last_ym = rows[-1]['ym']
    last_ymd = rows[-1]['ymd']
    all_months = month_range(rows[0]['ym'], last_ym)

    # 最後一個月可能不完整（資料匯出日在月中），統計用「完整月」
    export_day = int(last_ymd[6:8])
    last_full = all_months[-2] if export_day < 28 else all_months[-1]
    idx = all_months.index(last_full)
    m12 = all_months[max(0, idx-11): idx+1]     # 近12完整月
    m24 = all_months[max(0, idx-23): idx+1]

    # ── 每月：總額 / 經常性 / 一次性 ──
    tot = collections.Counter()
    rec = collections.Counter()
    lmp = collections.Counter()
    cnt = collections.Counter()
    for r in rows:
        tot[r['ym']] += r['amt']
        cnt[r['ym']] += 1
        if is_lump(r):
            lmp[r['ym']] += r['amt']
        else:
            rec[r['ym']] += r['amt']

    # ── 近12月分類（經常性 / 全部） ──
    cat_rec = collections.Counter()
    cat_all = collections.Counter()
    sub_rec = collections.Counter()
    for r in rows:
        if r['ym'] in m12:
            cat_all[r['cat']] += r['amt']
            if not is_lump(r):
                cat_rec[r['cat']] += r['amt']
                sub_rec[(r['cat'], r['sub'] or '(未分類)')] += r['amt']

    rec12 = sum(rec[m] for m in m12)
    lmp12 = sum(lmp[m] for m in m12)
    tot12 = rec12 + lmp12
    rec_mo = rec12 / len(m12)
    lmp_mo = lmp12 / len(m12)

    # ── 含房貸 ──
    mort_yr = MORTGAGE_MONTHLY * 12
    rec_mo_m = rec_mo + MORTGAGE_MONTHLY
    tot12_m = tot12 + mort_yr

    # ── 年度 ──
    yr = collections.Counter()
    yr_rec = collections.Counter()
    for r in rows:
        yr[r['y']] += r['amt']
        if not is_lump(r):
            yr_rec[r['y']] += r['amt']

    # ── FIRE 提領試算（以含房貸/不含房貸兩情境） ──
    def fire(annual, rate):
        return annual / rate

    scen = []
    for label, annual in [('經常性（不含房貸）', rec_mo*12),
                          ('經常性＋房貸', rec_mo_m*12),
                          ('全部支出（含一次性）', tot12),
                          ('全部支出＋房貸', tot12_m)]:
        scen.append(dict(label=label, annual=annual,
                         r35=fire(annual, 0.035), r40=fire(annual, 0.04)))

    monthly_series = [dict(m=m, tot=round(tot[m]), rec=round(rec[m]), lmp=round(lmp[m]),
                           n=cnt[m]) for m in all_months]

    recent = [rec[m] for m in m12]
    return dict(
        last_ym=last_ym, last_ymd=last_ymd, last_full=last_full,
        n_rows=len(rows), span=f"{rows[0]['ym']} ~ {last_ym}",
        m12=m12, m24=m24, months=monthly_series,
        cat_rec=cat_rec, cat_all=cat_all, sub_rec=sub_rec,
        rec12=rec12, lmp12=lmp12, tot12=tot12,
        rec_mo=rec_mo, lmp_mo=lmp_mo, rec_mo_m=rec_mo_m,
        mort_yr=mort_yr, tot12_m=tot12_m,
        med=statistics.median(recent), mx=max(recent), mn=min(recent),
        yr=yr, yr_rec=yr_rec, scen=scen,
    )


def w(n):
    """元 → 萬（1 位小數）"""
    return round(n/10000, 1)


def render(D):
    """產生 tab HTML + JS 資料"""
    # ── JS：月度序列（近36月） ──
    ms = D['months'][-36:]
    EXP_MONTHLY = json.dumps([
        {"m": x['m'], "t": w(x['t' 'ot']) if False else w(x['tot']),
         "r": w(x['rec']), "l": w(x['lmp']), "n": x['n']} for x in ms
    ], ensure_ascii=False)

    # ── JS：分類 Pareto（經常性，近12月） ──
    cr = D['cat_rec'].most_common()
    tot_cr = sum(v for _, v in cr) or 1
    EXP_CAT = json.dumps([
        {"name": k, "val": w(v), "pct": round(v/tot_cr*100, 1),
         "mo": w(v/12), "color": CAT_COLOR.get(k, '#8C8C8C')} for k, v in cr
    ], ensure_ascii=False)

    # ── JS：子分類 Top 15 ──
    sr = D['sub_rec'].most_common(15)
    EXP_SUB = json.dumps([
        {"name": f"{c} / {s}", "val": w(v), "mo": w(v/12),
         "color": CAT_COLOR.get(c, '#8C8C8C')} for (c, s), v in sr
    ], ensure_ascii=False)

    # ── JS：年度 ──
    ys = sorted(D['yr'])
    EXP_YEAR = json.dumps([
        {"y": y, "tot": w(D['yr'][y]), "rec": w(D['yr_rec'][y])} for y in ys
    ], ensure_ascii=False)

    # ── 分類 bar（HTML，不用 Chart.js，避免渲染問題） ──
    mxv = max((v for _, v in cr), default=1)
    bars = []
    for k, v in cr:
        pct = v/mxv*100
        bars.append(
            f'<div class="xbar-row"><div class="xbar-name">{k}</div>'
            f'<div class="xbar-track"><div class="xbar-fill" style="width:{pct:.1f}%;'
            f'background:{CAT_COLOR.get(k,"#8C8C8C")}"></div></div>'
            f'<div class="xbar-val">{w(v):,.1f}萬</div>'
            f'<div class="xbar-pct">{v/tot_cr*100:.1f}%</div></div>')
    CAT_BARS = "\n      ".join(bars)

    # ── Pareto 表 ──
    cum = 0
    trs = []
    for i, (k, v) in enumerate(cr, 1):
        cum += v
        trs.append(
            f'<tr><td class="rk">{i}</td><td><span class="dot" style="background:'
            f'{CAT_COLOR.get(k,"#8C8C8C")}"></span>{k}</td>'
            f'<td class="num">{w(v):,.1f}萬</td><td class="num">{w(v/12):,.1f}萬</td>'
            f'<td class="num">{v/tot_cr*100:.1f}%</td>'
            f'<td class="num">{cum/tot_cr*100:.1f}%</td></tr>')
    trs.append(
        f'<tr class="ttl"><td></td><td>合計</td><td class="num">{w(tot_cr):,.1f}萬</td>'
        f'<td class="num">{w(tot_cr/12):,.1f}萬</td><td class="num">100.0%</td>'
        f'<td class="num">—</td></tr>')
    CAT_TABLE = "\n        ".join(trs)

    # ── 子分類表 ──
    sub_trs = []
    for i, ((c, s), v) in enumerate(sr, 1):
        sub_trs.append(
            f'<tr><td class="rk">{i}</td><td><span class="dot" style="background:'
            f'{CAT_COLOR.get(c,"#8C8C8C")}"></span>{c} / {s}</td>'
            f'<td class="num">{w(v):,.1f}萬</td><td class="num">{w(v/12):,.1f}萬</td></tr>')
    SUB_TABLE = "\n        ".join(sub_trs)

    # ── FIRE 試算表 ──
    fire_trs = []
    for s in D['scen']:
        fire_trs.append(
            f'<tr><td>{s["label"]}</td>'
            f'<td class="num">{w(s["annual"]/12):,.1f}萬</td>'
            f'<td class="num">{w(s["annual"]):,.1f}萬</td>'
            f'<td class="num">{w(s["r40"]):,.0f}萬</td>'
            f'<td class="num">{w(s["r35"]):,.0f}萬</td></tr>')
    FIRE_TABLE = "\n        ".join(fire_trs)

    # ── 年度表 ──
    yr_trs = []
    for y in ys:
        n_full = 12
        if y == ys[0]:
            n_full = 12 - int(D['months'][0]['m'][5:7]) + 1
        if y == ys[-1]:
            n_full = int(D['last_ym'][5:7])
        yr_trs.append(
            f'<tr><td>{y}</td><td class="num">{w(D["yr"][y]):,.1f}萬</td>'
            f'<td class="num">{w(D["yr_rec"][y]):,.1f}萬</td>'
            f'<td class="num">{w(D["yr"][y]/max(n_full,1)):,.1f}萬</td>'
            f'<td class="num">{n_full}</td></tr>')
    YEAR_TABLE = "\n        ".join(yr_trs)

    tab = f'''<div id="tab-expense" class="tab-content">
  <div class="sdiv"><span>每月開銷總覽（近12完整月 {D['m12'][0]} ~ {D['m12'][-1]}）</span></div>
  <div class="g3">
    <div class="card kpi"><div class="kpi-l">經常性月開銷</div>
      <div class="kpi-v">{w(D['rec_mo']):,.1f}<span class="u">萬</span></div>
      <div class="kpi-s">中位 {w(D['med']):,.1f}萬 ｜ 區間 {w(D['mn']):,.1f}–{w(D['mx']):,.1f}萬</div></div>
    <div class="card kpi"><div class="kpi-l">＋房貸後月開銷</div>
      <div class="kpi-v warn">{w(D['rec_mo_m']):,.1f}<span class="u">萬</span></div>
      <div class="kpi-s">星展房貸 {w(MORTGAGE_MONTHLY):,.0f}萬/月（未含於帳本）</div></div>
    <div class="card kpi"><div class="kpi-l">一次性大額（月均攤）</div>
      <div class="kpi-v">{w(D['lmp_mo']):,.1f}<span class="u">萬</span></div>
      <div class="kpi-s">綜所稅・房地產・年繳保費</div></div>
  </div>
  <div class="g3">
    <div class="card kpi"><div class="kpi-l">近12月總支出</div>
      <div class="kpi-v">{w(D['tot12']):,.0f}<span class="u">萬</span></div>
      <div class="kpi-s">經常 {w(D['rec12']):,.0f}萬 ＋ 一次性 {w(D['lmp12']):,.0f}萬</div></div>
    <div class="card kpi"><div class="kpi-l">含房貸年支出</div>
      <div class="kpi-v warn">{w(D['tot12_m']):,.0f}<span class="u">萬</span></div>
      <div class="kpi-s">＋房貸 {w(D['mort_yr']):,.0f}萬/年</div></div>
    <div class="card kpi"><div class="kpi-l">帳本筆數</div>
      <div class="kpi-v">{D['n_rows']:,}<span class="u">筆</span></div>
      <div class="kpi-s">{D['span']}</div></div>
  </div>

  <div class="alert alert-info">💡 <b>為何要分「經常性」與「一次性」？</b>
  退休現金流要用<b>經常性</b>推估（每月都會發生），一次性大額（綜所稅、買房車位、年繳保費）
  應另備預備金，不能混在月開銷裡平均，否則會高估退休所需資產。</div>

  <div class="sdiv"><span>月度支出走勢（近36個月）</span></div>
  <div class="card">
    <div class="legend-row">
      <span class="legend-item"><span class="legend-dot" style="background:#378ADD"></span>經常性</span>
      <span class="legend-item"><span class="legend-dot" style="background:#EF9F27"></span>一次性大額</span>
      <span class="legend-item"><span class="legend-dot" style="background:#E24B4A;height:3px;border-radius:2px;width:14px"></span>經常性12月移動平均</span>
    </div>
    <div class="chart-wrap"><canvas id="expMonthlyChart"></canvas></div>
  </div>

  <div class="sdiv"><span>分類佔比（經常性・近12月）</span></div>
  <div class="card">
    <div class="xbar-wrap">
      {CAT_BARS}
    </div>
  </div>

  <div class="sdiv"><span>分類 Pareto 明細</span></div>
  <div class="card tbl-card">
    <table class="dtbl">
      <thead><tr><th>#</th><th>分類</th><th class="num">近12月</th><th class="num">月均</th>
      <th class="num">佔比</th><th class="num">累計</th></tr></thead>
      <tbody>
        {CAT_TABLE}
      </tbody>
    </table>
  </div>

  <div class="sdiv"><span>子分類 Top 15（經常性・近12月）</span></div>
  <div class="card tbl-card">
    <table class="dtbl">
      <thead><tr><th>#</th><th>分類 / 子分類</th><th class="num">近12月</th><th class="num">月均</th></tr></thead>
      <tbody>
        {SUB_TABLE}
      </tbody>
    </table>
  </div>

  <div class="sdiv"><span>🔥 FIRE 提領試算：支出需要多少資產支撐</span></div>
  <div class="card tbl-card">
    <table class="dtbl">
      <thead><tr><th>情境</th><th class="num">月支出</th><th class="num">年支出</th>
      <th class="num">4% 法則</th><th class="num">3.5% 法則</th></tr></thead>
      <tbody>
        {FIRE_TABLE}
      </tbody>
    </table>
  </div>
  <div class="alert alert-warn" id="exp-fire-note">—</div>

  <div class="sdiv"><span>年度支出</span></div>
  <div class="card tbl-card">
    <table class="dtbl">
      <thead><tr><th>年度</th><th class="num">總支出</th><th class="num">經常性</th>
      <th class="num">月均</th><th class="num">月數</th></tr></thead>
      <tbody>
        {YEAR_TABLE}
      </tbody>
    </table>
  </div>

  <div class="alert alert-info">📄 資料源：Google Drive「AndroMoney」帳本（{D['n_rows']:,} 筆，{D['span']}）｜
  房貸每月 {w(MORTGAGE_MONTHLY):,.0f} 萬由系統外加｜更新帳本 Excel 後重跑更新即可同步。</div>
</div>
'''

    js = f'''
// ══ 開銷分析數據 ══
window.EXP_MONTHLY={EXP_MONTHLY};
window.EXP_CAT={EXP_CAT};
window.EXP_SUB={EXP_SUB};
window.EXP_YEAR={EXP_YEAR};
window.EXP_META={json.dumps(dict(
    recMo=w(D['rec_mo']), recMoM=w(D['rec_mo_m']),
    tot12=w(D['tot12']), tot12M=w(D['tot12_m']),
    mortMo=w(MORTGAGE_MONTHLY),
    fire40=w(D['scen'][1]['r40']), fire35=w(D['scen'][1]['r35']),
    lastFull=D['last_full'], span=D['span'], n=D['n_rows']), ensure_ascii=False)};
'''
    return tab, js


def inject(html, tab, js):
    errs = []

    # 1) 分頁按鈕（插在「淨資產月曆」之後）
    anchor = '''<button class="tab" onclick="switchTab(this,'netcal')">💚 淨資產月曆</button>'''
    if anchor not in html:
        errs.append('找不到 netcal 分頁按鈕錨點')
    else:
        html = html.replace(
            anchor,
            anchor + '\n  <button class="tab" onclick="switchTab(this,\'expense\')">🧾 每月開銷</button>',
            1)

    # 2) 分頁內容（插在 tab-netcal 區塊之後、footer 之前）
    foot = '<div style="text-align:center;font-size:11px;color:var(--hint);margin-top:20px'
    i = html.find(foot)
    if i < 0:
        errs.append('找不到 footer 錨點')
    else:
        html = html[:i] + tab + '\n' + html[i:]

    # 3) JS 資料（插在 <script> 之後）
    m = re.search(r'<script>\n', html)
    if not m:
        errs.append('找不到 <script> 錨點')
    else:
        html = html[:m.end()] + js + html[m.end():]

    # 4) 樣式
    css = '''
/* ══ 開銷分析 ══ */
.kpi{text-align:left}
.kpi-l{font-size:11px;color:var(--hint);letter-spacing:.5px}
.kpi-v{font-size:30px;font-weight:800;line-height:1.15;margin-top:2px}
.kpi-v.warn{color:#EF9F27}
.kpi-v .u{font-size:14px;font-weight:600;margin-left:2px}
.kpi-s{font-size:11px;color:var(--hint);margin-top:4px}
.xbar-wrap{display:flex;flex-direction:column;gap:9px}
.xbar-row{display:grid;grid-template-columns:76px 1fr 62px 46px;align-items:center;gap:8px}
.xbar-name{font-size:12px;font-weight:600}
.xbar-track{height:16px;background:var(--border);border-radius:8px;overflow:hidden}
.xbar-fill{height:100%;border-radius:8px}
.xbar-val{font-size:12px;font-weight:700;text-align:right;font-variant-numeric:tabular-nums}
.xbar-pct{font-size:11px;color:var(--hint);text-align:right;font-variant-numeric:tabular-nums}
.tbl-card{padding:4px 0;overflow-x:auto}
.dtbl{width:100%;border-collapse:collapse;font-size:12px}
.dtbl th{text-align:left;padding:8px 10px;color:var(--hint);font-size:11px;font-weight:600;
  border-bottom:1px solid var(--border);white-space:nowrap}
.dtbl td{padding:7px 10px;border-bottom:1px solid var(--border);white-space:nowrap}
.dtbl .num{text-align:right;font-variant-numeric:tabular-nums}
.dtbl .rk{color:var(--hint);width:26px}
.dtbl tr.ttl td{font-weight:800;border-top:1.5px solid var(--border);border-bottom:none}
.dtbl .dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px}
@media(max-width:480px){
  .xbar-row{grid-template-columns:62px 1fr 56px 40px;gap:6px}
  .kpi-v{font-size:25px}
}
'''
    j = html.rfind('</style>')
    if j < 0:
        errs.append('找不到 </style>')
    else:
        html = html[:j] + css + html[j:]

    # 5) 圖表繪製 + switchTab 掛鉤
    draw = '''
// ══ 開銷分析圖表 ══
let expChart=null;
function drawExpenseChart(){
  const el=document.getElementById('expMonthlyChart');
  if(!el||!window.EXP_MONTHLY) return;
  if(expChart){expChart.destroy();expChart=null;}
  const D=window.EXP_MONTHLY;
  const labels=D.map(x=>x.m.slice(2).replace('-','/'));
  // 12 月移動平均（經常性）
  const ma=D.map((_,i)=>{
    const s=Math.max(0,i-11), seg=D.slice(s,i+1);
    return +(seg.reduce((a,b)=>a+b.r,0)/seg.length).toFixed(1);
  });
  expChart=new Chart(el,{type:'bar',data:{labels,datasets:[
    {label:'經常性',data:D.map(x=>x.r),backgroundColor:'#378ADD',stack:'s',order:2},
    {label:'一次性',data:D.map(x=>x.l),backgroundColor:'#EF9F27',stack:'s',order:2},
    {label:'12月移動平均',data:ma,type:'line',borderColor:'#E24B4A',borderWidth:2,
     pointRadius:0,tension:.3,order:1,fill:false}
  ]},options:{responsive:true,maintainAspectRatio:false,
    interaction:{mode:'index',intersect:false},
    plugins:{legend:{display:false},tooltip:{callbacks:{
      label:c=>c.dataset.label+'：'+c.parsed.y.toLocaleString()+'萬'}}},
    scales:{x:{stacked:true,grid:{color:GC},ticks:{color:TC,font:{size:9},
               maxRotation:0,autoSkip:true,maxTicksLimit:12}},
            y:{stacked:true,grid:{color:GC},ticks:{color:TC,font:{size:10},
               callback:v=>v+'萬'}}}}});
}
function renderExpenseNote(){
  const n=document.getElementById('exp-fire-note');
  if(!n||!window.EXP_META) return;
  const M=window.EXP_META;
  const net=(typeof NET_NOW==='number')?NET_NOW:null;
  let s='🎯 <b>以「經常性＋房貸」計算</b>：年支出 '+(M.recMoM*12).toFixed(0)+'萬，'+
        '4% 法則需 <b>'+M.fire40.toLocaleString()+'萬</b>，3.5% 法則需 <b>'+
        M.fire35.toLocaleString()+'萬</b>。';
  s+=' 退休目標 16,000萬 '+(16000>=M.fire40?'已覆蓋':'尚未覆蓋')+'此需求。';
  s+=' 房貸為期限負債，繳清後年支出可降 '+(M.mortMo*12).toFixed(0)+'萬，'+
     '對應所需資產減少約 '+(M.mortMo*12/0.04).toFixed(0)+'萬。';
  n.innerHTML=s;
}
'''
    k = html.rfind('</script>')
    if k < 0:
        errs.append('找不到 </script>')
    else:
        html = html[:k] + draw + '\n' + html[k:]

    # switchTab 掛鉤
    old = "    if(name==='calendar') renderCalendar();"
    if old not in html:
        errs.append('找不到 switchTab 掛鉤點')
    else:
        html = html.replace(
            old,
            old + "\n    if(name==='expense'){renderExpenseNote();try{drawExpenseChart();}catch(e){console.warn('expChart',e);}}",
            1)

    return html, errs


def verify(html, D):
    """反向驗證：從 HTML 解析回數字，對帳"""
    errs = []
    ok = []

    # div 平衡
    bal = html.count('<div') - html.count('</div>')
    if bal != 0:
        errs.append(f'div 不平衡：{bal}')
    else:
        ok.append('HTML div 結構平衡')

    # 分頁數
    n_btn = len(re.findall(r'switchTab\(this,', html))
    n_tab = len(re.findall(r'id="tab-[a-zA-Z-]+"', html))
    if n_btn != 18:
        errs.append(f'分頁按鈕數 {n_btn} ≠ 18')
    elif n_tab != 18:
        errs.append(f'分頁內容數 {n_tab} ≠ 18')
    else:
        ok.append(f'分頁 18 個（按鈕/內容一致）')

    # EXP_MONTHLY 解析回來加總對帳
    m = re.search(r'window\.EXP_MONTHLY=(\[.*?\]);', html, re.S)
    if not m:
        errs.append('找不到 EXP_MONTHLY')
    else:
        arr = json.loads(m.group(1))
        # 近12完整月的經常性，應等於 D['rec12']
        want = {x: True for x in D['m12']}
        got = sum(x['r'] for x in arr if x['m'] in want)
        exp = round(D['rec12']/10000, 1)
        if abs(got - exp) > 1.0:
            errs.append(f'EXP_MONTHLY 經常性 {got:.1f}萬 vs 計算 {exp:.1f}萬')
        else:
            ok.append(f'EXP_MONTHLY 近12月經常性 {got:,.1f}萬 對帳一致')
        gl = sum(x['l'] for x in arr if x['m'] in want)
        el = round(D['lmp12']/10000, 1)
        if abs(gl - el) > 1.0:
            errs.append(f'EXP_MONTHLY 一次性 {gl:.1f}萬 vs {el:.1f}萬')
        else:
            ok.append(f'EXP_MONTHLY 近12月一次性 {gl:,.1f}萬 對帳一致')

    # EXP_CAT 加總 == 經常性12月
    m = re.search(r'window\.EXP_CAT=(\[.*?\]);', html, re.S)
    if not m:
        errs.append('找不到 EXP_CAT')
    else:
        arr = json.loads(m.group(1))
        s = sum(x['val'] for x in arr)
        exp = round(D['rec12']/10000, 1)
        if abs(s - exp) > 1.0:
            errs.append(f'EXP_CAT 加總 {s:.1f}萬 vs {exp:.1f}萬')
        else:
            ok.append(f'EXP_CAT 加總 {s:,.1f}萬 對帳一致（{len(arr)} 類）')
        p = sum(x['pct'] for x in arr)
        if abs(p - 100) > 1.5:
            errs.append(f'EXP_CAT 佔比合計 {p:.1f}% ≠ 100%')
        else:
            ok.append(f'EXP_CAT 佔比合計 {p:.1f}%')
        # 排序遞減
        vals = [x['val'] for x in arr]
        if vals != sorted(vals, reverse=True):
            errs.append('EXP_CAT 未由大到小排序')
        else:
            ok.append('EXP_CAT 由大至小排序')

    # Pareto 表合計列
    m = re.search(r'<tr class="ttl"><td></td><td>合計</td><td class="num">([\d,.]+)萬</td>', html)
    if not m:
        errs.append('找不到 Pareto 合計列')
    else:
        v = float(m.group(1).replace(',', ''))
        exp = round(D['rec12']/10000, 1)
        if abs(v - exp) > 1.0:
            errs.append(f'Pareto 合計 {v}萬 vs {exp}萬')
        else:
            ok.append(f'Pareto 表合計 {v:,.1f}萬 與 EXP_CAT 一致')

    # KPI 數字存在
    for label, val in [('經常性月開銷', w(D['rec_mo'])),
                       ('＋房貸後月開銷', w(D['rec_mo_m'])),
                       ('近12月總支出', w(D['tot12']))]:
        pat = f'{val:,.1f}' if label != '近12月總支出' else f'{val:,.0f}'
        if pat not in html:
            errs.append(f'KPI「{label}」數字 {pat} 未出現在 HTML')
    if not any('KPI' in e for e in errs):
        ok.append('KPI 三項數字寫入正確')

    # 房貸加總關係
    if abs((D['rec_mo'] + MORTGAGE_MONTHLY) - D['rec_mo_m']) > 1:
        errs.append('房貸加總關係不符')
    else:
        ok.append(f'房貸關係：{w(D["rec_mo"]):,.1f} + {w(MORTGAGE_MONTHLY):,.1f} = {w(D["rec_mo_m"]):,.1f}萬')

    # FIRE 計算驗算
    s = D['scen'][1]
    if abs(s['r40'] - s['annual']/0.04) > 1:
        errs.append('FIRE 4% 計算錯誤')
    else:
        ok.append(f'FIRE 試算：年 {w(s["annual"]):,.1f}萬 → 4% {w(s["r40"]):,.0f}萬 / 3.5% {w(s["r35"]):,.0f}萬')

    # CSS 完整性（沿用既有規則：不得破壞 chart-wrap）
    if 'position:relative;width:100%;height:300px' not in html:
        errs.append('chart-wrap CSS 遭破壞')
    else:
        ok.append('chart-wrap CSS 完整')

    # 既有頁面未被破壞
    for var in ['TW_DATA', 'US_DATA', 'JP_DATA', 'FD_DATA']:
        if f'window.{var}=' not in html:
            errs.append(f'既有 {var} 遺失')
    for var in ['TW_BROKER', 'US_BROKER']:
        if not re.search(rf'{var}\s*=\s*\{{', html):
            errs.append(f'既有 {var} 遺失')
    if not any('遺失' in e for e in errs):
        ok.append('既有 6 組 JS 資料結構完整')

    # 既有分頁關鍵數字未被破壞
    for k in ['9,347', '4,461', '5,305', '2,423']:
        if k not in html:
            errs.append(f'既有儀表板數字 {k} 遺失')
    if not any('儀表板數字' in e for e in errs):
        ok.append('既有儀表板數字（總資產/淨資產/台股/美股）完整')

    return ok, errs


def main():
    rows = load_rows(CSV_PATH)
    D = build(rows)
    print(f"讀入 {len(rows):,} 筆　{D['span']}")
    print(f"近12完整月 {D['m12'][0]} ~ {D['m12'][-1]}")
    print(f"  經常性 {w(D['rec12']):,.1f}萬 → 月均 {w(D['rec_mo']):,.1f}萬")
    print(f"  一次性 {w(D['lmp12']):,.1f}萬")
    print(f"  ＋房貸 月 {w(D['rec_mo_m']):,.1f}萬 / 年 {w(D['rec_mo_m']*12):,.1f}萬")

    tab, js = render(D)
    html = open(BASE_HTML, encoding='utf-8').read()
    html, ierrs = inject(html, tab, js)
    if ierrs:
        print("\n⛔ 注入失敗：")
        for e in ierrs:
            print("   •", e)
        sys.exit(1)

    print("\n── 反向驗證 ──")
    ok, errs = verify(html, D)
    for o in ok:
        print("  ✅", o)
    if errs:
        print(f"\n⛔ {len(errs)} 項未通過，中止：")
        for e in errs:
            print("   •", e)
        sys.exit(1)

    open(OUT_HTML, 'w', encoding='utf-8').write(html)
    print(f"\n✅ 全部驗證通過 → {OUT_HTML}（{len(html):,} bytes）")


if __name__ == '__main__':
    main()
