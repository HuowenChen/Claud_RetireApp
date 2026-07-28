# RetireFlow Pro v3.4 開發日誌

> 記錄日期：2026/07/28
> 網址：https://huowenchen.github.io/Claud_RetireApp/
> Repo：HuowenChen/Claud_RetireApp（main）

---

## 系統現況（7/28 最新）

| 指標 | 數值 |
|------|------|
| 總資產 | NT$8,196萬 |
| 淨資產 | NT$3,927萬 |
| 總負債 | NT$4,269萬（房貸3,505＋質借763） |
| 退休達成率 | 51.2%（目標16,000萬） |
| USD/TWD | 32.30 |
| JPY/TWD | 0.195 |
| 年股息 | 134.7萬 |

---

## 本輪解決的問題

### 問題一：日股估值錯誤（349萬 vs 實際679萬）

**原因：** 用固定匯率 JPY/TWD=0.222 估算，但券商實際淨值更高。

**解法：** 改用 Google Drive 歷史記錄的實際總值，反推正確匯率後等比例分配各持股。

```python
jp_raw_jpy = 6000*3876 + 600*2926 + 900*3692 + 500*7381  # ¥32,024,900
jpy_twd = jp_gd_total / jp_raw_jpy  # 0.195（每次從GD推算）
```

---

### 問題二：台股美股報價嚴重錯誤

**發現的錯誤股價（舊→正確）：**

| 代號 | 舊錯誤價 | 正確價（GD） | 影響 |
|------|---------|-----------|------|
| 0056 元大高股息 | 40.5元 | 50.20元 | 估值+76萬 |
| 006208 富邦台50 | 80.5元 | 233元 | 估值+308萬 |
| 00881 國泰科技龍頭 | 20.3元 | 51.15元 | 估值+107萬 |
| 00927 群益半導體收益 | 22.5元 | 35.83元 | 估值+67萬 |
| 00935 野村新科技50 | 19.8元 | 55.15元 | 估值+109萬 |
| 5483 中美晶 | 65元 | 204元 | 估值+97萬 |
| 6147 頎邦 | 55元 | 155元（跌停後） | 估值+30萬 |

**解法：** 在 Google Sheets（RetireFlow_DB.xlsx）的個股後面加入股價欄，Claude 每次讀取時直接用真實報價計算。

---

### 問題三：自動抓取股價機制失敗

**嘗試方案：**
1. TWSE MIS API（`mis.twse.com.tw`）→ CORS 問題，瀏覽器端無法直接呼叫
2. Yahoo Finance API（`query1.finance.yahoo.com`）→ 同樣 CORS 限制

**最終解法：Google Sheets GOOGLEFINANCE 函式**

在 RetireFlow_DB.xlsx 新增「股價」工作表，D 欄填入公式：

```
=GOOGLEFINANCE("TPE:0050","price")     # 台股
=GOOGLEFINANCE("NASDAQ:NVDA","price")  # 美股
=GOOGLEFINANCE("TYO:2644","price")     # 日股
=GOOGLEFINANCE("CURRENCY:USDTWD")      # 匯率
```

Google Sheets 每 15 分鐘自動更新，Claude 每次更新儀表板時讀取 D 欄真實股價注入 HTML。

**工作表格式：**

| A（代號） | B（名稱） | C（市場） | D（收盤價/公式） |
|----------|---------|---------|----------------|
| 0050 | 元大台灣50 | 台股 | =GOOGLEFINANCE("TPE:0050","price") |
| NVDA | NVIDIA | 美股 | =GOOGLEFINANCE("NASDAQ:NVDA","price") |
| 2644 | 日本REITs ETF | 日股 | =GOOGLEFINANCE("TYO:2644","price") |
| USDTWD | 美元/台幣 | 匯率 | =GOOGLEFINANCE("CURRENCY:USDTWD") |

---

### 問題四：台股美股各券商明細表未出現

**原因：** HTML 容器 `div`（`id="tw-broker-table"`）沒有正確插入，`document.getElementById()` 回傳 null 直接 return。

**解法：** 用精確的 HTML 注釋標記定位插入點：

```python
# 在「美股 Pareto」分頁標記前面插入容器
html = html.replace(
    '</div>\n\n<!-- ════ 美股 Pareto ════ -->',
    BROKER_DIV + '</div>\n\n<!-- ════ 美股 Pareto ════ -->'
)
```

同時把 `renderBrokerTable` 移到 `switchTab` 直接呼叫（繞過 `chartsInit` 快取）：

```javascript
function switchTab(el, name){
  // ...tab 切換邏輯...
  setTimeout(()=>{
    drawTabCharts(name);
    if(name==='pareto-tw') renderBrokerTable(window.TW_BROKER,'tw-broker-table','TWD');
    if(name==='pareto-us') renderBrokerTable(window.US_BROKER,'us-broker-table','USD');
  }, 60);
}
```

---

### 問題五：所有圖表反覆失效（最常見問題）

#### 根本原因彙整

**Bug A — `TYPE_C` 常數未定義**

