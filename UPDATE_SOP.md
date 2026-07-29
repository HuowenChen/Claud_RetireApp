# RetireFlow 儀表板更新 SOP v2

> 最後更新：2026/07/28
> 每次執行「更新儀表板」時，Claude 必須確認以下 **25 個欄位**全部正確。

---

## 一、資料來源

| 來源 | 用途 |
|------|------|
| GD 工作表1（持股+股價欄） | 各持股股數、最新股價（GOOGLEFINANCE 公式） |
| GD 資產歷史記錄（最新一列） | 總資產、各類別、負債、股息 |
| GD 資產歷史記錄（前一列） | 計算今日變化 |
| GD 基金帳戶工作表 | 三個基金帳戶金額 |
| GD 負債工作表 | 房貸、質借餘額 |

---

## 二、匯率推算方式

```python
# 從 GD 數值反推（不用固定匯率）
usd_twd = gd_us_total / sum(shares × usd_price for all US stocks)
jpy_twd = gd_jp_total / sum(shares × jpy_price for all JP stocks)
```

---

## 三、各類別估值計算

| 類別 | 計算方式 |
|------|---------|
| 台股 | 股數 × 台幣股價（直接）|
| 美股 | 股數 × USD股價 × usd_twd |
| 日股 | 股數 × JPY股價 × jpy_twd（**不用等比例分配**）|
| 基金 | 直接從 GD 基金帳戶工作表讀取 |

> ⚠️ 日股過去曾用「等比例分配」是錯誤設計，**現在改為直接計算**

---

## 四、25 個必須更新的欄位（完整清單）

### A. Header（1個）

| # | 欄位 | HTML 位置 | 計算方式 |
|---|------|-----------|---------|
| 1 | 資料日期 | `Google Drive 即時同步｜YYYY/MM/DD｜` | GD 最新記錄日期 |

---

### B. Pills 標籤（2個）

| # | 欄位 | HTML | 計算方式 |
|---|------|------|---------|
| 2 | 達成率 % | `達成率 XX.X%` | `total / 1.6億 × 100` |
| 3 | 槓桿比率 % | `槓桿 XX.X%` | `槓桿ETF總值 / total × 100` |

> 槓桿ETF包含：00631L/00663L/00675L/00685L（台股）+ TQQQ/SOXL（美股×usd_twd）

---

### C. 核心 Metric 卡片（7個）

| # | 欄位 | HTML 位置 | 計算方式 |
|---|------|-----------|---------|
| 4 | 總資產 | `>X,XXX<span...>萬` | GD total_w |
| 5 | 今日變化 | `↑/↓ ±XXX萬 今日` | today_total - prev_total |
| 6 | 淨資產 | `>X,XXX<span...>萬` | total - debt |
| 7 | 負債比 | `負債比 XX.X%` | `debt / total × 100` |
| 8 | 槓桿ETF現值 | `>XXX.X<span...>萬` | 各槓桿ETF市值加總 |
| 9 | 槓桿ETF佔比 | `佔總資產 XX.X%` | `槓桿總值 / total × 100` |
| 10 | 年股息 | `年股息 XXX.X萬` | GD 預估年領股息 ÷ 10000 |
| 11 | 月均 | `月均 XX.X萬` | 年股息 ÷ 12 |

---

### D. 距退休倒數（2個）

| # | 欄位 | HTML | 計算方式 |
|---|------|------|---------|
| 12 | 距退休年 | `>X</span><span class="cd-u">年` | (2028/12 - 今日) 整年數 |
| 13 | 距退休月 | `>X</span><span class="cd-u">月` | (2028/12 - 今日) 剩餘月數 |

---

### E. 退休目標達成率區塊（4個）

| # | 欄位 | HTML | 計算方式 |
|---|------|------|---------|
| 14 | 達成率大字 | `>XX.X%</div>` | `total / 1.6億 × 100` |
| 15 | 進度條寬度 | `width:XX.X%` | 同上 |
| 16 | 副標題資產 | `總資產 X,XXX萬 ／ 目標 16,000萬` | GD total_w |
| 17 | 還需增加 | `還需增加 X,XXX萬` | `16000 - total_w` |

