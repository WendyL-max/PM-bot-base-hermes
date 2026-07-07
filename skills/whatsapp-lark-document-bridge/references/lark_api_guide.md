# Lark API 使用指南

## 概述
本文檔介紹 WhatsApp-Lark 橋接技能中使用的 Lark API 接口和操作方法。

## 身份驗證

### 獲取訪問令牌
```python
import requests

def get_lark_access_token(app_id, app_secret):
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    headers = {"Content-Type": "application/json"}
    data = {
        "app_id": app_id,
        "app_secret": app_secret
    }
    
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        result = response.json()
        if result.get("code") == 0:
            return result.get("tenant_access_token")
    return None
```

## 文檔操作 API

### 0. 關鍵：檢測父子任務關係

查詢 Lark 多維表格時，若表格包含「父記錄」(Two-way link) 字段，可以構建父子任務樹。

**檢測流程：**
1. 先調用 field_list API 確認是否有 `父記錄` / `parent_record` 類型的關聯字段
2. 查詢所有記錄時，檢查每條記錄的 `父記錄` 字段：
   - 若為 `null` 或空 → 該任務為頂層父任務
   - 若有值（關聯的 record_id） → 該任務為子任務
3. 構建樹狀結構後，計算每個父任務的進度 [n/m]

```python
def build_task_hierarchy(records, parent_field="父記錄"):
    """從 bitable 記錄構建父子任務樹"""
    # Phase 1: 按 record_id 索引
    by_id = {r["record_id"]: r for r in records}
    
    # Phase 2: 分組為 父任務 和 子任務
    parent_tasks = []
    child_map = {}  # parent_record_id -> [child_records]
    
    for record in records:
        fields = record.get("fields", {})
        parent_ref = fields.get(parent_field)
        
        if parent_ref is None:
            parent_tasks.append(record)
        else:
            # parent_field 可能是 {"link": [{"record_id": "rec_xxx"}]}
            parent_id = None
            if isinstance(parent_ref, dict):
                parent_id = parent_ref.get("link", [{}])[0].get("record_id")
            elif isinstance(parent_ref, list):
                parent_id = parent_ref[0].get("record_id") if parent_ref else None
            
            if parent_id:
                child_map.setdefault(parent_id, []).append(record)
    
    # Phase 3: 構建樹
    tree = []
    for parent in parent_tasks:
        pid = parent["record_id"]
        children = child_map.get(pid, [])
        subtask_info = []
        completed = 0
        total = len(children)
        
        for child in children:
            child_fields = child.get("fields", {})
            status = child_fields.get("Status", "")
            subtask_info.append({
                "record_id": child["record_id"],
                "task_name": extract_task_title(child_fields),
                "status": status,
                "assignee": extract_assignees(child_fields),
            })
            if status == "已完成":
                completed += 1
        
        tree.append({
            "task_id": pid,
            "task_name": extract_task_title(parent.get("fields", {})),
            "status": parent.get("fields", {}).get("Status", ""),
            "progress": f"{completed}/{total} completed",
            "subtasks": subtask_info,
        })
    
    return tree


def extract_task_title(fields):
    """Extract task title from bitable Text field (array format)"""
    task = fields.get("Task")
    if isinstance(task, list):
        return "".join(p.get("text", "") for p in task if isinstance(p, dict))
    return str(task) if task else "未命名任務"


def extract_assignees(fields):
    """Extract assignee names from MultiSelect field"""
    assignee = fields.get("Assignee")
    if isinstance(assignee, list):
        return [str(a) for a in assignee if a]
    return []
```

### 1. 查詢文檔內容
```python
def get_document_content(access_token, document_id):
    url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{document_id}/raw_content"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    return response.json()
```

### 2. 更新文檔段落
```python
def update_document_paragraph(access_token, document_id, paragraph_id, content):
    url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{document_id}/blocks/{paragraph_id}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = {
        "block_id": paragraph_id,
        "update_text_elements": {
            "elements": [
                {
                    "type": "textRun",
                    "text_run": {
                        "content": content,
                        "style": {}
                    }
                }
            ]
        }
    }
    
    response = requests.patch(url, headers=headers, json=data)
    return response.json()
```

### 3. 新增段落
```python
def add_document_paragraph(access_token, document_id, index, content):
    url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{document_id}/blocks/{index}/insert"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = {
        "index": index,
        "block_id": f"new_block_{index}",
        "block_type": 2,  # 2 表示段落
        "block_data": {
            "elements": [
                {
                    "type": "textRun",
                    "text_run": {
                        "content": content,
                        "style": {}
                    }
                }
            ]
        }
    }
    
    response = requests.post(url, headers=headers, json=data)
    return response.json()
```

### 4. 創建待辦事項（多維表格）
```python
def create_bitable_record(access_token, app_token, table_id, fields):
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = {
        "fields": fields
    }
    
    response = requests.post(url, headers=headers, json=data)
    return response.json()
```

## 錯誤處理

### 常見錯誤碼
| 錯誤碼 | 描述 | 解決方案 |
|--------|------|----------|
| 99991663 | 無權訪問文檔 | 檢查應用權限 |
| 99991664 | 文檔不存在 | 驗證文檔ID |
| 99991665 | 段落不存在 | 驗證段落ID |
| 99991668 | 請求參數錯誤 | 檢查請求格式 |
| 99991700 | 訪問令牌失效 | 重新獲取令牌 |
| 99991701 | 應用未啟用 | 檢查應用狀態 |

