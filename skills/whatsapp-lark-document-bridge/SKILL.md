---
name: whatsapp-lark-document-bridge
description: |
  Bridges WhatsApp messages to Lark document operations (read, insert, update, create todo).
  Triggers when a WhatsApp message contains "@Lark" followed by an operation command.
  Supports both Chinese and English:
    Chinese: @Lark 查詢, @Lark 新增, @Lark 更新, @Lark 待辦
    English: @Lark query, @Lark insert, @Lark update, @Lark todo
  Auto-detects language and responds in the same language.
  Outputs structured JSON + human-readable summary. Ignored if no "@Lark" marker.
tags: [lark, whatsapp, document, bridge, bilingual]
related_skills: [lark-task-daily-reminder]
trigger: |
  ALWAYS trigger when a WhatsApp message contains "@Lark" followed by a Lark document
  operation. Supports BOTH Chinese AND English commands:

  Chinese triggers:
  - @Lark 查詢/查/讀取/看看 + 文檔名/doc_id
  - @Lark 新增/加/寫入/插入 + 內容 + to 文檔
  - @Lark 更新/改/修改 + 段落內容
  - @Lark 待辦/任務/todo + 內容

  English triggers:
  - @Lark query/read/get/fetch + doc_name/doc_id
  - @Lark insert/add/append/write/create + content + to doc
  - @Lark update/edit/modify/change + section content
  - @Lark todo/task + content

  Do NOT trigger if:
  - No "@Lark" marker present
  - Message is general social chat without document operations
  - The marker is a platform-level @mention (not the literal text "@Lark")

  Response language matches the user's message language.
---

# WhatsApp-Lark 文檔橋接技能

## 概述

這個技能處理 WhatsApp 消息到 Lark 文檔操作的橋接，支援**中英文雙語**。當用戶在 WhatsApp 消息中包含 "@Lark" 標記時，技能會解析消息內容（無論中文或英文），執行相應的 Lark 文檔操作，並返回結構化的結果。

This skill bridges WhatsApp messages to Lark document operations, with **bilingual Chinese/English support**. When a WhatsApp message contains the "@Lark" marker, the skill parses the instruction (in either Chinese or English), performs the corresponding Lark document operation, and returns structured results. The response language matches the user's input language.

## 快速開始

呢個係一個 **agent 行為指南**（skill），唔係一個要自己 deploy 嘅服務。你唔需要起 server 或者 set webhook。

### 1. 確認 Agent 可用 Lark MCP tools
呢個 skill 依靠 Hermes agent 嘅 Lark MCP tools 執行操作。
如果你用緊 Hermes gateway（WhatsApp 連線），已經 ready。

### 2. 測試觸發
喺 WhatsApp 直接 send 訊息：
```
@Lark query Saibao Follow-up
@Lark 查詢 專案進度
```

Agent 會自動 detect `@Lark` 並執行對應操作。

## 觸發條件 / Trigger Conditions

**Bilingual — 中英文雙語支援**

Trigger when ALL conditions are met:
1. Message contains "@Lark" marker (case-insensitive)
2. Message content includes a Lark document operation command

**Supported commands — 支援指令：**

| 中文指令 | English Commands | 操作 |
|----------|-----------------|------|
| @Lark 查詢/查/讀取/看看 + doc | @Lark query/read/get/fetch + doc | 查詢文檔 |
| @Lark 新增/加/寫入/插入 + 內容 | @Lark insert/add/append/create + content | 新增內容 |
| @Lark 更新/改/修改 + 內容 | @Lark update/edit/modify/change + content | 更新段落 |
| @Lark 待辦/任務 + 內容 | @Lark todo/task + content | 建立待辦 |

**Language auto-detection:**
- If the user writes in Chinese → respond in Chinese
- If the user writes in English → respond in English
- Mixed → follow the dominant language

**Do NOT trigger:**
- General chat without "@Lark" marker
- Pure social conversation
- Platform-level @mention (not literal "@Lark" text)

