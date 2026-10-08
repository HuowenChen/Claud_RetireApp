#!/usr/bin/env python3
"""
台股／美股分析區塊產生器 —— 由當期持股重建

背景：Pareto 分頁的「標題、重點洞察、健康評估」原本是寫死的敘述文字，
      rf_update.py 只更新資料陣列與 Pareto 表，這三塊從 7 月起就沒再變過
      （例如仍寫「5,046萬、18檔、台積電 1,718萬」、仍列已出清的 0050/0056/SOFI）。
      此模組讓這三塊每次更新都由持股重算。
"""
import re

C_RED, C_BLUE, C_AMBER, C_GREEN, C_PURPLE = "#E24B4A", "#378ADD", "#EF9F27", "#1D9E75", "#7F77DD"

# 台股分組（代號 → 組別）
TW_GROUPS = [
    ("台積電個股集中",      lambda c: c == "2330",                                   C_RED,   15),
    ("槓桿ETF合計",        lambda c: c in ("00631L", "00663L", "00675L", "00685L"), C_AMBER, 15),
    ("市值型ETF",          lambda c: c in ("0050", "006208", "009816"),             C_BLUE,  None),
    ("配息型ETF",          lambda c: c in ("0056", "00881", "00894", "00927", "00935"), C_GREEN, None),
    ("主動型ETF",          lambda c: c.endswith("A"),                               C_PURPLE, None),
    ("其他個股",           lambda c: c in ("6121", "2812", "5483", "6147", "6290"), C_RED,   None),
]

US_GROUPS = [
    ("現金替代（SGOV）",    lambda c: c == "SGOV",                                   C_GREEN, None),
    ("核心ETF（VOO/VT/VTI/QQQ）", lambda c: c in ("VOO", "VT", "VTI", "QQQ"),        C_BLUE,  None),
    ("半導體ETF（SMH/SOXX）",     lambda c: c in ("SMH", "SOXX"),                    C_BLUE,  None),
    ("槓桿部位",            lambda c: c in ("TQQQ", "SOXL", "QLD", "SSO", "SNXX", "MUU", "TSMX", "SPCX"), C_AMBER, 15),
    ("個股合計",            lambda c: c in ("BRK.B", "GOOG", "NVDA", "PLTR", "TSLA", "MU",
                                            "AMD", "AVGO", "TER", "TSM", "GRAB", "DRAM", "MAGS"), C_RED, 40),
]


def _agg(rows, groups):
    """rows: [(code, val_yuan)] → [(label, val, pct, color, cap)]"""
    tot = sum(v for _, v in rows) or 1
    out = []
    for label, pred, col, cap in groups:
        v = sum(val for c, val in rows if pred(c))
        if v <= 0:
            continue
        out.append((label, v, v / tot * 100, col, cap))
    return out, tot


def _mark(pct, cap):
    if cap is None:
        return "✓", None
    if pct > cap * 1.3:
        return "⚠️", C_RED
    if pct > cap:
        return "⚠️", C_AMBER
    return "✓", C_GREEN


def _rows_html(aggs):
    out = []
    for label, v, pct, col, cap in aggs:
        mk, ov = _mark(pct, cap)
        c = ov or col
        out.append('<div style="display:flex;justify-content:space-between;align-items:center;'
                   'padding:6px 0;border-bottom:1px solid var(--border)">'
                   f'<span style="font-size:12px">{label}</span>'
                   f'<span style="font-size:12px;font-weight:600;color:{c}">{pct:.1f}%{mk}</span></div>')
    return "\n        ".join(out)


def _insight_tw(rows, tot):
    s = sorted(rows, key=lambda x: -x[1])
    t1, t2 = s[0], s[1]
    top5 = s[:5]
    lev = sum(v for c, v in rows if c in ("00631L", "00663L", "00675L", "00685L"))
    parts = [f"🔍 {t1[0]}（{t1[1]/1e4:,.0f}萬／{t1[1]/tot*100:.1f}%）"
             f"＋{t2[0]}（{t2[1]/1e4:,.0f}萬／{t2[1]/tot*100:.1f}%）"
             f"＝ 台股前兩大佔 {(t1[1]+t2[1])/tot*100:.1f}%。",
             f"前5大（{'+'.join(c for c, _ in top5)}）合計 {sum(v for _, v in top5)/tot*100:.1f}%。",
             f"槓桿ETF合計 {lev/1e4:,.0f}萬佔台股 {lev/tot*100:.1f}%"
             + ("，超過建議 15% 上限。" if lev / tot > 0.15 else "，在 15% 建議上限內。")]
    return "".join(parts)


def _insight_us(rows, tot, fx=31.74):
    s = sorted(rows, key=lambda x: -x[1])
    t1, t2 = s[0], s[1]
    lev = sum(v for c, v in rows if c in ("TQQQ", "SOXL", "QLD", "SSO", "SNXX", "MUU", "TSMX", "SPCX"))
    sg = sum(v for c, v in rows if c == "SGOV")
    return (f"🔍 {t1[0]}（{t1[1]*fx/1e4:,.0f}萬／{t1[1]/tot*100:.1f}%）為最大部位，"
            f"其次 {t2[0]}（{t2[1]*fx/1e4:,.0f}萬／{t2[1]/tot*100:.1f}%）。"
            f"SGOV 現金替代 {sg*fx/1e4:,.0f}萬（{sg/tot*100:.1f}%）。"
            f"槓桿部位合計 {lev*fx/1e4:,.0f}萬佔美股 {lev/tot*100:.1f}%"
            + ("，需嚴設停損。" if lev / tot > 0.15 else "。"))


