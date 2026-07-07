# 測試案例集

## 概述
本文檔包含 WhatsApp-Lark 文檔橋接技能的測試案例，涵蓋正常流程和風險流程。

## 測試案例結構

每個測試案例包含：
- **ID**: 唯一標識符
- **名稱**: 測試案例描述
- **類型**: normal/edge/error
- **輸入**: WhatsApp 消息內容
- **預期輸出**: 期望的響應
- **驗證點**: 需要驗證的事項
- **API 模擬**: 模擬的 API 響應

## 測試案例列表

### 1. 正常查詢文檔 (TC-001)
**類型**: normal  
**輸入**: `@Lark query doc_project_plan`  
**預期輸出**:
```json
{
  "status": "success",
  "operation": "query",
  "document_id": "doc_project_plan",
  "content_preview": "專案概述...\n時間安排...\n資源分配...",
  "paragraph_count": 12,
  "last_modified": "2024-01-15T14:30:00Z"
}
```
**WhatsApp 消息**:
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
**驗證點**:
- 正確解析 "@Lark query" 指令
- 成功調用 Lark 文檔查詢 API
- 返回正確的文檔內容預覽
- 生成人類可讀的摘要

**API 模擬**:
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "document": {
      "document_id": "doc_project_plan",
      "title": "專案規劃書",
      "content": "專案概述...\n時間安排...\n資源分配...",
      "paragraphs": 12,
      "updated_at": "2024-01-15T14:30:00Z"
    }
  }
}
```

### 2. 正常新增會議摘要 (TC-002)
**類型**: normal  
**輸入**: `@Lark insert meeting_summary to weekly_report: "今天團隊討論了Q2目標，決定優先處理客戶反饋系統。預計下週完成原型設計。"`  
**預期輸出**:
```json
{
  "status": "success",
  "operation": "insert",
  "document_id": "weekly_report",
  "inserted_content": "今天團隊討論了Q2目標，決定優先處理客戶反饋系統。預計下週完成原型設計。",
  "position": "end_of_document",
  "paragraph_id": "para_new_001",
  "trace_id": "trace_insert_789"
}
```
**WhatsApp 消息**:
```
📝 新增摘要成功！

位置：weekly_report 文檔結尾
新增內容：今天團隊討論了Q2目標，決定優先處理客戶反饋系統。預計下週完成原型設計。

變更摘要：
- 新增1個段落
- 字數：45字
- 位置：文檔末尾

🔍 追蹤 ID：trace_insert_789
✅ 操作完成，無需確認。
```
**驗證點**:
- 正確解析 "insert" 指令和目標文檔
- 成功新增段落到指定文檔
- 返回新增段落的 ID 和位置
- 提供追蹤 ID 用於後續查詢

**API 模擬**:
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "block": {
      "block_id": "para_new_001",
      "block_type": 2,
      "content": "今天團隊討論了Q2目標，決定優先處理客戶反饋系統。預計下週完成原型設計。"
    }
  }
}
```

### 3. 更新指定段落並返回 diff (TC-003)
**類型**: normal  
**輸入**: `@Lark update section_3 in doc_project_plan with: "更新後的專案時間安排：\n1. 需求分析：1月20日完成\n2. 原型設計：1月27日完成\n3. 開發測試：2月10日完成"`  
**預期輸出**:
```json
{
  "status": "success",
  "operation": "update",
  "document_id": "doc_project_plan",
  "paragraph_id": "section_3",
  "old_content": "原專案時間安排：\n1. 需求分析：1月15日\n2. 原型設計：1月25日",
  "new_content": "更新後的專案時間安排：\n1. 需求分析：1月20日完成\n2. 原型設計：1月27日完成\n3. 開發測試：2月10日完成",
  "diff": {
    "added_lines": ["3. 開發測試：2月10日完成"],
    "modified_lines": [
      {"old": "1. 需求分析：1月15日", "new": "1. 需求分析：1月20日完成"},
      {"old": "2. 原型設計：1月25日", "new": "2. 原型設計：1月27日完成"}
    ],
    "deleted_lines": []
  },
  "trace_id": "trace_update_456"
}
```
**WhatsApp 消息**:
```
🔄 段落更新成功！

文檔：專案規劃書
段落：section_3

變更摘要（diff）：
+ 新增：3. 開發測試：2月10日完成
~ 修改：1. 需求分析：1月15日 → 1月20日完成
~ 修改：2. 原型設計：1月25日 → 1月27日完成

總變更：3處
🔍 追蹤 ID：trace_update_456
✅ 操作完成，無需確認。
```
**驗證點**:
- 正確解析 "update" 指令和目標段落
- 成功更新指定段落內容
- 生成準確的 diff 對比
- 以清晰格式展示變更內容