---

### F. 退休試算預設值（1個）

| # | 欄位 | HTML | 計算方式 |
|---|------|------|---------|
| 18 | s-current | `id="s-current" value="XXXX"` | GD total_w（萬） |

---

### G. 油表 drawGauge（4個）

| # | 欄位 | 正確格式 |
|---|------|---------|
| 19 | 台股 | `drawGauge('g-tw', XX.X, 'X,XXX萬', '#378ADD')` |
| 20 | 美股 | `drawGauge('g-us', XX.X, 'X,XXX萬', '#1D9E75')` |
| 21 | 日股 | `drawGauge('g-jp', XX.X, 'XXX萬', '#EF9F27')` |
| 22 | 基金 | `drawGauge('g-fd', XX.X, 'XXX萬', '#7F77DD')` |

---

### H. 負債明細（2個）

| # | 欄位 | HTML | 來源 |
|---|------|------|------|
| 23 | 房貸 | `X,XXX萬` | GD 負債工作表（星展銀行） |
| 24 | 質借 | `XXX萬` | GD 負債工作表（永豐台股） |

---

### I. 資產月曆（1個）

| # | 欄位 | 格式 | 計算方式 |
|---|------|------|---------|
| 25 | 當日條目 | `"YYYY-MM-DD":{"v":XXXX,"c":±XXX.X,"p":±X.XX}` | v=萬元；c=今日變化萬；p=今日報酬% |

---

## 五、完整更新流程

```
① 讀取 Google Drive
   ├── 工作表1：各持股股數 + 最新股價
   ├── 資產歷史：最新列（today）+ 前一列（prev）
   ├── 基金帳戶：三帳戶金額
   └── 負債：房貸、質借餘額

② 計算核心數值
   usd_twd = gd_us / Σ(股數×USD股價)
   jpy_twd = gd_jp / Σ(股數×JPY股價)
   total_w, net_w, debt_w = GD 直接取值
   tw_w, us_w, jp_w, fd_w = GD 各類別
   div_w = GD 年股息 ÷ 10000
   day_chg = today_total - prev_total（÷10000取萬）
   lev_total = Σ(各槓桿ETF市值)（台股直接，美股×usd_twd）
   退休倒數 = (2028/12/31 - today).months 分解年/月

③ 重建 JS 數據（確認全部在頂層，深度=0）
   window.TW_DATA / window.US_DATA / window.JP_DATA
   window.FD_DATA / window.TW_BROKER / window.US_BROKER
   FALLBACK_PRICES（含 USDTWD/JPYTWD）

④ 替換 HTML 靜態欄位（共 25 個，按序）
   ── Header ──────────────────────────────────
    1. 日期
   ── Pills ────────────────────────────────────
    2. 達成率 %
    3. 槓桿比率 %
   ── Metric 卡片 ──────────────────────────────
    4. 總資產數字
    5. 今日變化（↑/↓ ±XXX萬）
    6. 淨資產數字              ← 最常出錯（混入舊總資產）
    7. 負債比 %
    8. 槓桿ETF現值（萬）
    9. 槓桿ETF佔比 %
   10. 年股息（萬）
   11. 月均（萬）
   ── 距退休 ───────────────────────────────────
   12. 年數
   13. 月數
   ── 達成率區塊 ───────────────────────────────
   14. 達成率大字 %            ← 最常出錯（獨立替換）
   15. 進度條 width:%          ← 最常出錯（獨立替換）
   16. 副標題總資產
   17. 還需增加
   ── 試算 ─────────────────────────────────────
   18. s-current value
   ── 油表 ─────────────────────────────────────
   19-22. drawGauge 4個呼叫
   ── 負債 ─────────────────────────────────────
   23. 房貸金額
   24. 質借金額
   ── 月曆 ─────────────────────────────────────
   25. CAL_DATA 當日條目       ← 最常遺漏

⑤ JS 語法驗證（node --check）

⑥ 25欄位全驗證（見下方程式碼）

⑦ Push GitHub Pages
```

