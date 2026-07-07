# WhatsApp-Lark 文檔橋接技能

## 概述
這個技能允許用戶通過 WhatsApp 消息操作 Lark 文檔，實現文檔查詢、內容新增、段落更新和待辦事項創建功能。用戶只需在 WhatsApp 消息中包含 "@Lark" 關鍵字，系統就會自動處理相應的 Lark 文檔操作。

## 功能特性

### 1. 文檔查詢
- **指令格式**: `@Lark query [document_id]`
- **功能**: 查詢指定文檔的內容和元數據
- **返回**: 文檔標題、內容摘要、段落數、最後更新時間
- **示例**: `@Lark query doc_project_plan`

### 2. 內容新增
- **指令格式**: `@Lark insert [content] to [document_id]`
- **功能**: 在指定文檔末尾新增內容
- **返回**: 新增段落的ID、位置、追蹤ID
- **示例**: `@Lark insert 會議摘要 to weekly_report`

### 3. 段落更新
- **指令格式**: `@Lark update [paragraph_id] in [document_id] with [content]`
- **功能**: 更新文檔中的指定段落
- **返回**: 更新前後內容對比（diff）、追蹤ID
- **示例**: `@Lark update section_3 in doc_project_plan with "新內容"`

### 4. 待辦事項創建
- **指令格式**: `@Lark todo: [task_description]`
- **功能**: 在多維表格中創建待辦事項記錄
- **返回**: 記錄ID、創建時間、追蹤ID
- **示例**: `@Lark todo: 跟進客戶反饋，優先級高`

## 技術架構

### 組件圖
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  WhatsApp   │────│   Webhook   │────│   Lark API   │
│   Client    │    │   Server    │    │   Gateway    │
└─────────────┘    └─────────────┘    └─────────────┘
                          │                    │
                    ┌─────┴─────┐        ┌─────┴─────┐
                    │  Message  │        │   Lark    │
                    │  Parser   │        │ Documents │
                    └───────────┘        └───────────┘
                          │                    │
                    ┌─────┴─────┐        ┌─────┴─────┐
                    │  Response │        │  Bitable  │
                    │ Generator │        │  Tables   │
                    └───────────┘        └───────────┘
```

### 數據流
1. **接收消息**: WhatsApp Webhook 接收用戶消息
2. **解析指令**: 檢查是否包含 "@Lark"，提取操作類型和參數
3. **API調用**: 根據操作類型調用相應的 Lark API
4. **處理響應**: 解析 API 響應，生成用戶友好的消息
5. **發送回覆**: 通過 WhatsApp API 發送回覆消息

## 配置要求

### 環境變量
```bash
# Lark 配置
export LARK_APP_ID=cli_xxx
export LARK_APP_SECRET=*** LARK_DOCUMENT_BASE_URL=https://open.feishu.cn

# WhatsApp 配置
export WHATSAPP_ACCESS_TOKEN=*** WHATSAPP_PHONE_NUMBER_ID=xxx
export WHATSAPP_WEBHOOK_VERIFY_TOKEN=your_v...n
# 應用配置
export DEBUG=true
export LOG_LEVEL=INFO
export MAX_RETRIES=3
```

### Lark 應用權限
需要為 Lark 應用配置以下權限：
- `docx:document:readonly` - 文檔讀取權限
- `docx:document:write` - 文檔寫入權限
- `bitable:record:write` - 多維表格寫入權限

## 安裝部署

### 1. 依賴安裝
```bash
# 創建虛擬環境
python -m venv venv
source venv/bin/activate

# 安裝依賴
pip install flask requests python-dotenv
```

### 2. 配置文件
```python
# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Lark 配置
    LARK_APP_ID = os.getenv('LARK_APP_ID')
    LARK_APP_SECRET=os.get...')
    LARK_API_BASE_URL = os.getenv('LARK_DOCUMENT_BASE_URL', 'https://open.feishu.cn')
    
    # WhatsApp 配置
    WHATSAPP_ACCESS_TOKEN=os.get...')
    WHATSAPP_PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
    WHATSAPP_WEBHOOK_VERIFY_TOKEN=os.get...')
    
    # 應用配置
    DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
```

### 3. 啟動服務
```bash
# 開發環境
python app.py

# 生產環境（使用 gunicorn）
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## API 接口

### Webhook 端點
```
POST /webhook/whatsapp
```

**請求格式**:
```json
{
  "object": "whatsapp_business_account",
  "entry": [{
    "id": "WHATSAPP_BUSINESS_ACCOUNT_ID",
    "changes": [{
      "value": {
        "messaging_product": "whatsapp",
        "metadata": {
          "display_phone_number": "15551234567",
          "phone_number_id": "WHATSAPP_PHONE_NUMBER_ID"
        },
        "contacts": [{
          "profile": {
            "name": "John Doe"
          },
          "wa_id": "15551234567"
        }],
        "messages": [{
          "from": "15551234567",
          "id": "wamid.xxxx",
          "timestamp": "1700000000",
          "text": {
            "body": "@Lark query doc_project_plan"
          },
          "type": "text"
        }]
      },
      "field": "messages"
    }]
  }]
}
```

