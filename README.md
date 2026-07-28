# RetireFlow Pro v3.4 開發日誌

> 最後更新：2026/07/28
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

**解法：** 每次從 Google Drive 歷史記錄反推正確匯率後等比例分配各持股。

```python
jpy_twd = gd_jp_total / sum(shares * price for each jp stock)  # 每次動態推算
```

---

### 問題二：台股美股報價嚴重錯誤

**發現的錯誤股價（舊→正確）：**

| 代號 | 舊錯誤價 | 正確價（GD） | 影響 |
|------|---------|-----------|------|
| 0056 元大高股息 | 40.5元 | 50.20元 | 估值+76萬 |
| 006208 富邦台50 | 80.5元 | 233元 | 估值+308萬 |
| 00881 國泰科技龍頭 | 20.3元 | 51.15元 | 估值+107萬 |
| 00935 野村新科技50 | 19.8元 | 55.15元 | 估值+109萬 |
| 5483 中美晶 | 65元 | 204元 | 估值+97萬 |
| 6147 頎邦 | 55元 | 155元（跌停後） | 估值+30萬 |

**解法：** 在 Google Sheets（RetireFlow_DB.xlsx）的個股後面加入股價欄，Claude 每次讀取時直接用真實報價計算。

---

### 問題三：自動抓取股價機制（結論）

**嘗試方案：**
1. TWSE MIS API → CORS 限制，瀏覽器端無法直接呼叫
2. Yahoo Finance API → 同樣 CORS 限制

**最終確定流程：Google Sheets GOOGLEFINANCE 函式**

在 RetireFlow_DB.xlsx 工作表1 的股數後面加入股價欄，用公式自動更新：

```
=GOOGLEFINANCE("TPE:0050","price")     # 台股
=GOOGLEFINANCE("NASDAQ:NVDA","price")  # 美股
=GOOGLEFINANCE("TYO:2644","price")     # 日股
=GOOGLEFINANCE("CURRENCY:USDTWD")      # 匯率
```

Will 更新完 Google Sheets 後，對 Claude 說「依照參考股價，更新儀表板」即可。

---

### 問題四：台股美股各券商明細表未出現

**原因：** HTML 容器 `div`（`id="tw-broker-table"`）沒有正確插入，`document.getElementById()` 回傳 null 直接 return。

**解法：** 用精確的 HTML 注釋標記定位插入點，並把 `renderBrokerTable` 移到 `switchTab` 直接呼叫（繞過 `chartsInit` 快取）：

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

### 問題五：基金頁面 Bar Chart 無法顯示

**根本原因：作用域錯誤（Scope Bug）**

```javascript
// ❌ 問題：FD_DATA 被困在 rebuildPortfolioData() 函式內部
function rebuildPortfolioData() {
  // ... 大量程式碼 ...
  const FD_DATA = [...];  // 只有函式內部能看到！
}

// drawTabCharts 呼叫時：
buildHBar('fundPareto', FD_DATA, ...)  // FD_DATA 在外部 = undefined
```

台股/美股/日股 用 `window.TW_DATA`、`window.US_DATA`、`window.JP_DATA`（全域）正常。
基金用 `const FD_DATA`（函式作用域），外部看不到 → `buildHBar` 拿到 `undefined` → 不渲染。

**解法：** 將 `FD_DATA` 移至頂層全域：

```javascript
// ✅ 正確：頂層定義，全域可見
window.FD_DATA = [
  {code:"鉅亨", name:"鉅亨網基金", val:411.4, type:"ETF"},
  {code:"HSBC", name:"HSBC結構型", val:314.5, type:"現金替代"},
  {code:"基富通", name:"基富通基金", val:142.7, type:"ETF"}
];
```

**驗證方法：** 計算 `const FD_DATA=` 定義時的大括號深度，必須為 0（頂層）：

