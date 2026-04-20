# Calendar Assistant

Google Calendar 助手，能夠透過 OpenClaw 或 Telegram 接收訊息，依需求以固定格式或自然語言解析後呼叫同一支 Python writer 寫入或修改事件。

## 功能摘要

- **雙模式輸入**：
  - 固定格式 `YYYY-MM-DD HH:MM ~ HH:MM | 標題` 或 `YYYY-MM-DD | 標題` (全天)。
  - 自然語言模式透過 LLM 解析（可指定 `LLM_MODEL`）。
- **單一寫入層**：所有解析結果都交由 `calendar_writer.py` 使用 Google Calendar API 寫入/更新。
- **修改事件**：依「日期 + 標題」搜尋，若結果多筆會回傳候選要求人工挑選。
- **Telegram/OpenClaw**：
  - `app.py` 內建 CLI，亦示範 telegram handler。OpenClaw 可直接於 CLI 模式呼叫。
- **Railway 部署友善**：支援 `SERVICE_ACCOUNT_JSON` 環境變數直接載入，不需要先寫檔案。

## 專案結構

```
calendar_assistant/
├─ app.py                # CLI 與 Telegram handler
├─ calendar_writer.py    # Google Calendar API 包裝
├─ parser.py             # 輸入解析 (固定/自然語言)
├─ config.py             # 環境設定載入
├─ secrets/
│  └─ service-account.json (本地測試需要，可留空模板)
├─ requirements.txt
└─ README.md
```

## 安裝與本地測試

```bash
cd calendar_assistant
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

必要環境變數：

| 變數 | 說明 |
| --- | --- |
| `CALENDAR_ID` | 目標 Google Calendar，例如 `xxxxxxxxxxxx@group.calendar.google.com` |
| `SERVICE_ACCOUNT_JSON` | （推薦）直接貼上整份 JSON；程式會用 `from_service_account_info` 載入 |
| `SERVICE_ACCOUNT_PATH` | 若未設 `SERVICE_ACCOUNT_JSON`，才會改讀這個檔案，預設 `secrets/service-account.json` |
| `CALENDAR_TIMEZONE` | 預設 `Asia/Taipei` |
| `OPENAI_API_KEY` / `LLM_MODEL` / `OPENAI_BASE_URL` | 自然語言模式設定 |
| `TELEGRAM_BOT_TOKEN` | 使用 `--telegram` 時必填 |

### Service Account 與 Calendar 設定

1. 建立 Service Account 並啟用 Calendar API。
2. 產生 JSON 金鑰：
   - 本地開發：把 JSON 放到 `secrets/service-account.json`。
   - Railway：直接將 JSON 內容貼到 `SERVICE_ACCOUNT_JSON` 變數即可，無需手動寫檔。
3. 將目標 Google Calendar 分享給該 service account email（給「製作與管理活動」權限）。
4. 設定 `CALENDAR_ID` 為該日曆的 ID。

### CLI / Telegram 使用

與前述相同，`python app.py` 可測新增、`--update` 可測修改；`update:` 前綴會走修改流程。Telegram 模式請先設 `TELEGRAM_BOT_TOKEN`。

## Railway 部署流程

1. Push 此專案到 GitHub，並確保 `secrets/` 下的實際金鑰未提交。
2. Railway 建立新服務，選 Python。Build Command `pip install -r requirements.txt`，Start Command `python app.py`（或自訂）。
3. Variables 中至少放入：
   - `CALENDAR_ID`
   - `SERVICE_ACCOUNT_JSON`（整段 JSON）
   - `OPENAI_API_KEY`、`LLM_MODEL`（自然語言所需）
   - `TELEGRAM_BOT_TOKEN`（若要 Telegram）
4. 由於程式已支援 `SERVICE_ACCOUNT_JSON`，無須再額外寫檔；Railway 會直接將 JSON 字串載入。
5. 若要給 OpenClaw 使用，可另外在 `app.py` 增加 FastAPI/Flask webhook，或改 Start Command 為 `uvicorn ...`。

## OpenClaw + Telegram 流程建議

1. OpenClaw/Telegram 接受訊息。
2. 偵測格式：固定格式直接送至 `/process_text`，否則送至自然語言模式或先由 OpenClaw LLM 解析後以 JSON 呼叫。
3. `calendar_writer` 僅負責寫入/更新，確保權限集中。
4. 修改流程：若回傳 `status=needs_selection`，請使用者回覆選擇索引，再次呼叫 `process_update`。

## 未來擴充

- 為 OpenClaw 建立 HTTP API。
- 支援多個 Calendar/多使用者 Profile。
- 增加提醒、描述等欄位對應。
