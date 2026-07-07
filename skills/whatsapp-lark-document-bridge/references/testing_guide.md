# WhatsApp-Lark Bridge 集成測試腳本

## 測試環境配置

### 1. 本地開發環境
```bash
# 安裝測試依賴
pip install pytest pytest-asyncio httpx pytest-cov pytest-mock

# 設置測試環境變量
export APP_ENV=testing
export DATABASE_URL=sqlite:///test.db
export LARK_APP_ID=test_app_id
export LARK_APP_SECRET=test_app_secret
export WHATSAPP_ACCESS_TOKEN=test_token

# 創建測試數據庫
python scripts/create_test_db.py
```

### 2. 測試目錄結構
```
tests/
├── conftest.py           # 測試配置
├── test_unit/           # 單元測試
│   ├── test_models.py
│   ├── test_services.py
│   └── test_utils.py
├── test_integration/    # 集成測試
│   ├── test_lark_api.py
│   ├── test_whatsapp_api.py
│   └── test_bridge.py
├── test_e2e/           # 端到端測試
│   ├── test_workflows.py
│   └── test_scenarios.py
└── test_performance/   # 性能測試
    ├── test_load.py
    └── test_stress.py
```

## 單元測試示例

### 測試數據模型
```python
# tests/test_unit/test_models.py
import pytest
from datetime import datetime
from app.models import User, Message, Document

def test_user_model():
    """測試用戶模型"""
    user = User(
        id=1,
        name="測試用戶",
        email="test@example.com",
        created_at=datetime.now()
    )
    
    assert user.id == 1
    assert user.name == "測試用戶"
    assert user.email == "test@example.com"
    assert isinstance(user.created_at, datetime)

def test_message_model():
    """測試消息模型"""
    message = Message(
        id="msg_123",
        content="測試消息",
        sender="user_123",
        timestamp=datetime.now(),
        platform="whatsapp"
    )
    
    assert message.id == "msg_123"
    assert message.content == "測試消息"
    assert message.platform == "whatsapp"

def test_document_model():
    """測試文檔模型"""
    doc = Document(
        id="doc_456",
        title="測試文檔",
        content="文檔內容",
        created_by="user_123",
        updated_at=datetime.now()
    )
    
    assert doc.id == "doc_456"
    assert doc.title == "測試文檔"
    assert doc.created_by == "user_123"
```

### 測試服務層
```python
# tests/test_unit/test_services.py
import pytest
from unittest.mock import Mock, patch
from app.services import LarkService, WhatsAppService, BridgeService

class TestLarkService:
    def test_get_document_success(self):
        """測試獲取文檔成功"""
        with patch('app.services.requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "data": {
                    "document": {
                        "title": "測試文檔",
                        "content": "文檔內容"
                    }
                }
            }
            
            service = LarkService()
            result = service.get_document("doc_123")
            
            assert result["title"] == "測試文檔"
            assert result["content"] == "文檔內容"
    
    def test_get_document_failure(self):
        """測試獲取文檔失敗"""
        with patch('app.services.requests.get') as mock_get:
            mock_get.return_value.status_code = 404
            
            service = LarkService()
            result = service.get_document("doc_123")
            
            assert result is None

class TestWhatsAppService:
    def test_send_message(self):
        """測試發送消息"""
        with patch('app.services.requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "messages": [{"id": "msg_789"}]
            }
            
            service = WhatsAppService()
            result = service.send_message("user_123", "測試消息")
            
            assert result["messages"][0]["id"] == "msg_789"
    
    def test_receive_message(self):
        """測試接收消息"""
        test_payload = {
            "object": "whatsapp_business_account",
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "from": "1234567890",
                            "text": {"body": "測試消息"}
                        }]
                    }
                }]
            }]
        }
        
        service = WhatsAppService()
        messages = service.parse_webhook(test_payload)
        
        assert len(messages) == 1
        assert messages[0]["from"] == "1234567890"
        assert messages[0]["text"] == "測試消息"

class TestBridgeService:
    def test_process_command_insert(self):
        """測試處理插入命令"""
        service = BridgeService()
        
        # Mock Lark 服務
        mock_lark = Mock()
        mock_lark.insert_content.return_value = {
            "paragraph_id": "para_123",
            "position": 5
        }
        
        service.lark_service = mock_lark
        
        result = service.process_command(
            command="insert",
            content="測試內容",
            target="test_doc"
        )
        
        assert result["paragraph_id"] == "para_123"
        assert result["position"] == 5
    
    def test_process_command_query(self):
        """測試處理查詢命令"""
        service = BridgeService()
        
        # Mock Lark 服務
        mock_lark = Mock()
        mock_lark.query_document.return_value = {
            "document": {
                "title": "測試文檔",
                "content": "文檔內容"
            }
        }
        
        service.lark_service = mock_lark
        
        result = service.process_command(
            command="query",
            content="測試文檔"
        )
        
        assert result["document"]["title"] == "測試文檔"
        assert result["document"]["content"] == "文檔內容"
```