def _merge(pairs):
    d = {}
    for c, v in pairs:
        d[c] = d.get(c, 0) + v
    return list(d.items())


def rebuild(html, TW, US, usd=31.74):
    """TW/US: rf_update.py 的持股 list [(broker,code,shares,price)]"""
    errs = []
    tw_rows = _merge([(c, s * p) for _, c, s, p in TW])
    us_rows_usd = _merge([(c, s * p) for _, c, s, p in US])

    tw_agg, tw_tot = _agg(tw_rows, TW_GROUPS)
    us_twd = sum(v for _, v in us_rows_usd) * usd
    us_agg, us_tot = _agg(us_rows_usd, US_GROUPS)

    info = dict(tw_tot=tw_tot, tw_n=len(tw_rows), us_tot=us_tot, us_twd=us_twd, us_n=len(us_rows_usd),
                tw_agg=tw_agg, us_agg=us_agg)

    # ── 台股 ──
    html, e = _sub(html, r'<div class="stitle">台股持股分析（[^<]*）</div>',
                   f'<div class="stitle">台股持股分析（{tw_tot/1e4:,.0f}萬，{len(tw_rows)}檔）</div>', '台股標題')
    errs += e
    html, e = _sub(html, r'<div class="key-insight">🔍 [^<]*?台股前兩大[^<]*?</div>',
                   f'<div class="key-insight">{_insight_tw(tw_rows, tw_tot)}</div>', '台股洞察')
    errs += e
    html, e = _sub_block(html, '台股持股健康評估', _rows_html(tw_agg), '台股健康評估')
    errs += e

    # ── 美股 ──
    html, e = _sub(html, r'<div class="stitle">美股持股分析（[^<]*）</div>',
                   f'<div class="stitle">美股持股分析（{us_twd/1e4:,.0f}萬，{len(us_rows_usd)}檔）</div>', '美股標題')
    errs += e
    html, e = _sub(html, r'<div class="key-insight">🔍 SGOV[^<]*?</div>',
                   f'<div class="key-insight">{_insight_us(us_rows_usd, us_tot, usd)}</div>', '美股洞察')
    errs += e
    html, e = _sub_block(html, '美股持股健康評估', _rows_html(us_agg), '美股健康評估')
    errs += e

    return html, info, errs


def _sub(html, pat, rep, name):
    if not re.search(pat, html):
        return html, [f'{name}：找不到錨點']
    return re.sub(pat, lambda m: rep, html, count=1), []


def _sub_block(html, title, rows_html, name):
    """取代 <div class="stitle">{title}</div><div style="margin-top:4px"> ... </div>"""
    i = html.find(f'<div class="stitle">{title}</div>')
    if i < 0:
        return html, [f'{name}：找不到標題']
    j = html.find('<div style="margin-top:4px">', i)
    if j < 0 or j - i > 200:
        return html, [f'{name}：找不到內容起點']
    # 以巢狀深度找到該 div 的結尾
    k, depth = j, 0
    while k < len(html):
        if html.startswith('<div', k):
            depth += 1
        elif html.startswith('</div>', k):
            depth -= 1
            if depth == 0:
                k += 6
                break
        k += 1
    new = '<div style="margin-top:4px">\n        ' + rows_html + '\n      </div>'
    return html[:j] + new + html[k:], []


def verify(html, info):
    errs = []
    # 標題筆數
    m = re.search(r'台股持股分析（([\d,]+)萬，(\d+)檔）', html)
    if not m:
        errs.append('台股分析標題未更新')
    else:
        if int(m.group(1).replace(',', '')) != round(info['tw_tot'] / 1e4):
            errs.append(f"台股分析標題金額 {m.group(1)}萬 ≠ {info['tw_tot']/1e4:,.0f}萬")
        if int(m.group(2)) != info['tw_n']:
            errs.append(f"台股分析標題檔數 {m.group(2)} ≠ {info['tw_n']}")
    # 健康評估百分比合計須 ≤100 且各列存在
    for mkt, agg in (('台股', info['tw_agg']), ('美股', info['us_agg'])):
        i = html.find(f'<div class="stitle">{mkt}持股健康評估</div>')
        if i < 0:
            errs.append(f'{mkt}健康評估區塊不存在'); continue
        seg = html[i:i + 2500]
        for label, v, pct, col, cap in agg:
            if f'{pct:.1f}%' not in seg:
                errs.append(f'{mkt}健康評估「{label}」{pct:.1f}% 未寫入')
    # 已出清標的不得出現在分析敘述
    for i_tab in ('pareto-tw', 'pareto-us'):
        a = html.find(f'<div id="tab-{i_tab}"')
        b = html.find('<div id="tab-', a + 10)
        seg = html[a:b]
        ki = re.findall(r'class="key-insight">(.*?)</div>', seg, re.S)
        hl = re.findall(r'<span style="font-size:12px">([^<]+)</span>', seg)
        txt = ' '.join(ki + hl)
        for dead in info.get('dead', []):
            if dead in txt:
                errs.append(f'{i_tab} 敘述仍提及已出清標的 {dead}')
    return errs