```python
depth = 0
for ch in js[:fd_idx]:
    if ch == '{': depth += 1
    elif ch == '}': depth -= 1
assert depth == 0, f"FD_DATA 不在頂層！深度={depth}"
```

**額外措施：** 基金分頁改用純 HTML 橫向進度條（不依賴 Chart.js），保證任何情況下都能顯示：

```javascript
if(name === 'fund'){
  const fw = document.getElementById('fundBarWrap');
  const items = [...]; // 直接寫入數據
  fw.innerHTML = items.map(it => `
    <div>...</div>  // 純 HTML bar
  `).join('');
  delete window.chartsInit['fund'];  // 允許下次重繪
}
```

**為什麼台股/美股/日股沒有這個問題？**
因為它們的數據陣列從一開始就定義為 `window.TW_DATA` 全域變數，從未放進函式內部。

---

### 問題六：所有圖表反覆失效（彙整）

#### Bug A — `TYPE_C` 常數未定義

`buildHBar` 執行時用 `TYPE_C[d.type]` 決定顏色，常數被誤刪後整張圖表 crash。

```javascript
// 必須在 buildHBar 之前定義，置於頂層
const TYPE_C = {
  "個股":"#E24B4A", "ETF":"#378ADD", "槓桿":"#EF9F27",
  "主動ETF":"#1D9E75", "現金替代":"#7F77DD"
};
```

#### Bug B — `<script src="chart.umd.js">` 未閉合

```html
<!-- ❌ 錯誤 -->
<script src="chart.umd.js">
  const DARK = ...
</script>

<!-- ✅ 正確：兩個 script 分開 -->
<script src="chart.umd.js"></script>
<script>
  const DARK = ...
</script>
```

#### Bug C — `TW_BROKER=TW_BROKER||{}` 引用未定義變數

```javascript
// ❌ 錯誤：TW_BROKER 未定義，ReferenceError
window.TW_BROKER = TW_BROKER || { ... }

// ✅ 正確
window.TW_BROKER = { ... }
```

#### Bug D — `chartsInit` 作用域不一致

```javascript
// ❌ 錯誤：let 與 window.chartsInit 是不同變數
let chartsInit = {};
window.chartsInit = {};  // 清空的不是同一個

// ✅ 正確：統一用 window.chartsInit
window.chartsInit = {};
```

#### Bug E — JP_DATA 替換殘留舊程式碼

替換 `window.JP_DATA=[...]` 區塊時，若邊界不精確，舊 `buildHBar` 的 label plugin（~1.3萬字元）會殘留其後，導致語法錯誤。

**解法：** 精確定位結束邊界，清除殘留：

```python
idx_jp_end = js.find('];\n', idx_jp_start) + 3
idx_donut  = js.find('\n// ── Donut ──')
js_clean   = js[:idx_jp_end] + js[idx_donut:]
```

#### Bug F — `renderBrokerTable` 函式被誤刪

多次替換操作後消失。補入完整函式後加入必要函式驗證清單。

#### Bug G — `buildHBar` 未加 `Chart.destroy()`

同一個 canvas 被 `new Chart()` 初始化兩次，Chart.js 拒絕渲染。

```javascript
function buildHBar(canvasId, data, title){
  const ctx = document.getElementById(canvasId); if(!ctx) return;
  // ✅ 先銷毀舊實例
  const existing = Chart.getChart(ctx);
  if(existing) existing.destroy();
  // 再建立新的...
}
```

#### Bug H — US_DATA / JP_DATA 無靜態初始值

只在 `rebuildPortfolioData` 動態生成，但 `drawTabCharts` 在動態生成前就可能被呼叫。

**解法：** 在頂層加入靜態初始值（同 TW_DATA），確保頁面一開啟就有數據：

```javascript
// 頂層靜態初始值（rebuildPortfolioData 執行後會被覆蓋為最新值）
window.TW_DATA = [...];
window.US_DATA = [...];  // ← 必須有
window.JP_DATA = [...];  // ← 必須有
window.FD_DATA = [...];  // ← 必須有（不能用 const）
```