## 集成測試示例

### 測試 Lark API 集成
```python
# tests/test_integration/test_lark_api.py
import pytest
import os
from app.integrations.lark import LarkClient

@pytest.mark.integration
class TestLarkAPI:
    @pytest.fixture
    def lark_client(self):
        """創建 Lark 客戶端"""
        return LarkClient(
            app_id=os.getenv("LARK_APP_ID"),
            app_secret=os.getenv("LARK_APP_SECRET")
        )
    
    def test_get_tenant_access_token(self, lark_client):
        """測試獲取租戶訪問令牌"""
        token = lark_client.get_tenant_access_token()
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_search_documents(self, lark_client):
        """測試搜索文檔"""
        # 使用測試數據
        result = lark_client.search_documents(
            query="測試",
            count=10
        )
        
        assert isinstance(result, list)
        if result:  # 如果有結果
            doc = result[0]
            assert "document_id" in doc
            assert "title" in doc
    
    def test_create_document(self, lark_client):
        """測試創建文檔"""
        result = lark_client.create_document(
            title="測試文檔",
            content="測試內容",
            folder_token="test_folder"
        )
        
        assert "document_id" in result
        assert "url" in result
    
    def test_update_document(self, lark_client):
        """測試更新文檔"""
        # 先創建文檔
        create_result = lark_client.create_document(
            title="測試更新",
            content="原始內容",
            folder_token="test_folder"
        )
        
        doc_id = create_result["document_id"]
        
        # 更新文檔
        update_result = lark_client.update_document(
            document_id=doc_id,
            content="更新後的內容"
        )
        
        assert update_result["success"] is True
    
    def test_get_document_content(self, lark_client):
        """測試獲取文檔內容"""
        # 先創建文檔
        create_result = lark_client.create_document(
            title="測試獲取",
            content="文檔內容",
            folder_token="test_folder"
        )
        
        doc_id = create_result["document_id"]
        
        # 獲取內容
        content = lark_client.get_document_content(doc_id)
        
        assert content is not None
        assert "文檔內容" in content
```

### 測試 WhatsApp API 集成
```python
# tests/test_integration/test_whatsapp_api.py
import pytest
import os
from app.integrations.whatsapp import WhatsAppClient

@pytest.mark.integration
class TestWhatsAppAPI:
    @pytest.fixture
    def whatsapp_client(self):
        """創建 WhatsApp 客戶端"""
        return WhatsAppClient(
            access_token=os.getenv("WHATSAPP_ACCESS_TOKEN"),
            phone_number_id=os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        )
    
    def test_send_text_message(self, whatsapp_client):
        """測試發送文本消息"""
        result = whatsapp_client.send_message(
            to="1234567890",
            text="測試消息"
        )
        
        assert "messages" in result
        assert len(result["messages"]) > 0
        assert "id" in result["messages"][0]
    
    def test_send_template_message(self, whatsapp_client):
        """測試發送模板消息"""
        result = whatsapp_client.send_template(
            to="1234567890",
            template_name="test_template",
            language_code="en_US"
        )
        
        assert "messages" in result
        assert len(result["messages"]) > 0
    
    def test_get_message_status(self, whatsapp_client):
        """測試獲取消息狀態"""
        # 先發送消息
        send_result = whatsapp_client.send_message(
            to="1234567890",
            text="狀態測試"
        )
        
        message_id = send_result["messages"][0]["id"]
        
        # 獲取狀態
        status = whatsapp_client.get_message_status(message_id)
        
        assert "status" in status
        assert status["status"] in ["sent", "delivered", "read"]
    
    def test_webhook_verification(self, whatsapp_client):
        """測試 Webhook 驗證"""
        challenge = "test_challenge_123"
        
        result = whatsapp_client.verify_webhook(
            mode="subscribe",
            token="test_token",
            challenge=challenge
        )
        
        assert result == challenge
```