## 功能範圍

支援的 Lark 文檔操作：
1. **查詢文檔 (query)** — 讀取文檔內容或特定段落。

   ⚠️ **查詢任務時必須檢查父子關係（強制執行）：**
   - 當用戶用任務名稱查詢時（例如 `@Lark query Saibao Follow-up`），
     **必須**執行「處理流程 > Step 4」的完整父子任務解析
   - 檢查該任務的「父記錄」(parent_record) 字段：
     - 如有值 → 該任務是子任務，顯示「隸屬於: {父任務名}」
   - 查詢所有其他記錄的「父記錄」字段是否指向本任務：
     - 如找到 → 這些是子任務，**必須列出全部子任務及其進度**
   - 輸出格式必須是樹狀結構（見 Step 4c 格式要求）
   - 進度摘要必須包含 [M/N] 格式（已完成數/總數）
   - 支持遞歸多層級（父→子→孫，最多3層）

   **沒有父子關係時：** 正常輸出文檔內容即可。

2. **新增摘要 (insert)** - 在文檔中新增會議摘要或內容
3. **更新段落 (update)** - 更新指定段落並返回差異對比
4. **建立待辦事項 (todo)** - 在相關表格中創建待辦事項
5. **錯誤處理** - 處理 API 失敗、缺少參數等情況

## 配置文件說明

### 環境變量
- `LARK_APP_ID`: Lark 應用 ID
- `LARK_APP_SECRET`: Lark 應用密鑰
- `LARK_DOCUMENT_BASE_URL`: Lark API 基礎 URL
- `WHATSAPP_ACCESS_TOKEN`: WhatsApp Business API 訪問令牌
- `WHATSAPP_PHONE_NUMBER_ID`: WhatsApp 電話號碼 ID
- `WHATSAPP_WEBHOOK_VERIFY_TOKEN`: Webhook 驗證令牌

### Lark 權限配置
需要為 Lark 應用配置以下權限：
- `docx:document:readonly` - 文檔讀取權限
- `docx:document:write` - 文檔寫入權限
- `bitable:record:write` - 多維表格寫入權限

## 輸入格式

WhatsApp 消息應包含：
- `@Lark` 標記
- 操作類型（query/insert/update/todo）
- 文檔 ID（doc_id）、文檔名稱、**或任務名稱**
- 操作內容或參數

**示例格式：**
```
# 查詢整份文檔
@Lark query doc_12345
@Lark 查詢 專案規劃書

# 查詢特定任務（會自動顯示子任務進度）
@Lark query Saibao Follow-up
@Lark 查詢 E-lock data buffering

# 新增內容
@Lark insert meeting_summary: "今天會議討論了..."

# 更新段落
@Lark update section_3 with: "更新後的內容..."

# 建立待辦
@Lark todo: "跟進客戶反饋"
```

## 處理流程

### 1. 消息解析
- 檢查是否包含 "@Lark"
- 提取操作類型（query/insert/update/todo）
- 提取文檔 ID 或名稱
- 提取操作內容和參數

### 2. 參數驗證
- 驗證必要的參數是否存在
- 驗證文檔 ID 格式
- 驗證操作內容格式

### 3. 查詢原始數據
- 根據操作類型調用相應的 Lark API
- 處理身份驗證和權限
- 讀取文檔內容或表格記錄

### 4. 解析父子任務關係（僅 query 操作執行此步）
**這一步直接在 query 操作中執行，不可跳過。**

當用戶查詢一個任務時，按以下順序執行：

**Step 4a — 獲取目標記錄：**
- 使用 Lark Bitable API 查詢用戶指定的任務
- 透過表名/任務名稱/doc_id 匹配對應記錄
- 如果用戶只給了 doc/table 名稱而未指定具體任務，先列出所有記錄