---

## 安全更新 SOP（每次更新必執行）

### 1. 替換 JS 數據用精確邊界

```python
# 找開始
idx = html.find('window.TW_DATA=\n[')
# 找結束（第一個 ];）
end = html.find('];\n', idx) + 3
# 只替換數據，不碰周圍程式碼
html = html[:idx] + 'window.TW_DATA=\n' + new_data + ';\n' + html[end:]
```

### 2. JS 語法驗證（必做）

```python
js = html[html.rfind('<script>')+8:html.rfind('</script>')]
with open('/tmp/check.js','w') as f: f.write(js)
r = subprocess.run(['node','--check','/tmp/check.js'],capture_output=True,text=True)
assert r.returncode == 0, r.stderr
```

### 3. 關鍵函式完整性驗證（必做）

```python
must_have = [
    'function drawGauge',       # 油表
    'function buildHBar',       # 橫向 Bar（含 Chart.destroy()）
    'function buildDonut',      # 圓餅
    'function mkLine',          # 折線
    'function drawAllCharts',   # 初始化
    'function drawTabCharts',   # 分頁渲染
    'function switchTab',       # 分頁切換
    'function renderBrokerTable', # 券商明細表
    'function rebuildPortfolioData', # 動態重算
    'const TYPE_C=',            # 顏色常數（必須在頂層）
    'window.FD_DATA=',          # 基金數據（必須在頂層）
    'window.TW_DATA=\n[',       # 台股靜態初始值
    'window.US_DATA=\n[',       # 美股靜態初始值
    'window.JP_DATA=\n[',       # 日股靜態初始值
    'chart.umd.js"></script>',  # Chart.js 正確閉合
]
for fn in must_have:
    assert fn in html, f"❌ 缺少: {fn}"
```

### 4. 作用域深度驗證

```python
# 確認所有數據變數在頂層（深度=0）
js = html[html.rfind('<script>')+8:html.rfind('</script>')]
for var in ['window.TW_DATA','window.US_DATA','window.JP_DATA','window.FD_DATA',
            'window.TW_BROKER','window.US_BROKER','const TYPE_C']:
    idx = js.find(var)
    if idx < 0: continue
    depth = sum(1 if c=='{' else -1 if c=='}' else 0 for c in js[:idx])
    assert depth == 0, f"❌ {var} 不在頂層！深度={depth}"
```

---

## 每次更新儀表板流程

```
Will 說：「依照參考股價，更新儀表板」
    ↓
Claude 讀取 Google Drive（工作表1 + 資產歷史記錄）
    ↓
從最新一列取得：總資產、各類別、負債
從持股明細取得：各檔股數＋Google Finance 股價
    ↓
計算推算匯率（us_total / Σ(股數×USD股價) = USD/TWD）
                （jp_total / Σ(股數×JPY股價) = JPY/TWD）
    ↓
重算 TW_DATA、US_DATA、JP_DATA、FD_DATA
重算 TW_BROKER、US_BROKER（各券商明細）
    ↓
替換 HTML 靜態數字（總資產/淨資產/達成率/各類別）
更新 drawGauge 呼叫參數
更新 FALLBACK_PRICES
更新基金 HTML bar 的 items 數據
    ↓
node --check 語法驗證
關鍵函式 + 作用域深度驗證
    ↓
Push GitHub Pages
```

---

## 關鍵 JS 結構（完整版）