### 測試橋接服務集成
```python
# tests/test_integration/test_bridge.py
import pytest
from app.bridge import WhatsAppLarkBridge
from unittest.mock import Mock, patch

@pytest.mark.integration
class TestBridgeIntegration:
    def test_process_whatsapp_message(self):
        """測試處理 WhatsApp 消息"""
        bridge = WhatsAppLarkBridge()
        
        # Mock 服務
        bridge.lark_service = Mock()
        bridge.lark_service.query_document.return_value = {
            "document": {
                "title": "測試文檔",
                "content": "文檔內容"
            }
        }
        
        bridge.whatsapp_service = Mock()
        bridge.whatsapp_service.send_message.return_value = {
            "messages": [{"id": "msg_123"}]
        }
        
        # 測試消息
        whatsapp_message = {
            "from": "1234567890",
            "text": "@Lark query 測試文檔"
        }
        
        result = bridge.process_message(whatsapp_message)
        
        assert result["success"] is True
        assert "response" in result
    
    def test_command_parsing(self):
        """測試命令解析"""
        bridge = WhatsAppLarkBridge()
        
        test_cases = [
            {
                "input": "@Lark insert 測試內容 to test_doc",
                "expected": {
                    "command": "insert",
                    "content": "測試內容",
                    "target": "test_doc"
                }
            },
            {
                "input": "@Lark query 測試文檔",
                "expected": {
                    "command": "query",
                    "content": "測試文檔",
                    "target": None
                }
            },
            {
                "input": "@Lark update para_123: 新內容",
                "expected": {
                    "command": "update",
                    "content": "新內容",
                    "target": "para_123"
                }
            },
            {
                "input": "@Lark todo: 完成測試",
                "expected": {
                    "command": "todo",
                    "content": "完成測試",
                    "target": None
                }
            }
        ]
        
        for test_case in test_cases:
            result = bridge.parse_command(test_case["input"])
            assert result == test_case["expected"]
    
    def test_error_handling(self):
        """測試錯誤處理"""
        bridge = WhatsAppLarkBridge()
        
        # Mock 服務拋出異常
        bridge.lark_service = Mock()
        bridge.lark_service.query_document.side_effect = Exception("API 錯誤")
        
        bridge.whatsapp_service = Mock()
        
        result = bridge.process_message({
            "from": "1234567890",
            "text": "@Lark query 不存在的文檔"
        })
        
        assert result["success"] is False
        assert "error" in result
        assert "API 錯誤" in result["error"]
```

## 端到端測試示例