**Step 4b — 檢查父子關係（雙向檢查）：**
- 檢查該記錄的字段中是否包含「父記錄」(parent_record / 父記錄 / SingleLink) 字段
  - 如果有值 → 該任務是**子任務**，用 link 值找出父任務信息，在輸出中標明「隸屬於: {父任務名}」
- 查詢表格中所有其他記錄，檢查是否有記錄的「父記錄」字段指向本記錄
  - 如果找到 → 這些是**子任務**，全部取回

**Step 4c — 構建任務樹：**
- 如果找到子任務，按以下格式構建樹：
  ```
  🔹 {父任務名} [{已完成數}/{總數}]  {狀態}
     ├─ ✅ {子任務1} ({負責人}) — {狀態}
     ├─ ⬜ {子任務2} ({負責人}) — {狀態}
     └─ ⬜ {子任務3} ({負責人}) — {狀態}
  ```
- 使用 ├─ 表示中間子任務，└─ 表示最後一個子任務
- 狀態圖標：✅ 已完成, ⬜ 進行中, 🔴 已停滯, ⬜ 待開始

**Step 4d — 計算進度摘要：**
- 總子任務數 = N
- 已完成子任務數 = M
- 進度 = [M/N]
- 百分比 = M/N * 100%
- 到期日範圍：最早子任務到期日 → 最晚子任務到期日

**Step 4e — 遞歸處理（多層級）：**
- 對每個子任務，重複 Step 4b-4d
- 支持多層級縮進，最多 3 層
- 格式：
  ```
  🔹 父任務 [2/4]
     ├─ ✅ 子任務1
     │   ├─ ✅ 孫任務1a
     │   └─ ⬜ 孫任務1b
     └─ ⬜ 子任務2
  ```

### 5. 結果處理
- 收集 API 響應
- 如果是查詢操作，包含父子任務樹狀結構
- 生成變更摘要（diff）
- 準備結構化 JSON 輸出
- 生成人類可讀的摘要

### 6. 響應生成
- 創建 WhatsApp 回復消息
- 包含成功/失敗狀態
- 包含變更摘要
- 包含父子任務進度摘要
- 包含是否需要用戶確認

## 輸出格式

### 結構化 JSON 輸出
```json
{
  "status": "success|error|partial_success",
  "operation": "query|insert|update|todo",
  "document_id": "doc_12345",
  "timestamp": "2024-01-01T12:00:00Z",
  "changes": {
    "added": ["段落1", "段落2"],
    "modified": ["段落3"],
    "deleted": []
  },
  "diff_summary": "變更摘要文字",
  "trace_id": "api_trace_id_if_available",
  "requires_confirmation": true|false,
  "confirmation_prompt": "請確認是否繼續？",
  "task_hierarchy": {
    "has_parent_child_tasks": true|false,
    "total_tasks": 10,
    "top_level_tasks": 3,
    "tree": [
      {
        "task_id": "rec_parent_1",
        "task_name": "Saibao Follow-up",
        "status": "進行中",
        "assignee": ["Vincent", "Frances"],
        "progress": "2/4 sub-tasks completed",
        "subtasks": [
          {
            "task_id": "rec_child_1a",
            "task_name": "Technical proposal",
            "status": "已完成",
            "assignee": ["Vincent"],
            "due_date": "2026-06-30"
          },
          {
            "task_id": "rec_child_1b",
            "task_name": "External coordination",
            "status": "進行中",
            "assignee": ["Frances"],
            "due_date": "2026-07-15"
          }
        ]
      }
    ]
  }
}
```

### 人類可讀的 WhatsApp 消息（無父子任務）
```
✅ Lark 操作完成！

操作：查詢文檔
文檔：專案規劃書
狀態：成功

摘要：
- 讀取了 5 個段落
- 最新更新：今天 10:30

追蹤 ID：trace_abc123
是否需要確認：否
```

