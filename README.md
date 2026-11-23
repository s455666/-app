# 果實時光 — 水果播種成熟日計算機

以 Flask 3、Python 3.12 與 Jinja2 建置的繁體中文響應式網站。提供 14 種水果估算、自訂天數、環境校正、生長階段時間軸、栽培提示，以及 Open-Meteo 今日天氣建議。外部天氣服務失效時會降級顯示友善提示，不影響日期計算。

## 本機啟動

需要 Python 3.12。於專案根目錄執行：

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python app.py
```

瀏覽 <http://127.0.0.1:5000>。Open-Meteo 不需要 API 金鑰；網路或服務不可用時，網站仍可計算成熟日期。

## API

- `GET /api/fruits`：取得水果清單、參考天數與照護資料。
- `POST /api/calculate`：JSON 欄位 `fruit`、`sowing_date`（`YYYY-MM-DD`）、`environment`、`city`；自訂水果另提供 `custom_name`、`custom_days`。錯誤輸入回傳 HTTP 400 JSON。

## 部署至 Vercel

1. 將此專案推送至 GitHub。
2. 在 Vercel 選擇 **Add New → Project**，匯入該 GitHub repository。
3. Framework Preset 選 **Other**，保留根目錄設定並部署。`vercel.json` 會使用 Vercel Python runtime 將所有路由導向根目錄 `app.py`；不需要設定秘密環境變數。
4. 後續推送至連結的分支即可觸發部署。

## GitHub 推送

若尚未建立 Git repository：

```powershell
git init
git add .
git commit -m "建立果實時光水果成熟日計算器"
git branch -M main
git remote add origin https://github.com/你的帳號/你的儲存庫.git
git push -u origin main
```

已連結遠端 repository 時，提交後使用 `git push`。請勿提交 `.env`；可複製 `.env.example` 作為本機設定範本。