### 測試完整工作流
```python
# tests/test_e2e/test_workflows.py
import pytest
import asyncio
from app.main import app
from fastapi.testclient import TestClient

@pytest.mark.e2e
class TestEndToEndWorkflows:
    @pytest.fixture
    def client(self):
        """創建測試客戶端"""
        return TestClient(app)
    
    def test_whatsapp_webhook_flow(self, client):
        """測試 WhatsApp Webhook 完整流程"""
        # 1. WhatsApp Webhook 驗證
        verify_response = client.get("/webhook/whatsapp", params={
            "hub.mode": "subscribe",
            "hub.verify_token": "test_token",
            "hub.challenge": "test_challenge"
        })
        
        assert verify_response.status_code == 200
        assert verify_response.text == "test_challenge"
        
        # 2. 接收 WhatsApp 消息
        webhook_payload = {
            "object": "whatsapp_business_account",
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "from": "1234567890",
                            "text": {"body": "@Lark query 測試文檔"}
                        }]
                    }
                }]
            }]
        }
        
        webhook_response = client.post("/webhook/whatsapp", json=webhook_payload)
        
        assert webhook_response.status_code == 200
        
        # 3. 檢查數據庫記錄
        db_response = client.get("/api/messages")
        
        assert db_response.status_code == 200
        messages = db_response.json()
        
        assert len(messages) > 0
        latest_message = messages[-1]
        assert latest_message["content"] == "@Lark query 測試文檔"
        assert latest_message["sender"] == "1234567890"
    
    def test_lark_command_processing(self, client):
        """測試 Lark 命令處理流程"""
        # 1. 發送命令
        command_response = client.post("/api/commands", json={
            "command": "insert",
            "content": "測試內容",
            "target": "test_doc",
            "sender": "test_user"
        })
        
        assert command_response.status_code == 200
        command_result = command_response.json()
        
        assert command_result["success"] is True
        assert "paragraph_id" in command_result
        
        # 2. 驗證文檔更新
        doc_response = client.get(f"/api/documents/test_doc")
        
        assert doc_response.status_code == 200
        document = doc_response.json()
        
        assert "測試內容" in document["content"]
    
    def test_error_recovery_flow(self, client):
        """測試錯誤恢復流程"""
        # 1. 發送錯誤命令
        error_response = client.post("/api/commands", json={
            "command": "invalid_command",
            "content": "測試",
            "sender": "test_user"
        })
        
        assert error_response.status_code == 400
        error_result = error_response.json()
        
        assert error_result["success"] is False
        assert "error" in error_result
        
        # 2. 檢查錯誤日誌
        logs_response = client.get("/api/logs/errors")
        
        assert logs_response.status_code == 200
        logs = logs_response.json()
        
        assert len(logs) > 0
        assert "invalid_command" in logs[-1]["message"]
    
    def test_performance_monitoring(self, client):
        """測試性能監控"""
        import time
        
        # 測試多個並發請求
        start_time = time.time()
        
        responses = []
        for i in range(10):
            response = client.post("/api/commands", json={
                "command": "query",
                "content": f"文檔{i}",
                "sender": f"user{i}"
            })
            responses.append(response)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 所有請求應該成功
        for response in responses:
            assert response.status_code == 200
        
        # 性能檢查：10個請求應該在5秒內完成
        assert duration < 5
        
        # 檢查性能指標
        metrics_response = client.get("/api/metrics")
        
        assert metrics_response.status_code == 200
        metrics = metrics_response.json()
        
        assert "request_count" in metrics
        assert "average_response_time" in metrics
        assert metrics["request_count"] >= 10
```

### 測試真實場景
```python
# tests/test_e2e/test_scenarios.py
import pytest
from app.scenarios import (
    MeetingNotesScenario,
    TaskAssignmentScenario,
    DocumentSearchScenario,
    StatusReportScenario
)

@pytest.mark.e2e
class TestRealWorldScenarios:
    def test_meeting_notes_scenario(self):
        """測試會議記錄場景"""
        scenario = MeetingNotesScenario()
        
        # 模擬會議討論
        messages = [
            "今天的會議要點：",
            "1. 專案進度超前",
            "2. 需要增加測試資源",
            "3. 下周三進行演示",
            "@Lark insert 會議總結：專案進度超前，需要增加測試資源，下周三進行演示 to weekly_report"
        ]
        
        results = []
        for msg in messages:
            result = scenario.process_message(msg, sender="meeting_host")
            results.append(result)
        
        # 驗證結果
        assert len(results) == 5
        assert results[-1]["success"] is True
        assert "paragraph_id" in results[-1]
        
        # 驗證文檔更新
        document = scenario.get_document("weekly_report")
        assert "會議總結" in document
        assert "專案進度超前" in document
    
    def test_task_assignment_scenario(self):
        """測試任務分配場景"""
        scenario = TaskAssignmentScenario()
        
        # 模擬任務分配
        commands = [
            "@Lark todo: 小明完成API文檔",
            "@Lark todo: 小華測試新功能",
            "@Lark todo: 小張準備演示材料"
        ]
        
        tasks = []
        for cmd in commands:
            result = scenario.process_command(cmd, sender="manager")
            tasks.append(result)
        
        # 驗證結果
        assert len(tasks) == 3
        for task in tasks:
            assert task["success"] is True
            assert "record_id" in task
        
        # 驗證待辦事項列表
        todo_list = scenario.get_todo_list()
        assert len(todo_list) == 3
        assert any("API文檔" in item["content"] for item in todo_list)
        assert any("測試新功能" in item["content"] for item in todo_list)
        assert any("演示材料" in item["content"] for item in todo_list)
    
    def test_document_search_scenario(self):
        """測試文檔搜索場景"""
        scenario = DocumentSearchScenario()
        
        # 創建測試文檔
        scenario.create_document(
            title="專案規劃書",
            content="專案概述：本專案旨在...\n目標：在Q2完成...\n時間安排：1月完成設計..."
        )
        
        # 搜索文檔
        result = scenario.process_command(
            "@Lark query 專案規劃書",
            sender="new_member"
        )
        
        # 驗證結果
        assert result["success"] is True
        assert "document" in result
        assert result["document"]["title"] == "專案規劃書"
        assert "專案概述" in result["document"]["content"]
    
    def test_status_report_scenario(self):
        """測試狀態報告場景"""
        scenario = StatusReportScenario()
        
        # 模擬每日報告
        report = """
今日工作：
- 完成了用戶登錄功能
- 修復了3個bug
- 開始編寫測試用例
"""
        
        result = scenario.process_command(
            f"@Lark insert 2024-01-15 工作報告：{report} to daily_reports",
            sender="team_member"
        )
        
        # 驗證結果
        assert result["success"] is True
        assert "paragraph_id" in result
        
        # 驗證報告內容
        reports = scenario.get_daily_reports()
        assert len(reports) > 0
        latest_report = reports[-1]
        assert "2024-01-15" in latest_report
        assert "用戶登錄功能" in latest_report
        assert "修復了3個bug" in latest_report
```

