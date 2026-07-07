# WhatsApp-Lark Bridge API 文檔

## 概述

WhatsApp-Lark Bridge 是一個橋接服務，允許用戶通過 WhatsApp 消息控制 Lark 文檔。當用戶在 WhatsApp 消息中包含 `@Lark` 標記時，系統會自動解析命令並執行相應的 Lark 文檔操作。

## API 端點

### 1. Webhook 端點
```
POST /webhook/whatsapp
```

**功能：** 接收 WhatsApp Business API 的 Webhook 通知

**請求格式：**
```json
{
  "messages": [
    {
      "from": "發送者ID",
      "id": "消息ID",
      "timestamp": "ISO時間戳",
      "text": {
        "body": "消息內容"
      },
      "type": "text"
    }
  ]
}
```

**響應格式：**
```json
{
  "status": "success|error|ignored",
  "operation": "query|insert|update|todo",
  "message": "用戶友好的消息",
  "data": { /* 操作數據 */ },
  "timestamp": "ISO時間戳"
}
```

**Webhook 驗證：**
```
GET /webhook/whatsapp?hub.mode=subscribe&hub.challenge=CHALLENGE&hub.verify_token=TOKEN
```
返回 `hub.challenge` 值完成驗證。

### 2. 健康檢查
```
GET /health
```

**響應：**
```json
{
  "status": "healthy",
  "timestamp": "ISO時間戳",
  "service": "whatsapp-lark-bridge"
}
```

### 3. Lark 連接測試
```
GET /test/lark
```

**響應：**
```json
{
  "status": "success|error",
  "lark_connected": true|false,
  "has_token": true|false,
  "error": "錯誤信息（如果失敗）"
}
```

## 命令格式

### 基本語法
```
@Lark [操作] [參數]
```

### 支持的操作

#### 1. 查詢文檔
```
@Lark query [文檔ID]
```
或
```
@Lark query [文檔名稱]
```

**示例：**
```
@Lark query doc_project_plan
@Lark query 專案規劃書
```

**響應：**
```
📄 文檔查詢成功！

文檔：專案規劃書
段落數：12
最後更新：2024-01-15 14:30

前3個段落：
1. 專案概述...
2. 時間安排...
3. 資源分配...

✅ 操作完成，無需確認。
```

#### 2. 新增內容
```
@Lark insert [內容]
```
或
```
@Lark insert [內容] to [文檔]
```

**示例：**
```
@Lark insert 會議摘要：討論了Q2目標和時間線
@Lark insert 新任務分配 to weekly_report
```

**響應：**
```
✅ 內容新增成功！

位置：第15段
段落ID：para_789012
追蹤ID：trace_abc123

✅ 操作完成，無需確認。
```

#### 3. 更新內容
```
@Lark update [段落ID]: [新內容]
```

**示例：**
```
@Lark update para_123456: 更新後的任務描述
```

**響應：**
```
🔄 內容更新成功！

原內容：舊的任務描述
新內容：更新後的任務描述
變更摘要：修改了任務描述

✅ 操作完成，無需確認。
```

#### 4. 創建待辦事項
```
@Lark todo: [任務描述]
```
或
```
@Lark todo: [任務描述] [優先級]
```

**示例：**
```
@Lark todo: 跟進客戶反饋
@Lark todo: 修復系統bug 高優先級
```

**響應：**
```
✅ 待辦事項創建成功！

任務：跟進客戶反饋，優先級高
狀態：待處理
創建時間：2024-01-15 14:35
記錄ID：rec_xyz456

✅ 操作完成，無需確認。
```

#### 5. 幫助命令
```
@Lark help
@Lark ?
```

**響應：**
```
📋 WhatsApp-Lark Bridge 使用說明：

可用命令：
1. @Lark query [文檔ID] - 查詢文檔
2. @Lark insert [內容] - 新增內容
3. @Lark update [內容] - 更新內容
4. @Lark todo: [任務描述] - 創建待辦事項

示例：
@Lark query doc_project_plan
@Lark insert 會議摘要：討論了Q2目標
@Lark todo: 跟進客戶反饋

✅ 操作完成，無需確認。
```

## 錯誤處理

### 錯誤響應格式
```json
{
  "status": "error",
  "message": "錯誤描述",
  "error_code": "錯誤代碼",
  "suggestion": "建議操作",
  "timestamp": "ISO時間戳"
}
```

### 常見錯誤

#### 1. 命令解析錯誤
**錯誤碼：** `PARSE_ERROR`
**原因：** 命令格式不正確
**解決方案：** 檢查命令格式，參考幫助文檔