---

## 六、驗證程式碼（每次必跑）

```python
def verify_all(html, v):
    checks = [
        # (描述, 要找的字串)
        ("總資產",     f">{v['total_w']:,}<span"),
        ("淨資產",     f">{v['net_w']:,}<span"),
        ("今日變化",   f"{v['day_chg']:+}萬 今日"),
        ("負債比",     f"負債比 {v['debt_ratio']}%"),
        ("達成率pill", f"達成率 {v['tot_ach']}%"),
        ("達成率大字", f">{v['tot_ach']}%</div>"),
        ("進度條",     f"width:{v['tot_ach']}%"),
        ("還需增加",   f"還需增加 {16000-v['total_w']:,}萬"),
        ("達成率副標", f"總資產 {v['total_w']:,}萬 ／ 目標 16,000萬"),
        ("年股息",     f"年股息 {v['div_w']}萬"),
        ("月均",       f"月均 {v['div_mo']}萬"),
        ("槓桿現值",   f">{v['lev_total']}<span"),
        ("槓桿佔比",   f"佔總資產 {v['lev_pct']}%"),
        ("槓桿pill",   f"槓桿 {v['lev_pct']}%"),
        ("試算預設值", f'value="{v["total_w"]}"'),
        ("距退休年",   f">{v['retire_yr']}</span>"),
        ("距退休月",   f">{v['retire_mo']}</span>"),
        ("油表台股",   f"drawGauge('g-tw',{v['tw_ach']},"),
        ("油表美股",   f"drawGauge('g-us',{v['us_ach']},"),
        ("油表日股",   f"drawGauge('g-jp',{v['jp_ach']},"),
        ("油表基金",   f"drawGauge('g-fd',{v['fd_ach']},"),
        ("月曆當日",   f'"{v["today_date"]}"'),
        ("房貸",       f"{v['mortgage_w']:,}萬"),
        ("USD匯率",    f'"USDTWD":{v["usd_twd"]}'),
        ("JPY匯率",    f'"JPYTWD":{v["jpy_twd"]}'),
    ]
    failed = []
    for desc, pat in checks:
        if pat not in html:
            failed.append(f"❌ {desc}：找不到 '{pat}'")
    if failed:
        for f in failed: print(f)
        raise AssertionError(f"{len(failed)} 個欄位未通過")
    print(f"✅ 全部 {len(checks)} 個欄位驗證通過")
```

---

## 七、常見錯誤速查

| 症狀 | 根本原因 | 解法 |
|------|---------|------|
| 淨資產顯示舊總資產數字 | 替換 pattern 未精確匹配 | 用 `>X,XXX<span...>萬` 精確比對 |
| 達成率大字未更新 | `>XX.X%</div>` 與 `width:XX.X%` 是獨立字串 | 兩處都要替換，加入 assert |
| 年股息/月均顯示舊值 | 更新流程未包含這兩個欄位 | 從 GD div 欄位重新計算 |
| 槓桿ETF現值/佔比錯誤 | 槓桿ETF估值未重算（美股需 ×usd_twd）| 重算後同步更新顯示與 pill |
| 試算預設值未更新 | s-current value 字串格式不同 | 精確比對 `value="XXXX"` |
| 日股用舊等比例值 | 早期錯誤設計殘留 | 改用股數×JPY股價×jpy_twd 直接計算 |
| 月曆未追加 | CAL_DATA 步驟遺漏 | 明確在流程第⑤步執行 |
| 基金 Bar Chart 空白 | `FD_DATA` 不在頂層 | 確認 `window.FD_DATA` 深度=0 |
| 所有圖表空白 | `TYPE_C`/`buildHBar` 遺失 | 執行關鍵函式完整性驗證 |

---

## 八、關鍵函式完整性驗證