### 人類可讀的 WhatsApp 消息（有父子任務）
```
✅ Lark 操作完成！

操作：查詢文檔
文檔：團隊任務看板
狀態：成功
任務總數：20（3個父任務，17個子任務）

📋 任務結構：

🔹 Saibao Follow-up [2/4]  ⬜ 進行中
   ├─ ✅ Technical proposal (Vincent) — 已完成
   ├─ ⬜ External coordination (Frances) — 進行中
   ├─ ⬜ 文件翻譯 (Viola) — 待開始
   └─ ⬜ 客戶演示準備 (Man) — 進行中

🔹 Huawei NPU Server [0/3]  ⬜ 進行中
   ├─ ⬜ 硬體設置 (Annabelle) — 待開始
   ├─ ⬜ 驅動安裝 (Frances) — 待開始
   └─ ⬜ 性能測試 (Kevin) — 待開始

🔹 CAD UTM Demo [0/0]  ⬜ 進行中
   （無子任務）

追蹤 ID：trace_abc123
是否需要確認：否
```

## 錯誤處理

### 1. 缺少必要參數
- 返回澄清問題
- 提示用戶提供缺失信息
- 示例："請提供文檔 ID：@Lark query [doc_id]"

### 2. API 失敗
- 記錄錯誤詳情
- 返回失敗狀態和 trace_id
- 提供重試建議
- 示例："❌ 操作失敗 (API 錯誤: 404)。追蹤 ID: trace_xyz789"

### 3. 權限不足
- 提示權限問題
- 建議聯繫管理員
- 返回部分成功狀態（如果適用）

### 4. 網路問題
- 實現重試機制（最多3次）
- 記錄重試次數
- 返回超時錯誤

## 配置要求

這個 skill **唔需要**額外嘅環境變量或依賴 — 佢依靠 Hermes agent 內建嘅 Lark MCP tools。
如果你需要手動 call Lark API 做測試，可以用以下環境變量：

```bash
LARK_APP_ID=cli_xxx
LARK_APP_SECRET=xxx
```

## 安全考慮

1. **身份驗證**：確保所有 Lark API 調用都使用有效的訪問令牌
2. **輸入驗證**：嚴格驗證 WhatsApp 消息內容，防止注入攻擊
3. **權限檢查**：驗證用戶對目標文檔的操作權限
4. **日誌記錄**：記錄所有操作以備審計
5. **敏感信息**：避免在日誌中記錄敏感文檔內容

## 測試案例

技能包含以下測試案例：
1. 正常查詢文檔（無父子任務）
2. 查詢含有父子任務結構的文檔（自動識別父子關係）
3. 查詢特定父任務，驗證子任務進度匯報
4. 查詢子任務，驗證父任務關聯顯示
5. 正常新增會議摘要
6. 更新指定段落並返回 diff
7. 缺少 doc_id 時的澄清流程
8. API 失敗時的錯誤處理

## 使用示例 / Usage Examples

**Language follows user input** — 回覆語言跟隨用戶指令語言

### 查詢文檔 / Query Document

**English:**
```
User: @Lark query doc_project_plan
Agent: 📄 Document query successful!

Document: Project Plan
Paragraphs: 12
Last updated: 2026-01-15 14:30

First 3 paragraphs:
1. Project Overview...
2. Timeline...
3. Resource Allocation...

✅ Complete, no confirmation needed.
```

**中文：**
```
用戶: @Lark 查詢 專案規劃書
系統: 📄 文檔查詢成功！

文檔：專案規劃書
段落數：12
最後更新：2026-01-15 14:30

前3個段落：
1. 專案概述...
2. 時間安排...
3. 資源分配...

✅ 操作完成，無需確認。
```

### 查詢父子任務進度 / Query Parent Task Progress

