# WhatsApp-Lark Bridge 測試腳本

#!/usr/bin/env python3
"""
WhatsApp-Lark Bridge 測試腳本
用於測試 Webhook 和 Lark API 功能
"""

import os
import sys
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# 添加項目根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 載入環境變量
load_dotenv()

class WhatsAppLarkBridgeTester:
    """測試器類"""
    
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.test_messages = [
            {
                "name": "查詢文檔",
                "message": "@Lark query doc_project_plan",
                "expected_operation": "query"
            },
            {
                "name": "新增內容",
                "message": "@Lark insert 會議摘要：討論了Q2目標和時間線",
                "expected_operation": "insert"
            },
            {
                "name": "創建待辦事項",
                "message": "@Lark todo: 跟進客戶反饋，優先級高",
                "expected_operation": "todo"
            },
            {
                "name": "幫助命令",
                "message": "@Lark help",
                "expected_operation": "unknown"
            },
            {
                "name": "非 Lark 命令",
                "message": "今天天氣怎麼樣？",
                "expected_operation": None
            }
        ]
    
    def test_health_endpoint(self):
        """測試健康檢查端點"""
        print("🧪 測試健康檢查端點...")
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 健康檢查通過: {data}")
                return True
            else:
                print(f"❌ 健康檢查失敗: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 健康檢查錯誤: {e}")
            return False
    
    def test_lark_connection(self):
        """測試 Lark API 連接"""
        print("🧪 測試 Lark API 連接...")
        try:
            response = requests.get(f"{self.base_url}/test/lark", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Lark 連接測試: {data}")
                return data.get('lark_connected', False)
            else:
                print(f"❌ Lark 連接測試失敗: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Lark 連接測試錯誤: {e}")
            return False
    
    def test_webhook_endpoint(self, message_data):
        """測試 Webhook 端點"""
        print(f"🧪 測試 Webhook 端點: {message_data['name']}")
        
        # 模擬 WhatsApp Webhook 請求
        payload = {
            "messages": [
                {
                    "from": "test_user",
                    "id": "test_message_id",
                    "timestamp": datetime.now().isoformat(),
                    "text": {
                        "body": message_data["message"]
                    },
                    "type": "text"
                }
            ]
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/webhook/whatsapp",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Webhook 測試通過")
                print(f"   狀態: {result.get('status')}")
                print(f"   操作: {result.get('operation', 'N/A')}")
                print(f"   消息: {result.get('message', '')[:50]}...")
                
                # 驗證操作類型
                if message_data["expected_operation"] is None:
                    # 非 Lark 命令應該被忽略
                    if result.get('status') == 'ignored':
                        return True
                    else:
                        print(f"❌ 預期忽略，但收到: {result.get('status')}")
                        return False
                else:
                    # Lark 命令應該被處理
                    if result.get('operation') == message_data["expected_operation"]:
                        return True
                    else:
                        print(f"❌ 預期操作 {message_data['expected_operation']}，但收到: {result.get('operation')}")
                        return False
            else:
                print(f"❌ Webhook 測試失敗: {response.status_code}")
                print(f"   響應: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Webhook 測試錯誤: {e}")
            return False
    
    def run_all_tests(self):
        """運行所有測試"""
        print("=" * 50)
        print("🚀 WhatsApp-Lark Bridge 測試開始")
        print("=" * 50)
        
        test_results = []
        
        # 測試健康檢查
        health_ok = self.test_health_endpoint()
        test_results.append(("健康檢查", health_ok))
        
        # 測試 Lark 連接
        lark_ok = self.test_lark_connection()
        test_results.append(("Lark 連接", lark_ok))
        
        # 測試 Webhook 端點
        for test_case in self.test_messages:
            webhook_ok = self.test_webhook_endpoint(test_case)
            test_results.append((f"Webhook: {test_case['name']}", webhook_ok))
        
        # 顯示測試結果
        print("\n" + "=" * 50)
        print("📊 測試結果總結")
        print("=" * 50)
        
        all_passed = True
        for test_name, passed in test_results:
            status = "✅ 通過" if passed else "❌ 失敗"
            print(f"{status}: {test_name}")
            if not passed:
                all_passed = False
        
        print("=" * 50)
        if all_passed:
            print("🎉 所有測試通過！")
        else:
            print("⚠️  部分測試失敗，請檢查配置和日誌。")
        
        return all_passed
    
    def test_integration(self):
        """集成測試：模擬完整流程"""
        print("\n" + "=" * 50)
        print("🔗 集成測試：模擬完整 WhatsApp-Lark 流程")
        print("=" * 50)
        
        # 模擬用戶發送消息
        test_message = "@Lark query doc_project_plan"
        print(f"📱 模擬用戶發送: {test_message}")
        
        # 發送到 Webhook
        payload = {
            "messages": [
                {
                    "from": "user_123",
                    "id": "msg_001",
                    "timestamp": datetime.now().isoformat(),
                    "text": {
                        "body": test_message
                    },
                    "type": "text"
                }
            ]
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/webhook/whatsapp",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 集成測試成功")
                print(f"   服務器響應: {result}")
                
                # 驗證響應格式
                required_fields = ['status', 'operation', 'message', 'timestamp']
                if all(field in result for field in required_fields):
                    print(f"✅ 響應格式正確")
                    return True
                else:
                    print(f"❌ 響應格式錯誤，缺少字段")
                    return False
            else:
                print(f"❌ 集成測試失敗: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 集成測試錯誤: {e}")
            return False

def main():
    """主函數"""
    tester = WhatsAppLarkBridgeTester()
    
    # 檢查服務是否運行
    try:
        requests.get("http://localhost:5000/health", timeout=2)
        print("✅ 檢測到服務正在運行")
    except:
        print("❌ 服務未運行，請先啟動服務")
        print("   運行命令: python scripts/app.py")
        return
    
    # 運行測試
    all_tests_passed = tester.run_all_tests()
    
    # 運行集成測試
    if all_tests_passed:
        integration_passed = tester.test_integration()
        if integration_passed:
            print("\n🎉 集成測試通過！系統準備就緒。")
        else:
            print("\n⚠️  集成測試失敗，請檢查服務配置。")
    else:
        print("\n⚠️  基本測試失敗，跳過集成測試。")

if __name__ == "__main__":
    main()