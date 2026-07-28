# RetireFlow 儀表板更新 SOP

> 每次執行「更新儀表板」時，Claude 必須確認以下所有欄位都已正確更新。

---

## 一、資料來源

| 來源 | 用途 |
|------|------|
| Google Drive 工作表1（持股+股價欄） | 各持股股數、最新股價 |
| Google Drive 資產歷史記錄（最新一列） | 總資產、各類別、負債、股息 |
| 前一日歷史記錄 | 計算今日變化（萬元、%） |

---

## 二、每次必須更新的欄位（完整清單）

### A. Header 區域

| 欄位 | 位置 | 計算方式 |
|------|------|---------|
| 資料日期 | `Google Drive 即時同步｜YYYY/MM/DD｜` | Google Drive 最新記錄日期 |

---

### B. Pills（頂部摘要標籤）

| 欄位 | HTML 位置 | 計算方式 |
|------|-----------|---------|
| 達成率 % | `達成率 XX.X%` | `total / 1,600,000,000 × 100` |
| 槓桿比率 % | `槓桿 XX.X%` | `槓桿ETF總值 / total × 100` |

---

### C. 核心 Metric 卡片（共 5 張）

| 卡片 | 主數字 | 副文字 | 計算方式 |
|------|------|------|---------|
| 總資產 | `X,XXX萬` | `↑/↓ ±XXX萬 今日` | GD total；今日變化 = today - prev |
| 淨資產 | `X,XXX萬` | `負債比 XX.X%` | `total - debt`；負債比 = `debt/total×100` |
| 年化波動度 | `33.5%` | `最大回撤 -14.7%` | **靜態，不需更新** |
| 槓桿ETF現值 | `XXX萬` | `佔總資產 XX.X%` | 各槓桿ETF市值加總；佔比 = `槓桿/total×100` |
| 距退休 | `X年 X月` | `年股息 XXX萬｜月均 XX萬` | 2028/12 距今；GD 年股息欄位 |

> ⚠️ **最常出錯**：淨資產數字與總資產混淆、負債比未隨總資產更新

---

### D. 退休目標達成率區塊

| 欄位 | 計算方式 |
|------|---------|
| 總資產 X,XXX萬 ／ 目標 16,000萬 | GD total |
| 達成率大字 XX.X% | `total / 160,000,000 × 100` |
| 還需增加 X,XXX萬 | `16,000 - total_w`（萬） |
| 進度條寬度 width:XX.X% | 同達成率 % |

> ⚠️ **最常出錯**：達成率大字和進度條寬度用兩個獨立字串替換，其中一個容易遺漏

---

### E. 退休試算 input 預設值

| input id | 欄位 | 更新方式 |
|----------|------|---------|
| `s-current` | 目前總資產（萬） | GD total_w |
| `s-target` | 退休目標（萬） | 固定 16000，**不更新** |
| `s-monthly` | 每月新增（萬） | 固定 15，**不更新** |
| `s-return` | 預期年報酬率 | 固定 10，**不更新** |
| `s-expense` | 退休每月支出 | 固定 12，**不更新** |
| `s-age` | 目前年齡 | 固定 52，**不更新** |

---

### F. 油表（4 個 drawGauge 呼叫）

| 函式呼叫 | 參數 | 計算方式 |
|---------|------|---------|
| `drawGauge('g-tw', ach%, 'X,XXX萬', '#378ADD')` | 台股達成率、台股市值 | `tw/100,000,000×100`；GD tw |
| `drawGauge('g-us', ach%, 'X,XXX萬', '#1D9E75')` | 美股達成率、美股市值 | `us/40,000,000×100`；GD us |
| `drawGauge('g-jp', ach%, 'XXX萬', '#EF9F27')` | 日股達成率、日股市值 | `jp/10,000,000×100`；GD jp |
| `drawGauge('g-fd', ach%, 'XXX萬', '#7F77DD')` | 基金達成率、基金市值 | `fund/10,000,000×100`；GD fund |

---

### G. JS 數據陣列（影響所有 Bar Chart）

| 變數 | 頂層定義 | 更新方式 |
|------|---------|---------|
| `window.TW_DATA` | ✅ 必須頂層 | 重算台股各持股估值，排序 |
| `window.US_DATA` | ✅ 必須頂層 | 重算美股各持股估值×USD/TWD，排序 |
| `window.JP_DATA` | ✅ 必須頂層 | 重算日股各持股估值×JPY/TWD，排序 |
| `window.FD_DATA` | ✅ 必須頂層 | 基金三帳戶（鉅亨/HSBC/基富通），排序 |
| `window.TW_BROKER` | ✅ 必須頂層 | 依券商分組台股持股 |
| `window.US_BROKER` | ✅ 必須頂層 | 依券商分組美股持股 |

---

### H. 基金頁面 HTML bar items

```javascript
const items = [
  {name:'鉅亨網基金', val:411.4, pct:47.3, color:'#378ADD'},
  {name:'HSBC結構型', val:314.5, pct:36.2, color:'#1D9E75'},
  {name:'基富通基金', val:142.7, pct:16.5, color:'#EF9F27'},
];
```

> 基金金額固定（GD 基金帳戶表），僅在基金帳戶有變動時更新

---

### I. FALLBACK_PRICES（API 失效時備用）

| 類別 | 更新時機 |
|------|---------|
| 台股股價（22檔） | 每次更新都從 GD 取最新值 |
| 美股股價（29檔） | 每次更新都從 GD 取最新值 |
| 日股股價（4檔） | 每次更新都從 GD 取最新值 |
| `USDTWD` | 從 GD 推算（us_total / Σ(股數×USD股價)） |
| `JPYTWD` | 從 GD 推算（jp_total / Σ(股數×JPY股價)） |