**English:**
```
User: @Lark query Saibao Follow-up
Agent: ✅ Task query successful!

Task: Saibao Follow-up [2/4] — In Progress
Assignees: Vincent, Frances

📋 Subtask Progress:

✅ Technical proposal — Vincent — Completed
⬜ External coordination — Frances — In Progress
⬜ Translation — Viola — Not Started
⬜ Client demo prep — Man — In Progress

Summary: 2 of 4 subtasks completed (50%)
Due dates range: 2026-06-30 to 2026-07-20
```

**中文：**
```
用戶: @Lark 查詢 Saibao Follow-up
系統: ✅ 任務查詢成功！

任務：Saibao Follow-up [2/4] — 進行中
負責人：Vincent, Frances

📋 子任務進度：

✅ Technical proposal — Vincent — 已完成
⬜ External coordination — Frances — 進行中
⬜ 文件翻譯 — Viola — 待開始
⬜ 客戶演示準備 — Man — 進行中

進度摘要：4個子任務中已完成2個（50%）
到期日範圍：2026-06-30 至 2026-07-20
```

### 新增內容 / Insert Content

**English:**
```
User: @Lark insert Meeting summary: Discussed Q2 goals and timeline into weekly_report
Agent: ✅ Content inserted successfully!

Location: Paragraph 15
Paragraph ID: para_789012
Trace ID: trace_abc123

✅ Complete, no confirmation needed.
```

**中文：**
```
用戶: @Lark insert 會議摘要：討論了Q2目標和時間線 to weekly_report
系統: ✅ 內容新增成功！

位置：第15段
段落ID：para_789012
追蹤ID：trace_abc123

✅ 操作完成，無需確認。
```

### 創建待辦事項 / Create Todo

**English:**
```
User: @Lark todo Follow up on customer feedback, high priority
Agent: ✅ Todo created successfully!

Task: Follow up on customer feedback, high priority
Status: Pending
Created: 2026-01-15 14:35
Record ID: rec_xyz456

✅ Complete, no confirmation needed.
```

**中文：**
```
用戶: @Lark todo: 跟進客戶反饋，優先級高
系統: ✅ 待辦事項創建成功！

任務：跟進客戶反饋，優先級高
狀態：待處理
創建時間：2026-01-15 14:35
記錄ID：rec_xyz456

✅ 操作完成，無需確認。
```

## 最佳實踐

1. **消息格式**：保持 WhatsApp 消息簡潔明確
2. **錯誤處理**：提供具體的錯誤信息和解決建議
3. **確認機制**：對於重要操作，要求用戶確認
4. **日誌記錄**：記錄所有操作以便追蹤和調試
5. **性能優化**：緩存常用文檔信息，減少 API 調用

## 故障排除

### 常見問題 / Common Issues
1. **@Lark 未觸發 / @Lark not triggering**
   - 檢查消息是否包含 "@Lark" 文字（非平台@提及）
   - Check the message contains the literal "@Lark" text (not a platform @mention)
   - 支援中英文指令，例如：`@Lark 查詢 ...` 或 `@Lark query ...`
   - Both Chinese and English commands work: `@Lark 查詢 ...` or `@Lark query ...`
2. **權限錯誤**：確認 Lark 應用有相應文檔的訪問權限
3. **網路問題**：檢查網路連接和防火牆設置
4. **API 限流**： Lark API 有調用頻率限制，請適當控制請求頻率

### 調試信息
- 啟用詳細日誌：設置 `DEBUG=true`
- 檢查 API 響應：查看 `logs/api_responses.log`
- 驗證 Webhook：使用 `curl` 測試 Webhook 端點

## 擴展功能

未來可擴展的功能：
1. **模板支持**：預定義文檔模板
2. **批量操作**：一次處理多個文檔
3. **預覽功能**：操作前預覽變更
4. **撤銷操作**：支持撤銷最近的操作
5. **自定義指令**：用戶自定義快捷指令

> 💡 需要批次處理 @Lark 命令？用 `whatsapp-lark-bridge-final` skill（獨立 Python 腳本）。
> 需要即時 agent 回應？用呢個 skill（`whatsapp-lark-document-bridge`）。