## 性能測試示例

### 測試負載性能
```python
# tests/test_performance/test_load.py
import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from app.main import app
from fastapi.testclient import TestClient

@pytest.mark.performance
class TestLoadPerformance:
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_concurrent_commands(self, client):
        """測試並發命令處理"""
        num_requests = 100
        results = []
        
        def send_command(i):
            response = client.post("/api/commands", json={
                "command": "query",
                "content": f"文檔{i}",
                "sender": f"user{i % 10}"  # 10個用戶循環
            })
            return response.status_code
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(send_command, i) for i in range(num_requests)]
            results = [future.result() for future in futures]
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 驗證所有請求成功
        assert all(status == 200 for status in results)
        
        # 性能要求：100個請求在10秒內完成
        assert duration < 10
        
        # 計算 QPS
        qps = num_requests / duration
        print(f"\n並發性能測試：")
        print(f"  請求數量：{num_requests}")
        print(f"  總耗時：{duration:.2f}秒")
        print(f"  QPS：{qps:.2f}")
        
        # QPS 應該大於 10
        assert qps > 10
    
    def test_memory_usage(self, client):
        """測試內存使用"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # 記錄初始內存
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 發送大量請求
        for i in range(1000):
            client.post("/api/commands", json={
                "command": "query",
                "content": f"測試{i}",
                "sender": "test_user"
            })
        
        # 記錄最終內存
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"\n內存使用測試：")
        print(f"  初始內存：{initial_memory:.2f} MB")
        print(f"  最終內存：{final_memory:.2f} MB")
        print(f"  內存增長：{memory_increase:.2f} MB")
        
        # 內存增長應該小於 50MB
        assert memory_increase < 50
    
    def test_response_time_percentile(self, client):
        """測試響應時間百分位"""
        response_times = []
        
        # 發送100個請求
        for i in range(100):
            start_time = time.time()
            client.post("/api/commands", json={
                "command": "insert",
                "content": f"內容{i}",
                "target": "test_doc",
                "sender": f"user{i}"
            })
            end_time = time.time()
            response_times.append(end_time - start_time)
        
        # 計算百分位
        sorted_times = sorted(response_times)
        p50 = sorted_times[50]  # 中位數
        p90 = sorted_times[90]  # 90百分位
        p99 = sorted_times[99]  # 99百分位
        
        print(f"\n響應時間百分位：")
        print(f"  P50：{p50:.3f}秒")
        print(f"  P90：{p90:.3f}秒")
        print(f"  P99：{p99:.3f}秒")
        
        # 性能要求
        assert p50 < 0.5   # 50%的請求在0.5秒內完成
        assert p90 < 1.0   # 90%的請求在1秒內完成
        assert p99 < 2.0   # 99%的請求在2秒內完成
```