`buildHBar` 執行時用 `TYPE_C[d.type]` 決定顏色，常數被誤刪後整張圖表噴錯中止。

```javascript
// 必須在 buildHBar 之前定義
const TYPE_C = {
  "個股":"#E24B4A", "ETF":"#378ADD", "槓桿":"#EF9F27",
  "主動ETF":"#1D9E75", "現金替代":"#7F77DD"
};
```

**Bug B — `<script src="chart.umd.js">` 未閉合**

```html
<!-- ❌ 錯誤：JS 寫在 src script 標籤裡，瀏覽器忽略 -->
<script src="chart.umd.js">
const DARK = ...
function buildHBar(){...}
</script>

<!-- ✅ 正確：兩個 script 分開 -->
<script src="chart.umd.js"></script>
<script>
const DARK = ...
function buildHBar(){...}
</script>
```

**Bug C — `TW_BROKER=TW_BROKER||{...}` 引用未定義變數**

```javascript
// ❌ 錯誤：TW_BROKER 這個名稱從未定義，直接 ReferenceError
window.TW_BROKER = TW_BROKER || { ... }

// ✅ 正確：直接賦值
window.TW_BROKER = { ... }
```

**Bug D — `chartsInit` 作用域不一致**

```javascript
// ❌ 錯誤：let 是區塊作用域，window.chartsInit={} 清空無效
let chartsInit = {};
// 在 loadLivePrices 裡：
window.chartsInit = {};  // 清空的是 window.chartsInit，不是 let chartsInit

// ✅ 正確：統一用 window
window.chartsInit = {};
// 所有地方都用 window.chartsInit[name]
```

**Bug E — JP_DATA 陣列替換時，舊 labelPlugin 程式碼殘留其後**

每次替換 `window.JP_DATA=[...]` 區塊時，若用 `replace(old_block, new_block)` 且 `old_block` 邊界不精確，舊 `buildHBar` 的 label plugin 程式碼（~1.3萬字元）會殘留在 JP_DATA 結尾後，導致語法錯誤。

**解法：** 精確定位 `window.JP_DATA` 結束（`];\n`）到 `// ── Donut ──` 之間，清除所有殘留。

```python
idx_jp_end = js.find(jp_end_marker, idx_jp_start) + len(jp_end_marker)
idx_donut  = js.find('\n// ── Donut ──')
js_clean   = js[:idx_jp_end] + js[idx_donut:]  # 清除殘留程式碼
```

**Bug F — `renderBrokerTable` 函式被誤刪**

多次替換操作後，`renderBrokerTable` 消失，導致台股美股券商明細表無法渲染。

---

## 安全更新 SOP（往後每次更新必須遵守）

### 1. 更新數據前，先備份
```python
shutil.copy('/tmp/retireflow_full.html', '/tmp/retireflow_backup.html')
```

### 2. 替換 JS 數據區塊，用精確邊界
```python
# 找開始位置
idx_start = html.find('window.TW_DATA=\n[')
# 找結束位置（第一個 ];）
idx_end = html.find('];\n', idx_start) + 3
# 只替換數據部分，不碰後面的程式碼
html = html[:idx_start] + 'window.TW_DATA=\n' + new_data + '\n' + html[idx_end:]
```

### 3. 每次修改後執行 JS 語法驗證
```python
js = html[html.rfind('<script>')+8:html.rfind('</script>')]
with open('/tmp/check.js','w') as f: f.write(js)
r = subprocess.run(['node','--check','/tmp/check.js'],capture_output=True,text=True)
assert r.returncode == 0, r.stderr
```

### 4. 驗證關鍵函式完整性
```python
must_have = ['function drawGauge','function buildHBar','function buildDonut',
             'function mkLine','function drawAllCharts','function drawTabCharts',
             'function switchTab','function rebuildPortfolioData',
             'function renderBrokerTable','const TYPE_C=']
for fn in must_have:
    assert fn in html, f"❌ 缺少: {fn}"
```

### 5. 確認靜態數字與 Google Drive 一致
```python
assert f'>{total_w:,}<span' in html, "總資產數字未更新"
assert f'>{net_w:,}<span'   in html, "淨資產數字未更新"
```

---

## 每次更新儀表板流程

```
Will 說：「依照參考股價，更新儀表板」
    ↓
Claude 讀取 Google Drive（工作表1 + 資產歷史紀錄）
    ↓
從最新一列取得：總資產、各類別、負債
從持股明細取得：各檔股數＋股價
    ↓
計算推算匯率（USD/JPY → TWD）
    ↓
重算 TW_DATA、US_DATA、JP_DATA、TW_BROKER、US_BROKER
    ↓
替換 HTML 靜態數字（總資產/淨資產/達成率/各類別）
更新 drawGauge 呼叫參數
更新 FALLBACK_PRICES（API 失敗時備用）
    ↓
node --check 語法驗證 + 關鍵函式完整性驗證
    ↓
Push GitHub Pages
```

---

## 關鍵 JS 結構（必須保持完整）

