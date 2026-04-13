# openclaw-calendar-plugin

第一版目標：

- 查今天行程
- 查明天行程
- 查本週行程
- 查指定日期
- 新增行程
- 刪除行程

## 不做
- 背景提醒掃描
- 主動推播提醒
- 找空檔
- 修改事件

## 目前狀態
這是一個 plugin 骨架：
- `openclaw.plugin.json` 已定義 6 個 tools
- `src/index.ts` 已註冊 6 個 tools
- `src/runtime/calendar-runtime.ts` 目前還是 TODO stub

## 下一步
把你現在 Python `calendar_service` 的已測通邏輯搬到 runtime 層，或改成由 runtime 呼叫現有 Python 腳本/API。