```html
<!-- [1] Chart.js CDN（獨立 script，必須正確閉合）-->
<script src="chart.umd.js"></script>

<!-- [2] 自訂 JS（獨立 script）-->
<script>
// ── 顏色與常數（頂層，必須最先定義）──
const DARK = matchMedia('(prefers-color-scheme:dark)').matches;
const GC = DARK ? 'rgba(255,255,255,0.07)' : 'rgba(0,0,0,0.06)';
const TC = DARK ? '#555' : '#aaa';
const TYPE_C = {"個股":"#E24B4A","ETF":"#378ADD","槓桿":"#EF9F27",
                "主動ETF":"#1D9E75","現金替代":"#7F77DD"};

// ── 基金數據（頂層全域，不能放進函式）──
window.FD_DATA = [...];

// ── 動態重算函式 ──
function rebuildPortfolioData() {
  // 根據 LIVE_PRICES 重算所有持股估值
  window.TW_DATA = [...];
  window.US_DATA = [...];
  window.JP_DATA = [...];
  window.TW_BROKER = {...};
  window.US_BROKER = {...};
}

// ── 靜態初始值（頁面載入時立即可用，rebuildPortfolioData 執行後覆蓋）──
window.TW_DATA = [...];  // 必須有
window.US_DATA = [...];  // 必須有
window.JP_DATA = [...];  // 必須有
window.TW_BROKER = {...};
window.US_BROKER = {...};

// ── 繪圖函式（缺一不可）──
function drawGauge(id, pct, label, color){ ... }
function buildHBar(canvasId, data, title){
  const ctx = document.getElementById(canvasId); if(!ctx) return;
  const existing = Chart.getChart(ctx);  // ← 必須先 destroy
  if(existing) existing.destroy();
  // ...new Chart(...)
}
function renderBrokerTable(brokerData, containerId, currency){ ... }
function buildDonut(canvasId, data){ ... }
function mkLine(id, ds, pct){ ... }
function drawAllCharts(){ ... }
function drawTabCharts(name){
  if(window.chartsInit[name]) return;
  window.chartsInit[name] = 1;
  // ...各分頁渲染邏輯...
  // 基金分頁用純 HTML bar：
  if(name==='fund'){
    const fw = document.getElementById('fundBarWrap');
    fw.innerHTML = items.map(it=>`<div>...</div>`).join('');
    delete window.chartsInit['fund'];  // 允許下次重繪
  }
}
function switchTab(el, name){
  // ...切換 active class...
  setTimeout(()=>{
    drawTabCharts(name);
    if(name==='calendar') renderCalendar();
    if(name==='pareto-tw') renderBrokerTable(window.TW_BROKER,'tw-broker-table','TWD');
    if(name==='pareto-us') renderBrokerTable(window.US_BROKER,'us-broker-table','USD');
  }, 60);
}
function calcRetire(){ ... }
// ── 月曆函式群 ──
function renderCalendar(){ ... }
function renderWeeklyTable(...){ ... }
function renderMiniChart(ym){ ... }
function navMonth(dir){ ... }

// ── 初始化 ──
window.chartsInit = {};
document.addEventListener('DOMContentLoaded', () => {
  rebuildPortfolioData();
  drawAllCharts();
  drawTabCharts('overview');
  calcRetire();
  loadLivePrices();
});
</script>
```

---

## 版本紀錄

| 版本 | 日期 | 主要更新 |
|------|------|---------|
| v3.3 | 07/27 | 13分頁、橫向Bar、資產月曆 |
| v3.3.1 | 07/27 | Bar Chart 百分比標籤、JS script 結構修正 |
| v3.3.2 | 07/28 | 修正台股美股錯誤報價 |
| v3.3.3 | 07/28 | 補入台股美股各券商明細表 |
| v3.3.4 | 07/28 | GOOGLEFINANCE 股價架構設計完成 |
| v3.3.5 | 07/28 | 修復 TYPE_C 缺失＋renderBrokerTable 遺失 |
| v3.4.0 | 07/28 | 全數據核對零誤差，完整 SOP 建立 |
| **v3.4.1** | **07/28** | **根本修復基金作用域Bug（FD_DATA→window.FD_DATA）；加入 US_DATA/JP_DATA 靜態初始值；buildHBar 加入 Chart.destroy()** |

---

## 常見問題快速排查