### 測試壓力測試
```python
# tests/test_performance/test_stress.py
import pytest
import time
import statistics
from locust import HttpUser, task, between

@pytest.mark.stress
class TestStressPerformance:
    def test_sustained_load(self):
        """測試持續負載"""
        # 使用 Locust 進行壓力測試
        class BridgeUser(HttpUser):
            wait_time = between(1, 3)
            
            @task
            def send_command(self):
                self.client.post("/api/commands", json={
                    "command": "query",
                    "content": "測試文檔",
                    "sender": "stress_user"
                })
            
            @task(3)
            def send_insert(self):
                self.client.post("/api/commands", json={
                    "command": "insert",
                    "content": "壓力測試內容",
                    "target": "stress_doc",
                    "sender": "stress_user"
                })
        
        # 運行壓力測試的邏輯（實際運行需要 locust）
        print("壓力測試需要單獨運行：")
        print("  locust -f tests/test_performance/test_stress.py")
    
    def test_peak_traffic(self, client):
        """測試峰值流量"""
        import threading
        
        request_count = 0
        error_count = 0
        lock = threading.Lock()
        
        def send_requests(num):
            nonlocal request_count, error_count
            for i in range(num):
                try:
                    response = client.post("/api/commands", json={
                        "command": "query",
                        "content": f"峰值測試{i}",
                        "sender": f"user{threading.current_thread().ident}"
                    })
                    
                    with lock:
                        request_count += 1
                        if response.status_code != 200:
                            error_count += 1
                except Exception:
                    with lock:
                        error_count += 1
        
        # 創建多個線程模擬峰值
        threads = []
        start_time = time.time()
        
        for _ in range(20):  # 20個並發線程
            t = threading.Thread(target=send_requests, args=(50,))  # 每個線程50個請求
            threads.append(t)
            t.start()
        
        # 等待所有線程完成
        for t in threads:
            t.join()
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n峰值流量測試：")
        print(f"  總請求數：{request_count}")
        print(f"  錯誤數：{error_count}")
        print(f"  錯誤率：{(error_count/request_count*100):.2f}%")
        print(f"  總耗時：{duration:.2f}秒")
        print(f"  平均 QPS：{request_count/duration:.2f}")
        
        # 驗證要求
        assert error_count == 0  # 應該沒有錯誤
        assert duration < 30     # 1000個請求應該在30秒內完成
    
    def test_recovery_after_stress(self, client):
        """測試壓力後的恢復"""
        # 先進行壓力測試
        for i in range(500):
            client.post("/api/commands", json={
                "command": "query",
                "content": f"恢復測試{i}",
                "sender": "recovery_user"
            })
        
        # 等待系統穩定
        time.sleep(2)
        
        # 測試恢復後的性能
        response_times = []
        for i in range(10):
            start_time = time.time()
            response = client.post("/api/commands", json={
                "command": "query",
                "content": "恢復後測試",
                "sender": "recovery_user"
            })
            end_time = time.time()
            
            assert response.status_code == 200
            response_times.append(end_time - start_time)
        
        avg_response_time = statistics.mean(response_times)
        
        print(f"\n壓力後恢復測試：")
        print(f"  平均響應時間：{avg_response_time:.3f}秒")
        
        # 恢復後響應時間應該正常
        assert avg_response_time < 1.0
```

## 測試配置

### pytest 配置文件
```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --cov=app
    --cov-report=term-missing
    --cov-report=html
    --cov-report=xml
    -p no:warnings
markers =
    unit: 單元測試
    integration: 集成測試
    e2e: 端到端測試
    performance: 性能測試
    stress: 壓力測試
    slow: 慢速測試
```

### 測試環境變量
```bash
# .env.testing
APP_ENV=testing
DEBUG=true
LOG_LEVEL=DEBUG

# 數據庫
DATABASE_URL=sqlite:///test.db

# Lark 測試配置
LARK_APP_ID=test_app_id
LARK_APP_SECRET=test_app_secret
LARK_BASE_URL=https://open.feishu.cn/open-apis

# WhatsApp 測試配置
WHATSAPP_ACCESS_TOKEN=test_token
WHATSAPP_PHONE_NUMBER_ID=test_number
WHATSAPP_BASE_URL=https://graph.facebook.com/v18.0

# Redis 測試配置
REDIS_URL=redis://localhost:6379/0

# 測試限制
MAX_REQUESTS_PER_MINUTE=1000
MAX_CONCURRENT_CONNECTIONS=50
```

