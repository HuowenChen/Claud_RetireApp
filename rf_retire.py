#!/usr/bin/env python3
"""
退休倒數時間表分頁產生器
退休日：2029-03-31（RETIRE_DATE）

設計重點：
  1. 倒數天數由瀏覽器端 JS 即時計算，不用每天重跑腳本也不會過期
  2. 里程碑與所需報酬率由當期總資產推算，每次更新自動重算
  3. 退休後現金流引用開銷分析頁的經常性支出，兩頁數字一致
"""
import datetime, math

RETIRE_DATE = datetime.date(2029, 3, 31)
TRACK_START = datetime.date(2026, 3, 24)   # 資產歷史紀錄起點
TARGET = 160_000_000                        # 總資產目標
MORTGAGE_MONTHLY = 160_000                  # 星展房貸月付（與開銷頁一致）
EXP_RECURRING_MO = 333_000                  # 經常性月開銷（開銷分析頁近12月均值）

C_OK, C_WARN, C_BAD, C_BLUE = "#1D9E75", "#EF9F27", "#E24B4A", "#378ADD"


def w(n):
    return round(n / 10000)


def w1(n):
    return round(n / 10000, 1)


def build(GD, today=None):
    """GD: rf_update.py 的 GD dict。回傳 (tab_html, info)"""
    today = today or datetime.date.today()
    cur = GD['total']
    net = GD['total'] - GD['debt']
    div_yr = GD['div']

    days = (RETIRE_DATE - today).days
    yrs = days / 365.25
    months = round(yrs * 12)
    elapsed = (today - TRACK_START).days
    span = (RETIRE_DATE - TRACK_START).days
    prog = max(0.0, min(100.0, elapsed / span * 100))

    gap = TARGET - cur
    cagr = ((TARGET / cur) ** (1 / yrs) - 1) if (yrs > 0 and cur > 0) else 0
    lin_mo = gap / months if months else 0

    # 追蹤以來實際年化
    base_v = 63_996_301.06   # 2026-03-24 總資產
    el_y = elapsed / 365.25
    actual = ((cur / base_v) ** (1 / el_y) - 1) if el_y > 0 else 0

    # ── 季度里程碑（依所需 CAGR 路徑）──
    miles = []
    d = today
    q_ends = []
    y, q = today.year, (today.month - 1) // 3 + 1
    while True:
        qm = q * 3
        last = datetime.date(y, qm, 1)
        # 該季最後一天
        nm = datetime.date(y + (qm // 12), (qm % 12) + 1, 1)
        last = nm - datetime.timedelta(days=1)
        if last > RETIRE_DATE:
            q_ends.append(RETIRE_DATE)
            break
        if last > today:
            q_ends.append(last)
        q += 1
        if q == 5:
            q, y = 1, y + 1
        if len(q_ends) > 16:
            break

    for qd in q_ends:
        t = (qd - today).days / 365.25
        need = cur * ((1 + cagr) ** t)
        miles.append(dict(date=qd, need=need,
                          label=f"{qd.year}Q{(qd.month-1)//3+1}",
                          is_final=(qd == RETIRE_DATE)))

    # ── 退休後現金流 ──
    exp_yr = (EXP_RECURRING_MO + MORTGAGE_MONTHLY) * 12
    exp_yr_nomort = EXP_RECURRING_MO * 12
    cover = div_yr / exp_yr * 100 if exp_yr else 0
    need_40 = exp_yr / 0.04
    need_35 = exp_yr / 0.035
    need_40_nm = exp_yr_nomort / 0.04

    info = dict(days=days, months=months, yrs=yrs, prog=prog, gap=gap,
                cagr=cagr, lin_mo=lin_mo, actual=actual, cur=cur, net=net,
                miles=miles, exp_yr=exp_yr, cover=cover,
                need_40=need_40, need_35=need_35)

    # ── KPI ──
    yy, mm = days // 365, (days % 365) // 30
    kpi = f'''  <div class="g3">
    <div class="metric"><div class="metric-label">距離退休</div>
      <div class="metric-value" id="rc-days" style="color:{C_BLUE}">{days:,}<span style="font-size:12px;color:var(--muted)">天</span></div>
      <div class="metric-sub" id="rc-ym">{yy} 年 {mm} 個月 ｜ {RETIRE_DATE:%Y/%m/%d}</div></div>
    <div class="metric"><div class="metric-label">目標缺口</div>
      <div class="metric-value warn">{w(gap):,}<span style="font-size:12px;color:var(--muted)">萬</span></div>
      <div class="metric-sub">目前 {w(cur):,}萬 / 目標 16,000萬</div></div>
    <div class="metric"><div class="metric-label">所需年化報酬</div>
      <div class="metric-value" style="color:{C_BAD if cagr>0.15 else C_OK}">{cagr*100:.1f}<span style="font-size:12px;color:var(--muted)">%</span></div>
      <div class="metric-sub">追蹤以來實際 {actual*100:.0f}%</div></div>
  </div>'''

    # ── 進度條 ──
    bar = f'''  <div class="card">
    <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px">
      <div class="stitle" style="margin-bottom:0">退休倒數進度</div>
      <div style="font-size:12px;color:var(--muted)">{TRACK_START:%Y/%m/%d} → {RETIRE_DATE:%Y/%m/%d}</div>
    </div>
    <div style="background:var(--bg);border-radius:7px;height:26px;overflow:hidden;position:relative">
      <div id="rc-bar" style="background:linear-gradient(90deg,{C_BLUE},{C_OK});width:{prog:.1f}%;height:100%;border-radius:7px"></div>
      <div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700" id="rc-bar-t">已過 {prog:.1f}%</div>
    </div>
    <div style="display:flex;justify-content:space-between;font-size:11px;color:var(--hint);margin-top:5px">
      <span>已追蹤 {elapsed:,} 天</span><span>剩餘 {days:,} 天</span>
    </div>
  </div>'''

    # ── 資產軌道里程碑 ──
    rows = []
    for m in miles:
        need = m['need']
        pct = need / TARGET * 100
        tag = ('<span style="background:%s;color:#fff;padding:2px 7px;border-radius:99px;font-size:10px;font-weight:700">退休</span>' % C_BAD) if m['is_final'] else ''
        rows.append(f'''        <tr><td style="padding:7px 8px;font-weight:600">{m['label']} {tag}</td>
          <td style="padding:7px 8px;font-size:11px;color:var(--muted)">{m['date']:%Y/%m/%d}</td>
          <td style="padding:7px 8px;text-align:right;font-weight:600">{w(need):,}萬</td>
          <td style="padding:7px 8px;text-align:right;color:var(--muted)">{pct:.0f}%</td>
          <td style="padding:7px 8px"><div style="background:var(--bg);border-radius:4px;height:14px;overflow:hidden"><div style="background:{C_BLUE};width:{min(pct,100):.1f}%;height:100%"></div></div></td></tr>''')

    track = f'''  <div class="card">
    <div class="stitle">資產軌道里程碑（依所需年化 {cagr*100:.1f}% 推算）</div>
    <div style="overflow-x:auto"><table class="tbl">
      <thead><tr><th>季度</th><th>日期</th><th style="text-align:right">應達總資產</th><th style="text-align:right">達成率</th><th style="width:34%">進度</th></tr></thead>
      <tbody>
{chr(10).join(rows)}
      </tbody>
    </table></div>
    <div class="alert alert-warn" style="margin-top:10px">⚠️ 所需年化 <b>{cagr*100:.1f}%</b> 遠高於長期股市合理預期（7–10%）。
    追蹤以來實際年化 {actual*100:.0f}% 來自 2026 年的多頭與槓桿部位，<b>不應假設能延續</b>。
    若年化僅 10%，2029/3/31 約可達 {w(cur*(1.10**yrs)):,}萬；若 15% 約 {w(cur*(1.15**yrs)):,}萬。</div>
  </div>'''

    # ── 情境試算 ──
    sc = []
    for r in [0.05, 0.08, 0.10, 0.15, 0.20, cagr]:
        v = cur * ((1 + r) ** yrs)
        hit = v >= TARGET
        lbl = f"{r*100:.1f}%" + ("（所需）" if abs(r - cagr) < 1e-9 else "")
        sc.append(f'''        <tr><td style="padding:7px 8px;font-weight:600">{lbl}</td>
          <td style="padding:7px 8px;text-align:right;font-weight:600;color:{C_OK if hit else 'var(--text)'}">{w(v):,}萬</td>
          <td style="padding:7px 8px;text-align:right;color:{C_OK if hit else C_WARN}">{v/TARGET*100:.0f}%</td>
          <td style="padding:7px 8px;text-align:right;color:{C_OK if hit else C_BAD}">{'達標' if hit else f'差 {w(TARGET-v):,}萬'}</td></tr>''')

    scen = f'''  <div class="card">
    <div class="stitle">退休日資產情境（{RETIRE_DATE:%Y/%m/%d}，{yrs:.2f} 年後）</div>
    <div style="overflow-x:auto"><table class="tbl">
      <thead><tr><th>年化報酬</th><th style="text-align:right">屆時總資產</th><th style="text-align:right">達成率</th><th style="text-align:right">vs 目標</th></tr></thead>
      <tbody>
{chr(10).join(sc)}
      </tbody>
    </table></div>
  </div>'''

    # ── 退休後現金流 ──
    cash = f'''  <div class="card">
    <div class="stitle">退休後現金流檢核</div>
    <div style="overflow-x:auto"><table class="tbl">
      <thead><tr><th>項目</th><th style="text-align:right">年</th><th style="text-align:right">月</th><th>說明</th></tr></thead>
      <tbody>
        <tr><td style="padding:7px 8px;font-weight:600">經常性開銷</td>
          <td style="padding:7px 8px;text-align:right">{w1(EXP_RECURRING_MO*12)}萬</td>
          <td style="padding:7px 8px;text-align:right">{w1(EXP_RECURRING_MO)}萬</td>
          <td style="padding:7px 8px;font-size:11px;color:var(--muted)">取自開銷分析頁近12月</td></tr>
        <tr><td style="padding:7px 8px;font-weight:600">＋房貸本息</td>
          <td style="padding:7px 8px;text-align:right">{w1(MORTGAGE_MONTHLY*12)}萬</td>
          <td style="padding:7px 8px;text-align:right">{w1(MORTGAGE_MONTHLY)}萬</td>
          <td style="padding:7px 8px;font-size:11px;color:var(--muted)">期限負債，繳清後消失</td></tr>
        <tr style="border-top:1.5px solid var(--border)"><td style="padding:7px 8px;font-weight:800">退休後年支出</td>
          <td style="padding:7px 8px;text-align:right;font-weight:800;color:{C_WARN}">{w1(exp_yr)}萬</td>
          <td style="padding:7px 8px;text-align:right;font-weight:800">{w1(exp_yr/12)}萬</td>
          <td style="padding:7px 8px;font-size:11px;color:var(--muted)">含房貸</td></tr>
        <tr><td style="padding:7px 8px;font-weight:600">目前年配息</td>
          <td style="padding:7px 8px;text-align:right;color:{C_OK}">{w1(div_yr)}萬</td>
          <td style="padding:7px 8px;text-align:right">{w1(div_yr/12)}萬</td>
          <td style="padding:7px 8px;font-size:11px;color:var(--muted)">覆蓋 {cover:.0f}% 的年支出</td></tr>
        <tr><td style="padding:7px 8px;font-weight:600">4% 法則所需資產</td>
          <td style="padding:7px 8px;text-align:right;font-weight:600">{w(need_40):,}萬</td>
          <td style="padding:7px 8px;text-align:right">—</td>
          <td style="padding:7px 8px;font-size:11px;color:var(--muted)">{'目標 16,000萬 已覆蓋' if TARGET>=need_40 else '目標不足'}</td></tr>
        <tr><td style="padding:7px 8px;font-weight:600">3.5% 法則所需資產</td>
          <td style="padding:7px 8px;text-align:right;font-weight:600">{w(need_35):,}萬</td>
          <td style="padding:7px 8px;text-align:right">—</td>
          <td style="padding:7px 8px;font-size:11px;color:var(--muted)">{'目標 16,000萬 已覆蓋' if TARGET>=need_35 else f'目標差 {w(need_35-TARGET):,}萬'}</td></tr>
      </tbody>
    </table></div>
    <div class="alert alert-info" style="margin-top:10px">💡 退休後還有 30+ 年要支應（三個小孩仍在教育期），<b>3.5% 法則比 4% 保守合理</b>。
    房貸繳清後年支出降 {w1(MORTGAGE_MONTHLY*12)}萬，對應所需資產減少約 {w(MORTGAGE_MONTHLY*12/0.04):,}萬。</div>
  </div>'''

    # ── 行動時間軸 ──
    tl_items = [
        ("2026 Q4", "現在", C_BLUE, "持續累積；配息年化 %s萬，距 360 萬目標仍有缺口" % w1(div_yr)),
        ("2027", "資產衝刺期", C_BLUE, "最後完整兩年；維持成長部位，槓桿比重控制在 20% 以內"),
        ("2028", "開始降風險", C_WARN, "逐步清除 3 倍槓桿（TQQQ/SOXL），台股正二部分轉高股息"),
        ("2029 Q1", "退休前最後一季", C_BAD, "完成配息結構轉換；確保年配息覆蓋退休年支出 %s萬" % w1(exp_yr)),
        ("2029/03/31", "退休日", C_BAD, "目標總資產 16,000 萬；之後靠配息＋提領支應"),
    ]
    tl = []
    for when, what, col, desc in tl_items:
        tl.append(f'''      <div style="display:flex;gap:10px;margin-bottom:12px;align-items:flex-start">
        <div style="flex:0 0 78px;font-size:11px;font-weight:700;color:{col};padding-top:2px">{when}</div>
        <div style="flex:0 0 8px;width:8px;height:8px;border-radius:50%;background:{col};margin-top:6px"></div>
        <div style="flex:1">
          <div style="font-size:13px;font-weight:600;margin-bottom:2px">{what}</div>
          <div style="font-size:11px;color:var(--muted);line-height:1.5">{desc}</div>
        </div>
      </div>''')

    timeline = f'''  <div class="card">
    <div class="stitle">行動時間軸</div>
    <div style="margin-top:10px">
{chr(10).join(tl)}
    </div>
  </div>'''

    body = (f'<div id="tab-retire" class="tab-content">\n{kpi}\n{bar}\n{track}\n{scen}\n{cash}\n{timeline}\n</div>\n')
    return body, info


JS_LIVE = '''
// ══ 退休倒數（瀏覽器端即時計算，每天自動正確）══
const RETIRE_TS = new Date(2029,2,31).getTime();   // 月份 0-based：2=3月
const TRACK_TS  = new Date(2026,2,24).getTime();
function tickRetire(){
  const el=document.getElementById('rc-days'); if(!el) return;
  const now=Date.now();
  const d=Math.max(0,Math.ceil((RETIRE_TS-now)/86400000));
  el.innerHTML=d.toLocaleString()+'<span style="font-size:12px;color:var(--muted)">天</span>';
  const ym=document.getElementById('rc-ym');
  if(ym) ym.textContent=Math.floor(d/365)+' 年 '+Math.floor((d%365)/30)+' 個月 ｜ 2029/03/31';
  const p=Math.max(0,Math.min(100,(now-TRACK_TS)/(RETIRE_TS-TRACK_TS)*100));
  const bar=document.getElementById('rc-bar'); if(bar) bar.style.width=p.toFixed(1)+'%';
  const bt=document.getElementById('rc-bar-t'); if(bt) bt.textContent='已過 '+p.toFixed(1)+'%';
}
'''


def inject(html, GD, today=None):
    """插入或重建退休倒數分頁。可重複執行（idempotent）。"""
    errs = []
    body, info = build(GD, today)

    # ── 分頁內容：已存在則整段取代，否則插在 footer 前 ──
    i = html.find('<div id="tab-retire" class="tab-content">')
    if i >= 0:
        j = html.find('<div id="tab-', i + 10)
        if j < 0:
            j = html.find('<div style="text-align:center;font-size:11px;color:var(--hint);margin-top:20px', i)
        tail = html.rfind('<!--', i, j)
        end = tail if tail > i else j
        html = html[:i] + body + '\n' + html[end:]
    else:
        foot = '<div style="text-align:center;font-size:11px;color:var(--hint);margin-top:20px'
        k = html.find(foot)
        if k < 0:
            errs.append('找不到 footer 錨點')
        else:
            html = html[:k] + body + '\n' + html[k:]

    # ── 分頁按鈕（只加一次）──
    if "switchTab(this,'retire')" not in html:
        anchor = '''<button class="tab" onclick="switchTab(this,'expense')">🧾 每月開銷</button>'''
        if anchor not in html:
            errs.append('找不到 expense 分頁按鈕錨點')
        else:
            html = html.replace(anchor,
                anchor + '\n  <button class="tab" onclick="switchTab(this,\'retire\')">⏳ 退休倒數</button>', 1)

    # ── JS（只加一次）──
    if 'function tickRetire' not in html:
        k = html.rfind('</script>')
        if k < 0:
            errs.append('找不到 </script>')
        else:
            html = html[:k] + JS_LIVE + '\n' + html[k:]

    # ── switchTab 掛鉤（只加一次）──
    if "if(name==='retire')" not in html:
        old = "    if(name==='calendar') renderCalendar();"
        if old not in html:
            errs.append('找不到 switchTab 掛鉤點')
        else:
            html = html.replace(old, old + "\n    if(name==='retire') tickRetire();", 1)

    # ── 載入時跑一次（只加一次）──
    if 'try{tickRetire();}catch(e){}' not in html:
        html = html.replace("</script>\n</body>", "\ntry{tickRetire();}catch(e){}\n</script>\n</body>", 1)

    # ── 頁首退休日 ──
    html = html.replace('目標：2028/12 退休', '目標：2029/03/31 退休')

    return html, info, errs


def verify(html, info):
    import re
    errs = []
    i = html.find('<div id="tab-retire"')
    if i < 0:
        return ['找不到 tab-retire 區塊']
    j = html.find('<div id="tab-', i + 10)
    seg = html[i:j if j > 0 else len(html)]

    if f'{info["days"]:,}' not in seg:
        errs.append(f'倒數天數 {info["days"]:,} 未寫入')
    if f'{w(info["gap"]):,}' not in seg:
        errs.append(f'目標缺口 {w(info["gap"]):,}萬 未寫入')
    # 里程碑最後一列必須是退休日
    ds = re.findall(r'(\d{4}/\d{2}/\d{2})</td>', seg)
    if not ds or ds[-1] != f'{RETIRE_DATE:%Y/%m/%d}':
        errs.append(f'里程碑末列 {ds[-1] if ds else "無"} ≠ 退休日')
    # 退休日必須出現在標題
    if '2029/03/31 退休' not in html:
        errs.append('頁首退休日未更新為 2029/03/31')
    # JS 常數
    if 'new Date(2029,2,31)' not in html:
        errs.append('JS 退休日常數錯誤')
    return errs