### 錯誤響應示例
```json
{
  "code": 99991663,
  "msg": "No permission to access this document.",
  "data": {}
}
```

## 最佳實踐

### 1. 令牌管理
- 緩存訪問令牌（有效期2小時）
- 實現令牌自動刷新機制
- 避免頻繁獲取令牌

### 2. 請求頻率控制
- Lark API 有頻率限制（通常 100次/分鐘）
- 實現請求隊列和重試機制
- 使用指數退避策略

### 3. 錯誤重試
```python
def retry_api_call(api_func, max_retries=3, delay=1):
    for attempt in range(max_retries):
        try:
            response = api_func()
            if response.get("code") == 0:
                return response
            elif response.get("code") in [99991700, 99991701]:  # 令牌相關錯誤
                refresh_token()
                continue
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
        time.sleep(delay * (2 ** attempt))  # 指數退避
    return None
```

### 4. 日誌記錄
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('lark_api.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def log_api_call(operation, document_id, status, trace_id=None):
    logger.info(f"Lark API Call - Operation: {operation}, Doc: {document_id}, Status: {status}, Trace: {trace_id}")
```

## Webhook 集成

### 接收 WhatsApp 消息
```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/webhook/whatsapp', methods=['POST'])
def whatsapp_webhook():
    data = request.json
    
    # 檢查是否包含 @Lark
    if '@Lark' in data.get('message', ''):
        # 解析消息
        message = data['message']
        sender = data['sender']
        
        # 處理 Lark 操作
        result = process_lark_operation(message)
        
        # 發送回覆
        send_whatsapp_reply(sender, result)
        
        return jsonify({"status": "processed"})
    
    return jsonify({"status": "ignored"})
```

### 發送 WhatsApp 回覆
```python
def send_whatsapp_reply(recipient, message):
    whatsapp_api_url = "https://graph.facebook.com/v17.0/me/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": recipient,
        "type": "text",
        "text": {"body": message}
    }
    
    response = requests.post(whatsapp_api_url, headers=headers, json=data)
    return response.json()
```

## 配置示例

### 環境變量配置
```bash
# Lark 配置
export LARK_APP_ID=cli_xxx
export LARK_APP_SECRET=xxx
export LARK_DOCUMENT_BASE_URL=https://open.feishu.cn

# WhatsApp 配置
export WHATSAPP_ACCESS_TOKEN=xxx
export WHATSAPP_PHONE_NUMBER_ID=xxx

# 應用配置
export DEBUG=true
export LOG_LEVEL=INFO
export MAX_RETRIES=3
```

### 配置文件
```yaml
lark:
  app_id: "cli_xxx"
  app_secret: "xxx"
  api_base_url: "https://open.feishu.cn"
  timeout: 30
  max_retries: 3

whatsapp:
  access_token: "xxx"
  phone_number_id: "xxx"
  webhook_verify_token: "your_verify_token"

logging:
  level: "INFO"
  file: "logs/app.log"
  max_size: "10MB"
  backup_count: 5
```

## 測試工具

### API 測試腳本
```python
#!/usr/bin/env python3
import sys
import json
from lark_client import LarkClient

def test_lark_operations():
    client = LarkClient()
    
    # 測試查詢文檔
    print("測試查詢文檔...")
    result = client.get_document("doc_test_123")
    print(f"結果: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # 測試新增段落
    print("\n測試新增段落...")
    result = client.add_paragraph("doc_test_123", 0, "測試內容")
    print(f"結果: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # 測試錯誤處理
    print("\n測試錯誤處理...")
    result = client.get_document("invalid_doc_id")
    print(f"結果: {json.dumps(result, indent=2, ensure_ascii=False)}")

if __name__ == "__main__":
    test_lark_operations()
```

### Webhook 測試
```bash
# 使用 curl 測試 Webhook
curl -X POST \
  http://localhost:5000/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "message": "@Lark query doc_123",
    "sender": "1234567890",
    "timestamp": "2024-01-01T12:00:00Z"
  }'
```

## 性能監控

### 關鍵指標
1. **API 響應時間**：目標 < 2秒
2. **成功率**：目標 > 99%
3. **並發處理能力**：目標 100請求/秒
4. **錯誤率**：目標 < 1%

### 監控腳本
```python
import time
import statistics
from prometheus_client import Counter, Histogram, start_http_server

# 定義指標
API_CALLS = Counter('lark_api_calls_total', 'Total Lark API calls')
API_ERRORS = Counter('lark_api_errors_total', 'Total Lark API errors')
API_DURATION = Histogram('lark_api_duration_seconds', 'Lark API call duration')

def monitor_api_call(func):
    def wrapper(*args, **kwargs):
        API_CALLS.inc()
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            API_DURATION.observe(duration)
            return result
        except Exception as e:
            API_ERRORS.inc()
            raise e
    return wrapper
```

## 安全建議

1. **令牌安全**：
   - 不要硬編碼令牌
   - 使用環境變量或密鑰管理服務
   - 定期輪換令牌

2. **輸入驗證**：
   - 驗證所有用戶輸入
   - 過濾潛在的注入攻擊
   - 限制輸入長度和格式

3. **訪問控制**：
   - 實現基於角色的訪問控制
   - 記錄所有操作日誌
   - 定期審計權限

4. **數據保護**：
   - 加密敏感數據
   - 遵守數據保留政策
   - 安全刪除不再需要的數據