**API 模擬**:
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "block": {
      "block_id": "section_3",
      "old_content": "原專案時間安排：\n1. 需求分析：1月15日\n2. 原型設計：1月25日",
      "new_content": "更新後的專案時間安排：\n1. 需求分析：1月20日完成\n2. 原型設計：1月27日完成\n3. 開發測試：2月10日完成"
    }
  }
}
```

### 4. 缺少 doc_id 時的澄清流程 (TC-004)
**類型**: edge  
**輸入**: `@Lark query`  
**預期輸出**:
```json
{
  "status": "clarification_needed",
  "operation": "query",
  "missing_parameters": ["document_id"],
  "clarification_prompt": "請提供要查詢的文檔ID，格式：@Lark query [doc_id]",
  "examples": [
    "@Lark query doc_project_plan",
    "@Lark query weekly_report_2024",
    "@Lark query meeting_notes_jan"
  ]
}
```
**WhatsApp 消息**:
```
❓ 需要更多信息

操作：查詢文檔
缺失：文檔 ID

請提供要查詢的文檔ID，例如：
@Lark query doc_project_plan
@Lark query weekly_report_2024
@Lark query meeting_notes_jan

請回复完整的指令。
```
**驗證點**:
- 檢測到缺少必要參數（doc_id）
- 返回清晰明確的澄清提示
- 提供具體的格式示例
- 保持友好的用戶體驗

**API 模擬**: 無 API 調用

### 5. API 失敗時的錯誤處理 (TC-005)
**類型**: error  
**輸入**: `@Lark update section_99 in invalid_doc with: "新內容"`  
**預期輸出**:
```json
{
  "status": "error",
  "operation": "update",
  "document_id": "invalid_doc",
  "paragraph_id": "section_99",
  "error_code": 99991664,
  "error_message": "Document not found or no permission to access",
  "trace_id": "trace_error_123",
  "suggestions": [
    "檢查文檔ID是否正確",
    "確認您有訪問權限",
    "聯繫管理員獲取幫助"
  ],
  "retry_possible": true
}
```
**WhatsApp 消息**:
```
❌ 操作失敗！

錯誤：文檔不存在或無權限訪問
錯誤碼：99991664
操作：更新段落
目標：invalid_doc 的 section_99

🔍 追蹤 ID：trace_error_123

建議操作：
1. 檢查文檔 ID 是否正確
2. 確認您有訪問權限
3. 聯繫管理員獲取幫助

🔄 是否需要重試？請回复「重試」或提供正確文檔ID。
```
**驗證點**:
- 正確捕獲 API 錯誤響應
- 返回詳細的錯誤信息（包括錯誤碼）
- 提供有用的解決建議
- 提供追蹤 ID 用於問題排查
- 提供重試選項

**API 模擬**:
```json
{
  "code": 99991664,
  "msg": "Document not found or no permission to access",
  "data": {},
  "trace_id": "trace_error_123"
}
```

### 6. 無效操作類型 (TC-006)
**類型**: error  
**輸入**: `@Lark invalid_operation doc_123`  
**預期輸出**:
```json
{
  "status": "error",
  "operation": "invalid_operation",
  "error_message": "不支援的操作類型：invalid_operation",
  "supported_operations": ["query", "insert", "update", "todo"],
  "examples": [
    "@Lark query [doc_id]",
    "@Lark insert [content] to [doc_id]",
    "@Lark update [paragraph] in [doc_id] with [content]",
    "@Lark todo [task_description]"
  ]
}
```
**WhatsApp 消息**:
```
❌ 操作不支援！

