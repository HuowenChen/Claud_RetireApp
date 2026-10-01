#!/usr/bin/env python3
"""
配息月曆分頁產生器 —— 以 dividend_records.csv 為唯一真實來源

背景：原本分頁是寫死的 HTML，CSV 只是獨立的紀錄檔，兩邊各走各的，
      更新 CSV 不會反映到儀表板。此模組讓分頁每次都由 CSV 重建。

用法：from rf_dividend import rebuild_dividend_tab
      html, info = rebuild_dividend_tab(html, 'dividend_records.csv')
"""
import csv, re, collections

MONTH_LABEL = {m: f"{m}月" for m in range(1, 13)}
C_PAID = "#1D9E75"   # 已入帳
C_ANN  = "#EF9F27"   # 已公告


def load_records(path):
    rows = []
    for r in csv.DictReader(open(path, encoding='utf-8')):
        d = (r.get('入帳日期') or '').strip()
        if not d:
            continue
        try:
            amt = float(r.get('實收金額') or 0)
            sh = float(r.get('股數') or 0)
            per = float(r.get('每股配息') or 0)
        except ValueError:
            continue
        rows.append(dict(date=d, code=(r.get('代號') or '').strip(),
                         name=(r.get('名稱') or '').strip(),
                         broker=(r.get('券商') or '').strip(),
                         sh=sh, per=per, amt=amt,
                         status=(r.get('狀態') or '').strip(),
                         note=(r.get('備註') or '').strip()))
    rows.sort(key=lambda x: (x['date'], x['code']))
    return rows


def w1(n):
    """元 → 萬，1 位小數"""
    return round(n / 10000, 1)


def build(rows, year='2026'):
    yr = [r for r in rows if r['date'].startswith(year)]
    paid = sum(r['amt'] for r in yr if r['status'] == '已入帳')
    ann = sum(r['amt'] for r in yr if r['status'] == '已公告')
    tot = paid + ann

    # 每月彙總（依入帳日歸月）
    mon = collections.defaultdict(lambda: dict(paid=0.0, ann=0.0))
    for r in yr:
        m = int(r['date'][5:7])
        key = 'paid' if r['status'] == '已入帳' else 'ann'
        mon[m][key] += r['amt']

    months = [m for m in range(1, 13)]
    mx = max((mon[m]['paid'] + mon[m]['ann']) for m in months) or 1

    # 已入帳涵蓋到哪個月
    paid_ms = sorted({int(r['date'][5:7]) for r in yr if r['status'] == '已入帳'})
    ann_ms = sorted({int(r['date'][5:7]) for r in yr if r['status'] == '已公告'})
    paid_rng = f"{paid_ms[0]}-{paid_ms[-1]}月實收" if paid_ms else "尚無"
    ann_rng = f"{ann_ms[0]}-{ann_ms[-1]}月發放" if ann_ms else "無"
    n_mon = len([m for m in months if mon[m]['paid'] + mon[m]['ann'] > 0]) or 1

    # ── KPI ──
    kpi = f'''  <div class="g3">
    <div class="metric"><div class="metric-label">已入帳</div><div class="metric-value" style="color:{C_PAID}">{w1(paid)}<span style="font-size:12px;color:var(--muted)">萬</span></div><div class="metric-sub">{paid_rng}</div></div>
    <div class="metric"><div class="metric-label">已公告待發放</div><div class="metric-value warn">{w1(ann)}<span style="font-size:12px;color:var(--muted)">萬</span></div><div class="metric-sub">{ann_rng}</div></div>
    <div class="metric"><div class="metric-label">累計已知</div><div class="metric-value">{w1(tot)}<span style="font-size:12px;color:var(--muted)">萬</span></div><div class="metric-sub">月均 {w1(tot/n_mon)}萬</div></div>
  </div>'''

    # ── 每月長條 ──
    bars = []
    for m in months:
        p, a = mon[m]['paid'], mon[m]['ann']
        t = p + a
        if t <= 0:
            lab, col, amt_txt = '尚未公告', 'var(--hint)', '—'
            pw = aw = 0.0
        else:
            if a > 0 and p > 0:
                lab = '部分已入帳'
            elif a > 0:
                lab = '已公告'
            else:
                lab = '已入帳'
            col = C_PAID if a == 0 else C_ANN
            amt_txt = f'{w1(t)}萬'
            pw = p / mx * 100
            aw = a / mx * 100
        seg = ''
        if pw > 0:
            seg += f'<div style="background:{C_PAID};width:{pw:.1f}%;height:100%"></div>'
        if aw > 0:
            seg += f'<div style="background:{C_ANN};width:{aw:.1f}%;height:100%"></div>'
        bars.append(f'''      <div style="margin-bottom:9px">
        <div style="display:flex;justify-content:space-between;font-size:11px;margin-bottom:3px">
          <span style="font-weight:600">{m}月<span style="font-weight:400;color:var(--hint);margin-left:5px">{lab}</span></span>
          <span style="font-weight:700;color:{col}">{amt_txt}</span>
        </div>
        <div style="background:var(--bg);border-radius:5px;height:22px;overflow:hidden;display:flex">{seg}</div>
      </div>''')

    bars_html = f'''  <div class="card">
    <div class="stitle">每月配息（依實際入帳日）</div>
    <div style="margin-top:10px">
{chr(10).join(bars)}
    </div>
    <div class="legend-row" style="margin-top:8px">
      <span class="legend-item"><span style="display:inline-block;width:9px;height:9px;background:{C_PAID};border-radius:2px;margin-right:4px"></span>已入帳</span>
      <span class="legend-item"><span style="display:inline-block;width:9px;height:9px;background:{C_ANN};border-radius:2px;margin-right:4px"></span>已公告待發放</span>
      <span class="legend-item"><span style="display:inline-block;width:9px;height:9px;background:var(--bg);border:1px solid var(--border);border-radius:2px;margin-right:4px"></span>尚未公告</span>
    </div>
    <div class="alert alert-info" style="margin-top:10px">💡 <b>本表以「入帳日」歸月，非除息日</b>。配息金額與每股配息均來自 <code>dividend_records.csv</code>，更新該檔即同步此頁。</div>
  </div>'''

    # ── 明細表 ──
    trs = []
    for r in yr:
        col = C_PAID if r['status'] == '已入帳' else C_ANN
        sh_txt = f"{r['sh']:,.0f}"
        trs.append(f'''        <tr><td style="padding:7px 8px;font-size:11px;color:var(--muted)">{r['date']}</td>
          <td style="padding:7px 8px;font-weight:500">{r['code']}</td><td style="padding:7px 8px">{r['name']}</td>
          <td style="padding:7px 8px;font-size:11px;color:var(--muted)">{r['broker']}</td>
          <td style="padding:7px 8px;text-align:right">{sh_txt}</td>
          <td style="padding:7px 8px;text-align:right">{r['per']:g} 元</td>
          <td style="padding:7px 8px;text-align:right;font-weight:600;color:{col}">{w1(r['amt'])}萬</td>
          <td style="padding:7px 8px;font-size:11px;color:var(--muted)">{r['note']}</td></tr>''')

    tbl = f'''  <div class="card">
    <div class="stitle">配息明細（{len(yr)} 筆）</div>
    <div style="overflow-x:auto"><table class="tbl">
      <thead><tr><th>入帳日</th><th>代號</th><th>名稱</th><th>券商</th><th style="text-align:right">股數</th><th style="text-align:right">每股</th><th style="text-align:right">金額</th><th>備註</th></tr></thead>
      <tbody>
{chr(10).join(trs)}
      </tbody>
    </table></div>
    <div class="alert alert-info" style="margin-top:10px">📊 已入帳 {w1(paid)}萬 ＋ 已公告 {w1(ann)}萬 ＝ 累計 {w1(tot)}萬（{len(yr)} 筆）。</div>
  </div>'''

    body = f'<div id="tab-dividend" class="tab-content">\n{kpi}\n{bars_html}\n{tbl}\n</div>\n'
    info = dict(paid=paid, ann=ann, tot=tot, n=len(yr), mon={m: mon[m] for m in months})
    return body, info