#### 2. 文檔不存在
**錯誤碼：** `DOC_NOT_FOUND`
**原因：** 指定的文檔ID不存在或無權限訪問
**解決方案：** 檢查文檔ID，確認訪問權限

#### 3. API 限流
**錯誤碼：** `RATE_LIMIT`
**原因：** Lark API 調用頻率超限
**解決方案：** 等待後重試，或聯繫管理員調整限流

#### 4. 網絡錯誤
**錯誤碼：** `NETWORK_ERROR`
**原因：** 網絡連接問題
**解決方案：** 檢查網絡連接，重試操作

#### 5. 權限不足
**錯誤碼：** `PERMISSION_DENIED`
**原因：** 缺少必要的操作權限
**解決方案：** 聯繫管理員獲取權限

## 數據格式

### Lark 文檔結構
```json
{
  "document_id": "文檔唯一標識",
  "title": "文檔標題",
  "content": "文檔內容",
  "paragraphs": [
    {
      "id": "段落ID",
      "content": "段落內容",
      "index": 1
    }
  ],
  "last_modified": "ISO時間戳",
  "owner": "所有者信息"
}
```

### 待辦事項結構
```json
{
  "record_id": "記錄ID",
  "task": "任務描述",
  "priority": "normal|high|urgent",
  "status": "pending|in_progress|completed|cancelled",
  "created_at": "ISO時間戳",
  "updated_at": "ISO時間戳",
  "assignee": "負責人"
}
```

## 配置參數

### 環境變量
| 變量名 | 說明 | 必需 | 默認值 |
|--------|------|------|--------|
| `LARK_APP_ID` | Lark 應用 ID | 是 | - |
| `LARK_APP_SECRET` | Lark 應用密鑰 | 是 | - |
| `WHATSAPP_ACCESS_TOKEN` | WhatsApp 訪問令牌 | 是 | - |
| `WHATSAPP_PHONE_NUMBER_ID` | WhatsApp 電話號碼 ID | 是 | - |
| `WHATSAPP_WEBHOOK_VERIFY_TOKEN` | Webhook 驗證令牌 | 是 | - |
| `APP_PORT` | 應用端口 | 否 | 5000 |
| `APP_ENV` | 環境 | 否 | development |
| `DEBUG` | 調試模式 | 否 | false |
| `LOG_LEVEL` | 日誌級別 | 否 | INFO |

### Lark 權限配置
應用需要以下 Lark 權限：
- `docx:document:readonly` - 文檔讀取權限
- `docx:document:write` - 文檔寫入權限
- `bitable:record:write` - 多維表格寫入權限

## 速率限制

### WhatsApp API 限制
- 消息發送頻率：根據 WhatsApp Business API 級別
- Webhook 接收：無限制

### Lark API 限制
- 訪問令牌獲取：100次/小時
- 文檔操作：1000次/天
- 並發請求：10個/秒

### 服務限制
- Webhook 處理：100請求/分鐘
- 消息隊列：1000條內存隊列
- 日誌大小：100MB/文件

## 安全考慮

### 1. 身份驗證
- WhatsApp Webhook 使用驗證令牌
- Lark API 使用應用令牌
- 所有 API 端點需要 HTTPS

### 2. 數據加密
- 敏感配置存儲在環境變量
- 通信使用 TLS 1.2+
- 日誌中的敏感信息脫敏

### 3. 訪問控制
- IP 白名單（可選）
- 請求頻率限制
- 操作審計日誌

### 4. 安全審計
- 定期檢查日誌
- 監控異常訪問
- 更新安全配置

## 監控指標

### 性能指標
- 請求響應時間
- 錯誤率
- 並發連接數
- 隊列長度

### 業務指標
- 命令處理數量
- 文檔操作統計
- 用戶活躍度
- 成功率

### 系統指標
- CPU/內存使用率
- 磁盤空間
- 網絡流量
- 日誌大小

## 故障恢復

### 自動恢復
1. 服務崩潰自動重啟
2. 網絡中斷自動重連
3. API 限流自動退避

### 手動恢復步驟
1. 檢查日誌定位問題
2. 驗證配置和憑證
3. 重啟服務組件
4. 測試功能恢復

### 備份策略
- 配置備份：每日自動備份
- 日誌歸檔：每周歸檔舊日誌
- 數據庫快照：根據需要手動備份

## 版本歷史

### v1.0.0 (2024-01-15)
- 初始版本
- 支持基本文檔操作
- WhatsApp Webhook 集成
- Lark API 集成

### v1.1.0 (計劃中)
- 支持更多文檔類型
- 增強錯誤處理
- 性能優化
- 監控儀表板