```javascript
// [1] Chart.js CDN（獨立 script）
<script src="chart.umd.js"></script>

// [2] 自訂 JS（獨立 script，不能混入 CDN script）
<script>
const DARK = matchMedia('(prefers-color-scheme:dark)').matches;
const GC = DARK ? 'rgba(255,255,255,0.07)' : 'rgba(0,0,0,0.06)';
const TC = DARK ? '#555' : '#aaa';

// ← TYPE_C 必須在這裡定義，在 buildHBar 之前
const TYPE_C = {
  "個股":"#E24B4A","ETF":"#378ADD","槓桿":"#EF9F27",
  "主動ETF":"#1D9E75","現金替代":"#7F77DD"
};

// ← rebuildPortfolioData 必須在此（動態更新數據）
function rebuildPortfolioData(){ ... }

// ← 靜態初始值（rebuildPortfolioData 執行後會被覆蓋）
window.TW_DATA = [ ... ];
window.US_DATA = [ ... ];
window.JP_DATA = [ ... ];
window.TW_BROKER = { ... };
window.US_BROKER = { ... };

// ← 以下函式缺一不可
function drawGauge(id, pct, label, color){ ... }
function buildHBar(canvasId, data, title){ ... }
function renderBrokerTable(brokerData, containerId, currency){ ... }
function buildDonut(canvasId, data){ ... }
function mkLine(id, ds, pct){ ... }
function drawAllCharts(){ ... }
function drawTabCharts(name){ ... }
function switchTab(el, name){ ... }
function calcRetire(){ ... }
// ← 月曆函式群
function renderCalendar(){ ... }
function renderWeeklyTable(...){ ... }
function renderMiniChart(ym){ ... }
function navMonth(dir){ ... }

document.addEventListener('DOMContentLoaded', () => {
  rebuildPortfolioData();
  drawAllCharts();
  drawTabCharts('overview');
  calcRetire();
  loadLivePrices();  // 非同步抓取最新股價
});
</script>
```

---

## 目前持股 Canvas 對應

| Canvas ID | 分頁 | 函式 | 高度 |
|-----------|------|------|------|
| g-tw/us/jp/fd | 油表（常駐） | drawGauge | 65px |
| overviewDonut | 總覽 | buildDonut | 190px |
| growthChart | 成長波動 | Chart.js bar | 260px |
| volChart | 成長波動 | mkLine | 220px |
| radarChart | 配置分析 | Chart.js radar | 190px |
| twPareto | 🇹🇼 台股 | buildHBar | 520px |
| twDonut | 🇹🇼 台股 | buildDonut | 190px |
| usPareto | 🇺🇸 美股 | buildHBar | 480px |
| usDonut | 🇺🇸 美股 | buildDonut | 190px |
| jpPareto | 🇯🇵 日股 | buildHBar | 200px |
| fundPareto | 📦 基金 | buildHBar | 180px |
| trendChart | 📉 走勢圖 | mkLine | 260px |
| allocChart | 📉 走勢圖 | mkLine | 260px |
| barChart | 📉 走勢圖 | Chart.js bar | 160px |
| calMiniChart | 📅 月曆 | Chart.js combo | 160px |

---

## 版本紀錄

| 版本 | 日期 | 主要更新 |
|------|------|---------|
| v3.3 | 07/27 | 三版合一（13分頁）、Pareto→橫向Bar、資產月曆 |
| v3.3.1 | 07/27 | Bar Chart 加入萬元+%標籤、修復 JS script 結構 |
| v3.3.2 | 07/28 | 修正台股美股錯誤報價（006208/00881/5483等） |
| v3.3.3 | 07/28 | 補入台股美股各券商明細表（HTML 容器+JS 渲染） |
| v3.3.4 | 07/28 | 自動股價系統（GOOGLEFINANCE 架構設計完成） |
| v3.3.5 | 07/28 | 修復 TYPE_C 缺失+renderBrokerTable 遺失 |
| **v3.4** | **07/28** | **全數據核對（GD驗算零誤差）、完整 SOP 建立** |

---

## 常見問題快速排查

| 症狀 | 可能原因 | 解法 |
|------|---------|------|
| 圖表空白/載入中 | `TYPE_C` 未定義 | 確認 `const TYPE_C={...}` 在 JS 開頭 |
| 圖表空白/載入中 | `drawGauge` 或 `buildHBar` 遺失 | `grep 'function drawGauge'` 確認存在 |
| 圖表空白/載入中 | Chart.js script 未閉合 | 確認 `chart.umd.js"></script>` 有 `>` 閉合 |
| 數字不更新 | 靜態 HTML 未替換 | 搜尋舊數字（如 8392）確認已全部換掉 |
| 券商明細表空白 | div 容器不存在 | 確認 `id="tw-broker-table"` 在 HTML body 中 |
| 數據更新後圖表不重繪 | `chartsInit` 快取 | 確認用 `window.chartsInit` 而非 `let chartsInit` |
| JS 語法錯誤 | 數據替換邊界不精確 | 用 `node --check` 驗證，找殘留程式碼 |

---

*RetireFlow Pro v3.4｜僅供個人財務規劃參考，不構成投資建議*