### 測試數據準備腳本
```python
# tests/conftest.py
import pytest
import os
import tempfile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, User, Message, Document

@pytest.fixture(scope="session")
def test_database():
    """創建測試數據庫"""
    # 使用臨時文件
    tmp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_url = f"sqlite:///{tmp_file.name}"
    
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    
    yield db_url
    
    # 清理
    tmp_file.close()
    os.unlink(tmp_file.name)

@pytest.fixture
def db_session(test_database):
    """創建數據庫會話"""
    engine = create_engine(test_database)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    session.rollback()
    session.close()

@pytest.fixture
def test_user(db_session):
    """創建測試用戶"""
    user = User(
        name="測試用戶",
        email="test@example.com",
        platform="whatsapp",
        platform_id="1234567890"
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def test_document(db_session):
    """創建測試文檔"""
    doc = Document(
        title="測試文檔",
        content="測試內容",
        created_by="test_user"
    )
    db_session.add(doc)
    db_session.commit()
    return doc

@pytest.fixture
def test_message(db_session, test_user):
    """創建測試消息"""
    message = Message(
        content="@Lark query 測試文檔",
        sender=test_user.platform_id,
        platform="whatsapp"
    )
    db_session.add(message)
    db_session.commit()
    return message
```

## 測試運行命令

### 基本測試
```bash
# 運行所有測試
pytest

# 運行特定類型的測試
pytest -m unit
pytest -m integration
pytest -m e2e
pytest -m performance

# 運行特定文件
pytest tests/test_unit/test_models.py
pytest tests/test_integration/test_lark_api.py

# 運行特定測試函數
pytest tests/test_unit/test_models.py::test_user_model
pytest tests/test_integration/test_lark_api.py::TestLarkAPI::test_get_tenant_access_token
```

### 測試報告
```bash
# 生成 HTML 報告
pytest --cov=app --cov-report=html

# 生成 XML 報告（用於 CI/CD）
pytest --cov=app --cov-report=xml

# 顯示測試覆蓋率
pytest --cov=app --cov-report=term-missing

# 生成性能報告
pytest tests/test_performance/ -v --durations=10
```

### 持續集成
```bash
# GitHub Actions 示例
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      - name: Run tests
        run: |
          pytest --cov=app --cov-report=xml --junitxml=test-results.xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
        with:
          files: ./coverage.xml
      - name: Upload test results
        uses: actions/upload-artifact@v2
        with:
          name: test-results
          path: test-results.xml
```

## 測試最佳實踐

### 1. 測試命名
- 使用描述性的測試名稱
- 遵循 `test_<場景>_<預期結果>` 格式
- 使用英文命名，保持一致性

### 2. 測試隔離
- 每個測試應該獨立運行
- 使用 fixture 設置和清理測試數據
- 避免測試之間的依賴

### 3. 測試數據
- 使用工廠函數創建測試數據
- 避免硬編碼的測試數據
- 使用隨機數據避免衝突

### 4. 錯誤處理
- 測試正常路徑和錯誤路徑
- 驗證錯誤消息和狀態碼
- 測試邊界條件和異常情況

### 5. 性能考慮
- 測試響應時間和資源使用
- 模擬真實的負載場景
- 監控內存泄漏和性能退化

### 6. 持續改進
- 定期更新測試用例
- 根據生產問題添加測試
- 保持測試覆蓋率在 80% 以上

## 故障排除

### 常見問題
1. **測試數據庫鎖定**
   ```bash
   rm -f test.db
   ```

2. **API 速率限制**
   ```python
   # 添加延遲
   import time
   time.sleep(1)
   ```

3. **網絡連接問題**
   ```python
   # 使用模擬對象
   from unittest.mock import Mock, patch
   ```

4. **測試超時**
   ```bash
   # 增加超時時間
   pytest --timeout=30
   ```

### 調試技巧
```python
# 在測試中添加調試輸出
import logging
logging.basicConfig(level=logging.DEBUG)

# 使用 pdb 調試
import pdb; pdb.set_trace()

# 檢查響應內容
print(response.json())
```

### 性能優化
```python
# 使用會話級別的 fixture
@pytest.fixture(scope="session")
def shared_resource():
    yield resource

# 批量操作測試數據
def test_batch_operations():
    # 一次性創建多個測試對象
    objects = [TestObject() for _ in range(100)]
    
# 使用內存數據庫
DATABASE_URL="sqlite:///:memory:"
```

## 結論

WhatsApp-Lark Bridge 的測試套件提供了全面的測試覆蓋，包括：

1. **單元測試**：驗證各個組件的正確性
2. **集成測試**：驗證組件之間的協作
3. **端到端測試**：驗證完整的工作流程
4. **性能測試**：驗證系統性能和穩定性

通過這些測試，我們可以確保系統的：
- 功能正確性
- 系統穩定性
- 性能可靠性
- 錯誤恢復能力

定期運行這些測試並根據生產反饋不斷改進，可以確保 WhatsApp-Lark Bridge 的高質量和高可靠性。