def rebuild_dividend_tab(html, csv_path='dividend_records.csv', year='2026'):
    rows = load_records(csv_path)
    body, info = build(rows, year)
    i = html.find('<div id="tab-dividend" class="tab-content">')
    if i < 0:
        raise RuntimeError('找不到 tab-dividend 區塊')
    j = html.find('<div id="tab-', i + 10)
    if j < 0:
        raise RuntimeError('找不到 tab-dividend 結尾')
    # 保留原本區塊之後的註解/空白
    tail_start = html.rfind('<!--', i, j)
    end = tail_start if tail_start > i else j
    html = html[:i] + body + '\n' + html[end:]
    return html, info


def verify(html, info):
    """反向驗證：從 HTML 解析回數字，與 CSV 對帳"""
    errs = []
    i = html.find('<div id="tab-dividend"')
    j = html.find('<div id="tab-', i + 10)
    seg = html[i:j if j > 0 else len(html)]

    # KPI 三個數字
    kv = re.findall(r'metric-value[^>]*>([\d.]+)<span', seg)
    if len(kv) < 3:
        errs.append(f'配息頁 KPI 解析失敗（找到 {len(kv)} 個）')
    else:
        want = [w1(info['paid']), w1(info['ann']), w1(info['tot'])]
        got = [float(x) for x in kv[:3]]
        for lbl, g, wv in zip(['已入帳', '已公告', '累計'], got, want):
            if abs(g - wv) > 0.15:
                errs.append(f'配息頁「{lbl}」{g}萬 vs CSV {wv}萬')

    # 明細筆數
    n = len(re.findall(r'<tr><td style="padding:7px 8px;font-size:11px;color:var\(--muted\)">\d{4}-\d{2}-\d{2}</td>', seg))
    if n != info['n']:
        errs.append(f'配息明細 {n} 筆 vs CSV {info["n"]} 筆')

    # 明細金額加總 == CSV 合計
    amts = [float(x) for x in re.findall(r'font-weight:600;color:#(?:1D9E75|EF9F27)">([\d.]+)萬<', seg)]
    s = sum(amts)
    if abs(s - w1(info['tot'])) > 1.0:
        errs.append(f'配息明細加總 {s:.1f}萬 vs CSV {w1(info["tot"]):.1f}萬')

    # 標題筆數字樣
    m = re.search(r'配息明細（(\d+) 筆）', seg)
    if m and int(m.group(1)) != info['n']:
        errs.append(f'配息明細標題寫 {m.group(1)} 筆 vs 實際 {info["n"]} 筆')

    return errs