不支援的操作類型：invalid_operation

支援的操作：
• query - 查詢文檔
• insert - 新增內容
• update - 更新段落
• todo - 創建待辦事項

使用示例：
@Lark query doc_project_plan
@Lark insert 會議摘要 to weekly_report
@Lark update section_3 with 新內容
@Lark todo 跟進客戶反饋

請使用支援的操作類型。
```
**驗證點**:
- 檢測到無效的操作類型
- 列出所有支援的操作類型
- 提供具體的使用示例
- 引導用戶使用正確格式

### 7. 網路超時重試 (TC-007)
**類型**: edge  
**輸入**: `@Lark query large_document`  
**預期輸出**:
```json
{
  "status": "partial_success",
  "operation": "query",
  "document_id": "large_document",
  "attempts": 3,
  "final_status": "timeout",
  "partial_content": "文檔前1000字內容...",
  "trace_id": "trace_timeout_789",
  "suggestions": [
    "文檔過大，建議分批查詢",
    "使用更精確的查詢條件",
    "稍後再試"
  ]
}
```
**WhatsApp 消息**:
```
⚠️ 部分成功

操作：查詢文檔
文檔：large_document
狀態：超時（重試3次）

已獲取部分內容（前1000字）：
文檔前1000字內容...

🔍 追蹤 ID：trace_timeout_789

建議：
1. 文檔過大，建議分批查詢
2. 使用更精確的查詢條件
3. 稍後再試

是否繼續獲取剩餘內容？
```
**驗證點**:
- 實現重試機制（最多3次）
- 記錄重試次數和最終狀態
- 返回已獲取的部分內容
- 提供實用的解決建議
- 提供繼續操作的選項

### 8. 創建待辦事項 (TC-008)
**類型**: normal  
**輸入**: `@Lark todo: "跟進客戶A的產品反饋，優先級高，截止日期2024-01-30"`  
**預期輸出**:
```json
{
  "status": "success",
  "operation": "todo",
  "task_description": "跟進客戶A的產品反饋，優先級高，截止日期2024-01-30",
  "table_id": "tbl_todo_list",
  "record_id": "rec_new_task_001",
  "fields_created": {
    "任務描述": "跟進客戶A的產品反饋",
    "優先級": "高",
    "截止日期": "2024-01-30",
    "狀態": "待處理",
    "創建時間": "2024-01-15T10:30:00Z"
  },
  "trace_id": "trace_todo_555"
}
```
**WhatsApp 消息**:
```
✅ 待辦事項創建成功！

任務：跟進客戶A的產品反饋
優先級：高
截止日期：2024-01-30
狀態：待處理

位置：待辦事項表格
記錄ID：rec_new_task_001

🔍 追蹤 ID：trace_todo_555
✅ 操作完成，無需確認。
```
**驗證點**:
- 正確解析 "todo" 指令
- 提取任務描述、優先級、截止日期等信息
- 成功創建多維表格記錄
- 返回完整的記錄信息

## 測試執行指南

### 1. 單元測試
```python
import pytest
from whatsapp_lark_bridge import WhatsAppLarkBridge

def test_query_document():
    bridge = WhatsAppLarkBridge()
    result = bridge.process_message("@Lark query doc_project_plan")
    assert result["status"] == "success"
    assert "content_preview" in result
    assert result["paragraph_count"] > 0

def test_missing_doc_id():
    bridge = WhatsAppLarkBridge()
    result = bridge.process_message("@Lark query")
    assert result["status"] == "clarification_needed"
    assert "missing_parameters" in result
    assert "document_id" in result["missing_parameters"]
```

### 2. 集成測試
```python
def test_integration_workflow():
    # 測試完整工作流程
    test_cases = [
        ("@Lark query doc_test", "success"),
        ("@Lark insert test_content", "success"),
        ("@Lark update para_1", "success"),
        ("@Lark invalid_op", "error"),
    ]
    
    bridge = WhatsAppLarkBridge()
    
    for input_msg, expected_status in test_cases:
        result = bridge.process_message(input_msg)
        assert result["status"] == expected_status