**響應格式**:
```json
{
  "status": "processed",
  "operation": "query",
  "document_id": "doc_project_plan",
  "response": "📄 文檔查詢成功！\n\n文檔：專案規劃書\n段落數：12\n最後更新：2024-01-15 14:30\n\n前3個段落：\n1. 專案概述...\n2. 時間安排...\n3. 資源分配...\n\n✅ 操作完成，無需確認。"
}
```

## 錯誤處理

### 錯誤類型
1. **解析錯誤**: 指令格式不正確
2. **API錯誤**: Lark API 調用失敗
3. **權限錯誤**: 無權訪問文檔
4. **網路錯誤**: 網路連接問題
5. **參數錯誤**: 缺少必要參數

### 錯誤響應
```json
{
  "status": "error",
  "error_code": "API_ERROR",
  "error_message": "文檔不存在或無權限訪問",
  "trace_id": "trace_123456",
  "suggestions": [
    "檢查文檔ID是否正確",
    "確認您有訪問權限"
  ]
}
```

## 日誌記錄

### 日誌格式
```python
import logging
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('whatsapp_lark_bridge.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def log_operation(operation, status, details):
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "operation": operation,
        "status": status,
        "details": details,
        "trace_id": generate_trace_id()
    }
    logger.info(json.dumps(log_entry, ensure_ascii=False))
```

### 日誌示例
```json
{
  "timestamp": "2024-01-15T14:30:00.123456",
  "operation": "query",
  "status": "success",
  "details": {
    "document_id": "doc_project_plan",
    "paragraph_count": 12,
    "response_time": "1.2s"
  },
  "trace_id": "trace_789012"
}
```

## 監控指標

### 關鍵指標
1. **請求數量**: 每分鐘處理的消息數
2. **成功率**: 成功處理的消息比例
3. **響應時間**: API 調用平均響應時間
4. **錯誤率**: 各類錯誤的發生頻率

### 監控面板
```
WhatsApp-Lark 橋接監控
─────────────────────
請求總數: 1,234
成功率: 98.5%
平均響應時間:電子
```

## 安全考慮

### 1. 輸入驗證
- 驗證 WhatsApp 消息簽名
- 過濾潛在的注入攻擊
- 限制輸入長度和格式

### 2. 訪問控制
- 驗證 Lark 應用權限
- 實現基於角色的訪問控制
- 記錄所有操作日誌

### 3. 數據保護
- 加密敏感配置信息
- 安全存儲訪問令牌
- 定期清理日誌文件

## 擴展性

### 支持更多操作
```python
# 未來可擴展的操作
SUPPORTED_OPERATIONS = {
    'query': handle_query,
    'insert': handle_insert,
    'update': handle_update,
    'todo': handle_todo,
    # 未來擴展
    'search': handle_search,
    'delete': handle_delete,
    'share': handle_share,
    'comment': handle_comment
}
```

### 支持更多平台
```python
# 未來可擴展的平台
SUPPORTED_PLATFORMS = {
    'whatsapp': WhatsAppHandler,
    'telegram': TelegramHandler,
    'slack': SlackHandler,
    'wechat': WeChatHandler
}
```

## 故障排除

### 常見問題
1. **Webhook 驗證失敗**
   - 檢查 WhatsApp Webhook 驗證令牌
   - 確認伺服器可公開訪問

2. **Lark API 調用失敗**
   - 檢查 Lark 應用權限
   - 確認訪問令牌有效
   - 驗證文檔 ID 正確

3. **消息解析錯誤**
   - 檢查指令格式
   - 驗證參數完整性
   - 查看日誌獲取詳細錯誤

### 調試步驟
```bash
# 1. 檢查服務狀態
curl http://localhost:5000/health

# 2. 檢查配置
python -c "from config import Config; print(Config.LARK_APP_ID)"

# 3. 測試 Lark API 連接
python test_lark_connection.py

# 4. 查看日誌
tail -f whatsapp_lark_bridge.log
```

## 性能優化

### 緩存策略
```python
from functools import lru_cache
import time

@lru_cache(maxsize=100)
def get_document_metadata(document_id):
    """緩存文檔元數據，減少 API 調用"""
    # 實現文檔元數據獲取邏輯
    pass

@lru_cache(maxsize=1000, ttl=300)  # 5分鐘 TTL
def get_access_token():
    """緩存訪問令牌，避免頻繁刷新"""
    # 實現令牌獲取邏輯
    pass
```

### 異步處理
```python
import asyncio
import aiohttp

async def process_message_async(message):
    """異步處理消息，提高吞吐量"""
    tasks = [
        parse_message(message),
        validate_parameters(message),
        call_lark_api(message)
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return await format_response(results)
```

## 版本歷史

### v1.0.0 (2024-01-15)
- 初始版本發布
- 支持文檔查詢、新增、更新操作
- 支持待辦事項創建
- 基本錯誤處理和日誌記錄

### v1.1.0 (計劃中)
- 支持文檔搜索功能
- 增加批量操作支持
- 優化性能緩存
- 增強安全性

## 貢獻指南

### 代碼規範
- 遵循 PEP 8 編碼規範
- 添加類型提示
- 編寫單元測試
- 更新文檔

### 提交流程
1. Fork 倉庫
2. 創建功能分支
3. 提交更改
4. 創建 Pull Request
5. 通過代碼審查

### 測試要求
- 新功能必須包含測試案例
- 測試覆蓋率不低於 80%
- 通過所有現有測試

## 許可證
MIT License