# RetireFlow 退休財務儀表板

自動從 `RetireFlow_DB.xlsx` 讀取資料，產生互動式退休財務儀表板，部署於 GitHub Pages。

## 快速開始

### 1. Fork 或 Clone 這個 Repo

```bash
git clone https://github.com/你的帳號/retireflow.git
cd retireflow
```

### 2. 放入你的 Excel 檔

把 `RetireFlow_DB.xlsx` 放到專案根目錄（和 `index.html` 同層）。

> ⚠️ 如果檔案含有個人資料，建議設定 Repo 為 **Private**。

### 3. 啟用 GitHub Pages

1. GitHub Repo 頁面 → **Settings**
2. 左側 **Pages**
3. Source 選 **Deploy from a branch**
4. Branch 選 **main**，目錄選 **/ (root)**
5. 按 **Save**

約 1 分鐘後，網址 `https://你的帳號.github.io/retireflow/` 就上線了。

---

## 更新方式

### 方式 A：手動 git push（每次更新後自己推）

```bash
# 1. 更新 RetireFlow_DB.xlsx

# 2. 在本機產生新 HTML
pip install openpyxl
python scripts/generate.py RetireFlow_DB.xlsx

# 3. 推上 GitHub（Pages 會自動更新）
git add .
git commit -m "更新資產 $(date +'%Y/%m/%d')"
git push
```

### 方式 B：GitHub Actions 自動排程

每天台灣時間 09:00 自動執行，前提是：

1. **把 `RetireFlow_DB.xlsx` 保持在 repo 裡並定期 push 更新**
2. GitHub Actions 會自動讀取最新 xlsx → 產生 HTML → push 回去
3. GitHub Pages 自動發布

#### 手動觸發（臨時更新）
GitHub Repo → **Actions** → **更新 RetireFlow 儀表板** → **Run workflow**

---

## 手機加入主畫面（像 App 一樣）

**iOS Safari：**
1. 開啟 `https://你的帳號.github.io/retireflow/`
2. 點下方分享圖示 ⎋
3. 選「**加入主畫面**」
4. 名稱填 `RetireFlow` → 新增

**Android Chrome：**
1. 開啟網址
2. 右上角 ⋮ → 「**新增至主畫面**」

---

## 本機測試

```bash
pip install openpyxl
python scripts/generate.py RetireFlow_DB.xlsx
open index.html   # macOS
# 或直接用瀏覽器開啟 index.html
```

---

## 工作表結構（RetireFlow_DB.xlsx）

| 工作表名稱 | 說明 |
|-----------|------|
| 工作表1 | 持股明細（市場/券商/代號/股數/殖利率/名稱） |
| 基金帳戶 | 基金總額（名稱/平台/金額/殖利率） |
| 負債清單 | 負債（項目/機構/餘額/利率） |
| 資產歷史紀錄 | 每日快照（日期/總資產/總負債/淨資產/股息/台股/美股/日股/基金） |

---

*RetireFlow v2.0 ｜ 僅供個人財務規劃參考，不構成投資建議*