```python
must_have = [
    'function drawGauge',          # 油表
    'function buildHBar',          # Bar Chart（含 Chart.destroy()）
    'function buildDonut',         # 圓餅
    'function mkLine',             # 折線
    'function drawAllCharts',      # 初始化
    'function drawTabCharts',      # 分頁渲染
    'function switchTab',          # 分頁切換
    'function renderBrokerTable',  # 券商明細表
    'function rebuildPortfolioData', # 動態重算
    'const TYPE_C=',              # 顏色常數
    'window.FD_DATA=',            # 基金數據（頂層）
    'window.TW_DATA=\n[',         # 台股靜態初始值
    'window.US_DATA=\n[',         # 美股靜態初始值
    'window.JP_DATA=\n[',         # 日股靜態初始值
    'Chart.getChart(ctx)',         # destroy 舊實例
    'chart.umd.js"></script>',    # Chart.js 正確閉合
]
for fn in must_have:
    assert fn in html, f"❌ 缺少: {fn}"
print("✅ 關鍵函式驗證通過")
```

---

## 九、作用域深度驗證

```python
# 確認所有數據變數在頂層（depth=0）
js = html[html.rfind('<script>')+8:html.rfind('</script>')]
for var in ['window.TW_DATA','window.US_DATA','window.JP_DATA',
            'window.FD_DATA','window.TW_BROKER','window.US_BROKER',
            'window.chartsInit','const TYPE_C']:
    idx = js.find(var)
    if idx < 0: continue
    depth = sum(1 if c=='{' else -1 if c=='}' else 0 for c in js[:idx])
    assert depth == 0, f"❌ {var} 不在頂層！深度={depth}"
print("✅ 作用域驗證通過")
```

---

*RetireFlow Pro v3.4.2 Update SOP ｜ 2026/07/28*

---

## 十、走勢圖歷史數據（第 26～33 個欄位）

走勢圖共 8 個陣列，每次更新都需**追加當日數值**：

| 陣列 | 說明 | 來源 |
|------|------|------|
| `HD` | 日期標籤 | `"MM/DD"` 格式 |
| `HT` | 總資產（萬） | GD 當日 total_w |
| `HN` | 淨資產（萬） | GD 當日 net_w |
| `HDbt` | 總負債（萬） | GD 當日 debt_w |
| `HTW` | 台股（萬） | GD 當日 tw_w |
| `HUS` | 美股（萬） | GD 當日 us_w |
| `HJP` | 日股（萬） | GD 當日 jp_w |
| `HFD` | 基金（萬） | GD 當日 fd_w |

```python
# 在各陣列最後 ]; 前插入新值
for arr_name, new_val in [
    ('HD',   f'"07/28"'),
    ('HT',   total_w),
    ('HN',   net_w),
    ('HDbt', debt_w),
    ('HTW',  tw_w),
    ('HUS',  us_w),
    ('HJP',  jp_w),
    ('HFD',  fd_w),
]:
    idx = html.find(f'const {arr_name}=[')
    end = html.find('];', idx)
    html = html[:end] + f',{new_val}' + html[end:]
```

---

## 十一、完整更新欄位總覽（33個）

```
Header（1）：日期
Pills（2）：達成率%、槓桿%
Metric 卡片（8）：總資產、今日變化、淨資產、負債比、
                   槓桿ETF現值、槓桿ETF佔比、年股息、月均
距退休（2）：年、月
達成率區塊（4）：大字%、進度條width%、副標題、還需增加
試算預設值（1）：s-current
油表（4）：台股、美股、日股、基金 drawGauge
負債明細（2）：房貸、質借
資產月曆（1）：CAL_DATA 當日條目
走勢圖（8）：HD + HT + HN + HDbt + HTW + HUS + HJP + HFD
```

> ⚠️ **走勢圖最容易被遺漏**：每次更新完靜態數字後，必須同步追加走勢圖歷史陣列。


---

## 十二、【重大修正】驗證方法論改版（2026/07/29）