---

### J. 資產月曆 CAL_DATA

```python
new_entry = {
    "date": "YYYY-MM-DD",
    "v": round(today_total / 10000),
    "c": round((today_total - prev_total) / 10000, 1),
    "p": round((today_total - prev_total) / prev_total * 100, 2),
}
```

> ⚠️ **容易遺漏**：每次更新儀表板必須同步追加當日月曆條目

---

## 三、更新完成後驗證清單

### 1. HTML 數字核對

```python
checks = [
    (f'>{total_w:,}<span',          '總資產數字'),
    (f'>{net_w:,}<span',            '淨資產數字'),   # ← 最常出錯
    (f'負債比 {debt_ratio}%',        '負債比'),
    (f'{chg_arrow} {day_chg:+}萬 今日', '今日變化'),
    (f'達成率 {tot_ach}%',           'pill 達成率'),
    (f'>{tot_ach}%</div>',           '達成率大字'),   # ← 最常出錯
    (f'width:{tot_ach}%',            '進度條寬度'),   # ← 最常出錯
    (f'還需增加 {16000-total_w:,}萬', '還需增加'),
    (f'總資產 {total_w:,}萬 ／ 目標 16,000萬', '達成率副標'),
    (f'value="{total_w}"',           '試算預設值'),
    (f'年股息 {div_w}萬',            '年股息'),
    (f'window.FD_DATA=',             'FD_DATA 頂層定義'),
    (f'window.TW_DATA=\n[',          'TW_DATA 靜態初始值'),
    (f'window.US_DATA=\n[',          'US_DATA 靜態初始值'),
    (f'window.JP_DATA=\n[',          'JP_DATA 靜態初始值'),
    (f'"date":"{today_date}"',        'CAL_DATA 當日條目'),
]
for pattern, desc in checks:
    assert pattern in html, f"❌ {desc} 未更新：找不到 '{pattern}'"
print("✅ 所有欄位驗證通過")
```

### 2. JS 語法驗證

```python
js = html[html.rfind('<script>')+8:html.rfind('</script>')]
with open('/tmp/check.js','w') as f: f.write(js)
r = subprocess.run(['node','--check','/tmp/check.js'],capture_output=True,text=True)
assert r.returncode == 0, f"❌ JS 語法錯誤：{r.stderr}"
print("✅ JS 語法正確")
```

### 3. 作用域深度驗證

```python
for var in ['window.TW_DATA','window.US_DATA','window.JP_DATA',
            'window.FD_DATA','window.TW_BROKER','window.US_BROKER','const TYPE_C']:
    idx = js.find(var)
    if idx < 0: continue
    depth = sum(1 if c=='{' else -1 if c=='}' else 0 for c in js[:idx])
    assert depth == 0, f"❌ {var} 不在頂層！深度={depth}"
print("✅ 作用域驗證通過")
```

---

## 四、完整更新流程（標準版）

```
① 讀取 Google Drive
   - 工作表1：各持股股數 + 最新股價（GOOGLEFINANCE 公式）
   - 資產歷史：最新一列（today）+ 前一列（prev）

② 計算核心指標
   - usd_twd = us_total / Σ(股數 × USD股價)
   - jpy_twd = jp_total / Σ(股數 × JPY股價)
   - total_w, net_w, debt_w, tw_w, us_w, jp_w, fd_w（萬元）
   - 各達成率、負債比、今日變化

③ 重建 JS 數據
   - TW_DATA / US_DATA / JP_DATA / FD_DATA（排序後陣列）
   - TW_BROKER / US_BROKER（券商分組）
   - FALLBACK_PRICES（各股最新價）

④ 替換 HTML 靜態欄位（按順序）
   A. 日期
   B. Pills（達成率%、槓桿%）
   C. 總資產數字 + 今日變化
   D. 淨資產數字 + 負債比          ← 容易出錯
   E. 年股息 + 月均
   F. 槓桿ETF現值 + 佔比
   G. 退休目標達成率大字 + 進度條   ← 容易出錯
   H. 還需增加 X,XXX 萬
   I. 達成率副標題（總資產 X,XXX萬 ／ 目標 16,000萬）
   J. 退休試算 s-current 預設值
   K. 油表 drawGauge 4 個呼叫
   L. 基金 HTML bar items

⑤ 追加月曆條目 CAL_DATA           ← 容易遺漏

⑥ 三重驗證
   - node --check JS 語法
   - HTML 數字核對 checklist
   - 作用域深度驗證

⑦ Push GitHub Pages
```

---

## 五、常見錯誤速查

| 症狀 | 根本原因 | 解法 |
|------|---------|------|
| 淨資產顯示舊總資產數字 | regex pattern 未精確匹配 | 用精確字串 `>X,XXX<span` 替換 |
| 達成率大字未更新 | `>XX.X%</div>` 與進度條 `width:XX.X%` 是兩個獨立替換 | 兩處都要替換，加入 assert 驗證 |
| 進度條寬度錯誤 | 同上 | 同上 |
| 月曆未更新 | CAL_DATA 追加步驟遺漏 | 在步驟⑤明確執行 |
| 基金 Bar Chart 空白 | `FD_DATA` 不在頂層（被困在函式內） | 確認 `window.FD_DATA` 深度 = 0 |
| 所有圖表空白 | `TYPE_C` 未定義或 `buildHBar` 遺失 | 執行關鍵函式完整性驗證 |
| 油表空白 | `drawGauge` 函式遺失 | 同上 |
| 數字更新但圖表不重繪 | `window.chartsInit` 與 `let chartsInit` 混用 | 統一用 `window.chartsInit` |