```

### 3. 性能測試
```python
import time
from concurrent.futures import ThreadPoolExecutor

def test_concurrent_requests():
    bridge = WhatsAppLarkBridge()
    messages = ["@Lark query doc_{}".format(i) for i in range(100)]
    
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(bridge.process_message, messages))
    
    end_time = time.time()
    
    success_count = sum(1 for r in results if r["status"] == "success")
    print(f"處理 {len(messages)} 條消息用時: {end_time - start_time:.2f}秒")
    print(f"成功率: {success_count/len(messages)*100:.1f}%")
    
    assert end_time - start_time < 30  # 30秒內完成
    assert success_count / len(messages) > 0.95  # 95%成功率
```

### 4. 錯誤恢復測試
```python
def test_error_recovery():
    bridge = WhatsAppLarkBridge()
    
    # 模擬 API 失敗
    with patch('lark_api.get_document_content', side_effect=Exception("API Error")):
        result = bridge.process_message("@Lark query doc_error")
        assert result["status"] == "error"
        assert "trace_id" in result
        assert "suggestions" in result
    
    # 測試重試後成功
    call_count = 0
    def mock_api():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise Exception("Temporary Error")
        return {"code": 0, "data": {"content": "Success"}}
    
    with patch('lark_api.get_document_content', side_effect=mock_api):
        result = bridge.process_message("@Lark query doc_retry")
        assert result["status"] == "success"
        assert call_count == 3  # 重試了3次
```

## 測試數據準備

### 測試文檔
```json
{
  "doc_project_plan": {
    "title": "專案規劃書",
    "content": "專案概述...\n時間安排...\n資源分配...",
    "paragraphs": ["para_1", "para_2", "para_3"]
  },
  "weekly_report": {
    "title": "週報",
    "content": "本週進度...\n下週計劃...",
    "paragraphs": ["para_weekly_1"]
  }
}
```

### 測試表格
```json
{
  "tbl_todo_list": {
    "fields": ["任務描述", "優先級", "截止日期", "狀態", "創建時間"],
    "records": []
  }
}
```

## 測試報告模板

### 測試執行報告
```
測試執行報告
============

測試時間: 2024-01-15 14:30:00
測試環境: 開發環境
測試版本: v1.0.0

測試結果摘要:
------------
總測試案例: 8
通過: 8
失敗: 0
跳過: 0
成功率: 100%

詳細結果:
--------
1. TC-001 正常查詢文檔: ✅ 通過
2. TC-002 正常新增摘要: ✅ 通過
3. TC-003 更新段落並返回diff: ✅ 通過
4. TC-004 缺少doc_id澄清: ✅ 通過
5. TC-005 API失敗處理: ✅ 通過
6. TC-006 無效操作類型: ✅ 通過
7. TC-007 網路超時重試: ✅ 通過
8. TC-008 創建待辦事項: ✅ 通過

性能指標:
--------
平均響應時間: 1.2秒
最大並發數: 10
錯誤率: 0%

建議:
-----
1. 增加更多邊界測試
2. 優化大文檔處理性能
3. 增強錯誤恢復機制
```

## 自動化測試腳本

```bash
#!/bin/bash
# run_tests.sh

echo "開始執行 WhatsApp-Lark 橋接技能測試..."

# 運行單元測試
echo "運行單元測試..."
python -m pytest tests/unit_tests.py -v

# 運行集成測試
echo "運行集成測試..."
python -m pytest tests/integration_tests.py -v

# 運行性能測試
echo "運行性能測試..."
python tests/performance_tests.py

# 生成測試報告
echo "生成測試報告..."
python -m pytest --html=test_report.html --self-contained-html

echo "測試完成！"
```

這個測試案例集涵蓋了您要求的所有場景，包括正常流程和風險流程。每個測試案例都有詳細的輸入、預期輸出、驗證點和 API 模擬，確保技能在不同情況下都能正確工作。