### 為什麼舊方法會反覆出錯

舊驗證只檢查「字串是否存在」：

```python
assert f'>{total_w:,}<' in html   # ❌ 只證明字串在，不證明數字對
```

這種檢查無法發現：券商表格用舊股價、JS 陣列沒被替換、加總與 Google Drive 對不上。

### 新方法：反向解析對帳

**從 HTML 把資料解析回來，加總後跟 Google Drive 比對，差異超過門檻就中止 push。**

```python
# 1. 各市場陣列加總 vs Google Drive
for var, gd_val in [('TW_DATA', GD['tw']), ('US_DATA', GD['us']), ('JP_DATA', GD['jp'])]:
    m = re.search(rf'window\.{var}=\s*(\[[\s\S]*?\]);', html)
    vals = [float(v) for v in re.findall(r'val:([\d.]+)', m.group(1))]
    diff = abs(round(sum(vals),1) - round(gd_val/10000,1))
    assert diff <= max(2.0, gd_val/10000*0.005), f"{var} 對帳差 {diff}萬"

# 2. 券商小計加總 vs Google Drive
m = re.search(rf'window\.TW_BROKER = (\{{[\s\S]*?\n\}});', html)
totals = [float(v) for _,v in re.findall(r'"([^"]+)": \{total:([\d.]+)', m.group(1))]
assert abs(sum(totals) - GD['tw']/10000) <= 2.0

# 3. 逐筆抽驗（股數 × 股價 = 估值）
m = re.search(r'\{code:"2330",name:"[^"]+",shares:(\d+),price:([\d.]+),val:([\d.]+)', html)
expected = round(int(m.group(1)) * float(m.group(2)) / 10000, 1)
assert abs(expected - float(m.group(3))) < 0.15, "台積電估值錯誤"
assert float(m.group(2)) == 今日股價, "股價未更新"   # ← 抓出用舊股價的問題
```

---

### 已修正的三個結構性 bug

**Bug A — 分多次 push 導致覆蓋**

主腳本 push 後，補救腳本重新讀磁碟舊檔、只改部分欄位再 push，把前次的 JS 陣列更新蓋掉。

> **規則：一次執行完成所有替換，通過驗證才 push，禁止分次補救 push。**

**Bug B — `find()` + 切片替換不可靠**

```python
# ❌ 舊做法：邊界計算受換行格式影響，會靜默失敗
idx = html.find('window.TW_DATA=\n[')
end = html.find('];\n', idx) + 3
html = html[:idx] + new + html[end:]

# ✅ 新做法：正則整塊替換
html = re.sub(r'window\.TW_DATA=\s*\[[\s\S]*?\];', f'window.TW_DATA=\n{new};', html, count=1)
```

**Bug C — 替換函式破壞反向參照**

```python
# ❌ 這行把 \g<1> 變成 \\g<1>，所有帶 backreference 的替換全部失效
new, n = re.subn(pat, rep.replace('\\','\\\\'), html, count=1)

# ✅ 直接傳入
new, n = re.subn(pat, rep, html, count=1)
```

---

### 正則錨點陷阱

`const items=` 在 `buildHBar()` 內也有一個（`const items=[...top].reverse();`），非貪婪匹配會從那裡一路吃到基金陣列，刪掉中間 1000+ 行程式碼。

```python
# ❌ 誤匹配 buildHBar 內的 const items
re.sub(r'const items=\[[\s\S]*?\];', ...)

# ✅ 用內容特徵錨定
re.sub(r"const items=\[\{name:'[\s\S]*?\];", ...)
```

> **規則：替換前先用 `re.findall()` 確認匹配數量，多於 1 個就要加錨點。**

---

### 標準腳本

`/tmp/rf_update.py` — 單一檔案完成：讀 GD 資料 → 計算 → 全部替換 → 反向對帳驗證 → 通過才 push。

每次更新只改頂部 `GD`、`TW`、`US`、`JP`、`FUND` 五個資料區塊，其餘不動。