| 症狀 | 可能原因 | 解法 |
|------|---------|------|
| 圖表空白 | `TYPE_C` 未定義 | 確認 `const TYPE_C={...}` 在頂層 |
| 圖表空白 | `drawGauge`/`buildHBar` 遺失 | node --check + 函式清單驗證 |
| 圖表空白 | Chart.js script 未閉合 | 確認 `chart.umd.js"></script>` |
| 圖表空白 | 數據變數 undefined | 確認所有 window.XXX 在頂層（深度=0） |
| **基金頁空白** | **`FD_DATA` 在函式內部** | **改成 `window.FD_DATA` 頂層定義** |
| 數字不更新 | 靜態 HTML 未替換 | 搜尋舊數字確認全部換掉 |
| 券商明細表空白 | div 容器不存在 | 確認 `id="tw-broker-table"` 在 HTML body |
| 數據更新後圖表不重繪 | `chartsInit` 快取 | 統一用 `window.chartsInit` |
| Canvas is already in use | 未 destroy 舊 Chart | `Chart.getChart(ctx)?.destroy()` |
| JS 語法錯誤 | 替換邊界不精確造成程式碼殘留 | node --check，清除 JP_DATA 後殘留 |

---

*RetireFlow Pro v3.4.1｜僅供個人財務規劃參考，不構成投資建議*

---

## 更新記錄

### 2026/07/28 儀表板更新

| 指標 | 數值 | 較前日 |
|------|------|------|
| 總資產 | 7,942萬 | ↓ -293.5萬（-3.56%） |
| 淨資產 | 3,673萬 | |
| 退休達成率 | 49.6% | 跌破 50% |
| USD/TWD | 32.39 | |
| JPY/TWD | 0.1957 | |
| 台股 | 4,209萬（42.1%） | |
| 美股 | 2,249萬（56.2%） | |
| 日股 | 615萬（61.5%） | |
| 基金 | 869萬（86.9%） | |

主因：台股全面走軟，台積電 2350→2280（-70元）、006208（222元）、0050（97.15元）均下跌。

---

### 問題九：資產月曆未隨儀表板自動更新

**原因：** `CAL_DATA` 是獨立維護的靜態字典，「更新儀表板」流程只更新股票數據和指標，沒有包含月曆條目追加。

**修正：** 往後每次「更新儀表板」一併補入當日月曆條目。

```python
# 從 Google Drive 最新一列計算當日條目
new_entry = {
    "date": "2026-07-28",
    "v": round(today_total / 10000),            # 萬元
    "c": round((today_total - prev_total) / 10000, 1),   # 日變化（萬）
    "p": round((today_total - prev_total) / prev_total * 100, 2),  # 日報酬%
}
# 插入在前一日條目結束 } 之後
new_cal_entry = f',"{date}":{{"v":{v},"c":{c},"p":{p}}}'
html = html[:entry_end] + new_cal_entry + html[entry_end:]
```

**月曆顏色規則：**
- ≥ +3%：深綠
- +1~3%：淺綠
- -1~+1%：灰
- -1~-3%：淺紅
- ≤ -3%：深紅（7/28 適用）

**更新後月曆筆數：** 71 筆（2026/05/01 ～ 2026/07/28）

---

### 更新流程補充（完整版）

```
Will 說：「更新儀表板」
    ↓
Claude 讀取 Google Drive（工作表1 持股+股價 + 資產歷史最新列）
    ↓
推算匯率、重算所有持股估值
重建 TW_DATA / US_DATA / JP_DATA / FD_DATA
重建 TW_BROKER / US_BROKER
    ↓
替換 HTML 靜態數字（總資產/淨資產/達成率/各類別）
更新 drawGauge 油表呼叫參數
更新 FALLBACK_PRICES
更新基金 HTML bar items
    ↓
【新增】追加 CAL_DATA 當日條目（v/c/p）
    ↓
node --check JS 語法驗證
    ↓
Push GitHub Pages
```
