#!/usr/bin/env python3
"""
Lark任務提醒測試腳本
測試所有邊界案例和正常情況
"""

import os
import sys
import json
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch, MagicMock

# 添加父目錄到Python路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 設置測試環境變量
os.environ.update({
    "LARK_APP_ID": "test_app_id",
    "LARK_APP_SECRET": "test_app_secret",
    "LARK_BASE_TOKEN": "test_base_token",
    "LARK_TABLE_ID": "test_table_id",
    "WHATSAPP_CHAT_ID": "test_chat_id"
})

from scripts.run_reminder import LarkTaskReminder

class TestLarkTaskReminder(unittest.TestCase):
    """Lark任務提醒測試類"""
    
    def setUp(self):
        """測試設置"""
        self.hkt = timezone(timedelta(hours=8))
        self.now_hkt = datetime.now(self.hkt)
        
        # 創建測試實例
        self.reminder = LarkTaskReminder()
        
        # 覆蓋API調用方法
        self.reminder._call_lark_api = Mock()
        self.reminder._send_whatsapp_message = Mock()
        
    def test_01_normal_case_d_minus_one_task(self):
        """測試1: 正常D-1任務"""
        print("\n" + "="*60)
        print("測試1: 正常D-1任務")
        print("="*60)
        
        # 設置模擬任務數據
        mock_tasks = [
            {
                "record_id": "rec001",
                "fields": {
                    "任務標題": "完成季度報告",
                    "負責人": [{"id": "ou_123456", "name": "張三"}],
                    "預計完成日期": (self.now_hkt + timedelta(days=1)).strftime('%Y-%m-%d'),
                    "任務狀態": "進行中",
                    "文檔連結": "https://example.com/doc1"
                }
            }
        ]
        
        # 設置模擬API響應
        self.reminder._call_lark_api.side_effect = [
            {"success": True, "data": {"items": []}},  # 字段列表
            {"success": True, "data": {"items": mock_tasks}}  # 任務列表
        ]
        
        # 設置模擬WhatsApp發送成功
        self.reminder._send_whatsapp_message.return_value = {
            "success": True,
            "message_id": "om_123456",
            "chat_id": "test_chat_id",
            "sent_at": datetime.now(self.hkt).isoformat()
        }
        
        # 執行處理
        result = self.reminder.process_tasks()
        
        # 驗證結果
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["summary"]["total_tasks"], 1)
        self.assertEqual(result["summary"]["d_minus_one_tasks"], 1)
        self.assertEqual(result["summary"]["sent_success"], 1)
        self.assertEqual(result["summary"]["sent_failed"], 0)
        self.assertEqual(result["summary"]["skipped"], 0)
        
        print("✓ 正常D-1任務測試通過")
        return result
    
    def test_02_no_d_minus_one_tasks(self):
        """測試2: 無D-1任務"""
        print("\n" + "="*60)
        print("測試2: 無D-1任務")
        print("="*60)
        
        # 設置模擬任務數據（所有任務要麼已完成，要麼日期不是D-1）
        mock_tasks = [
            {
                "record_id": "rec001",
                "fields": {
                    "任務標題": "已完成任務",
                    "負責人": [{"id": "ou_123456", "name": "張三"}],
                    "預計完成日期": (self.now_hkt + timedelta(days=1)).strftime('%Y-%m-%d'),
                    "任務狀態": "已完成",
                    "文檔連結": "https://example.com/doc1"
                }
            },
            {
                "record_id": "rec002",
                "fields": {
                    "任務標題": "未來任務",
                    "負責人": [{"id": "ou_234567", "name": "李四"}],
                    "預計完成日期": (self.now_hkt + timedelta(days=5)).strftime('%Y-%m-%d'),
                    "任務狀態": "進行中",
                    "文檔連結": "https://example.com/doc2"
                }
            }
        ]
        
        # 設置模擬API響應
        self.reminder._call_lark_api.side_effect = [
            {"success": True, "data": {"items": []}},
            {"success": True, "data": {"items": mock_tasks}}
        ]
        
        # 執行處理
        result = self.reminder.process_tasks()
        
        # 驗證結果
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["summary"]["total_tasks"], 2)
        self.assertEqual(result["summary"]["d_minus_one_tasks"], 0)
        self.assertEqual(result["summary"]["sent_success"], 0)
        self.assertEqual(result["summary"]["skipped_reasons"].get("status_completed", 0), 1)
        
        print("✓ 無D-1任務測試通過")
        return result
    
    def test_03_task_completed_or_cancelled(self):
        """測試3: 任務已完成/已取消"""
        print("\n" + "="*60)
        print("測試3: 任務已完成/已取消")
        print("="*60)
        
        mock_tasks = [
            {
                "record_id": "rec001",
                "fields": {
                    "任務標題": "已完成任務",
                    "負責人": [{"id": "ou_123456", "name": "張三"}],
                    "預計完成日期": (self.now_hkt + timedelta(days=1)).strftime('%Y-%m-%d'),
                    "任務狀態": "已完成",
                    "文檔連結": "https://example.com/doc1"
                }
            },
            {
                "record_id": "rec002",
                "fields": {
                    "任務標題": "已取消任務",
                    "負責人": [{"id": "ou_234567", "name": "李四"}],
                    "預計完成日期": (self.now_hkt + timedelta(days=1)).strftime('%Y-%m-%d'),
                    "任務狀態": "已取消",
                    "文檔連結": "https://example.com/doc2"
                }
            }
        ]
        
        self.reminder._call_lark_api.side_effect = [
            {"success": True, "data": {"items": []}},
            {"success": True, "data": {"items": mock_tasks}}
        ]
        
        result = self.reminder.process_tasks()
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["summary"]["d_minus_one_tasks"], 0)
        self.assertEqual(result["summary"]["skipped_reasons"].get("status_completed", 0), 2)
        
        print("✓ 已完成/已取消任務測試通過")
        return result
    
    def test_04_missing_due_date(self):
        """測試4: 缺少預計完成日期"""
        print("\n" + "="*60)
        print("測試4: 缺少預計完成日期")
        print("="*60)
        
        mock_tasks = [
            {
                "record_id": "rec001",
                "fields": {
                    "任務標題": "缺少日期任務",
                    "負責人": [{"id": "ou_123456", "name": "張三"}],
                    "預計完成日期": "",
                    "任務狀態": "進行中",
                    "文檔連結": "https://example.com/doc1"
                }
            }
        ]
        
        self.reminder._call_lark_api.side_effect = [
            {"success": True, "data": {"items": []}},
            {"success": True, "data": {"items": mock_tasks}}
        ]
        
        result = self.reminder.process_tasks()
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["summary"]["d_minus_one_tasks"], 0)
        self.assertEqual(result["summary"]["skipped_reasons"].get("missing_due_date", 0), 1)
        
        print("✓ 缺少預計完成日期測試通過")
        return result
    
    def test_05_missing_owner(self):
        """測試5: 缺少負責人"""
        print("\n" + "="*60)
        print("測試5: 缺少負責人")
        print("="*60)
        
        mock_tasks = [
            {
                "record_id": "rec001",
                "fields": {
                    "任務標題": "缺少負責人任務",
                    "負責人": [],
                    "預計完成日期": (self.now_hkt + timedelta(days=1)).strftime('%Y-%m-%d'),
                    "任務狀態": "進行中",
                    "文檔連結": "https://example.com/doc1"
                }
            }
        ]
        
        self.reminder._call_lark_api.side_effect = [
            {"success": True, "data": {"items": []}},
            {"success": True, "data": {"items": mock_tasks}}
        ]
        
        result = self.reminder.process_tasks()
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["summary"]["d_minus_one_tasks"], 0)
        self.assertEqual(result["summary"]["skipped_reasons"].get("missing_owner", 0), 1)
        
        print("✓ 缺少負責人測試通過")
        return result
    
    def test_06_lark_api_failure(self):
        """測試6: Lark API失敗"""
        print("\n" + "="*60)
        print("測試6: Lark API失敗")
        print("="*60)
        
        # 設置API調用失敗
        self.reminder._call_lark_api.side_effect = Exception("Lark API連接失敗")
        
        result = self.reminder.process_tasks()
        
        self.assertEqual(result["status"], "failed")
        self.assertTrue(len(result["errors"]) > 0)
        self.assertEqual(result["errors"][0]["type"], "unexpected_error")
        
        print("✓ Lark API失敗測試通過")
        return result
    
    def test_07_whatsapp_send_failure(self):
        """測試7: WhatsApp發送失敗"""
        print("\n" + "="*60)
        print("測試7: WhatsApp發送失敗")
        print("="*60)
        
        mock_tasks = [
            {
                "record_id": "rec001",
                "fields": {
                    "任務標題": "正常任務",
                    "負責人": [{"id": "ou_123456", "name": "張三"}],
                    "預計完成日期": (self.now_hkt + timedelta(days=1)).strftime('%Y-%m-%d'),
                    "任務狀態": "進行中",
                    "文檔連結": "https://example.com/doc1"
                }
            }
        ]
        
        self.reminder._call_lark_api.side_effect = [
            {"success": True, "data": {"items": []}},
            {"success": True, "data": {"items": mock_tasks}}
        ]
        
        # 設置WhatsApp發送失敗
        self.reminder._send_whatsapp_message.return_value = {
            "success": False,
            "error": "WhatsApp API連接失敗",
            "traceback": "詳細錯誤堆棧"
        }
        
        result = self.reminder.process_tasks()
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["summary"]["d_minus_one_tasks"], 1)
        self.assertEqual(result["summary"]["sent_success"], 0)
        self.assertEqual(result["summary"]["sent_failed"], 1)
        self.assertTrue(len(result["errors"]) > 0)
        
        print("✓ WhatsApp發送失敗測試通過")
        return result
    
    def test_08_timezone_boundary(self):
        """測試8: 時區邊界測試"""
        print("\n" + "="*60)
        print("測試8: 時區邊界測試")
        print("="*60)
        
        # 測試不同時區的日期計算
        test_cases = [
            {
                "name": "香港時間早上9點",
                "current_time": self.now_hkt.replace(hour=9, minute=0, second=0),
                "due_date": self.now_hkt.replace(hour=0, minute=0, second=0) + timedelta(days=1),
                "expected_days": 1
            },
            {
                "name": "香港時間晚上11點",
                "current_time": self.now_hkt.replace(hour=23, minute=0, second=0),
                "due_date": self.now_hkt.replace(hour=0, minute=0, second=0) + timedelta(days=1),
                "expected_days": 1  # 仍然是同一天
            },
            {
                "name": "跨午夜邊界",
                "current_time": self.now_hkt.replace(hour=0, minute=0, second=0) + timedelta(days=1),
                "due_date": self.now_hkt.replace(hour=0, minute=0, second=0) + timedelta(days=2),
                "expected_days": 1
            }
        ]
        
        for test_case in test_cases:
            # 臨時修改當前時間
            original_now = self.reminder.now_hkt
            self.reminder.now_hkt = test_case["current_time"]
            
            # 計算天數
            days = self.reminder._calculate_days_remaining(test_case["due_date"])
            
            # 恢復原始時間
            self.reminder.now_hkt = original_now
            
            self.assertEqual(days, test_case["expected_days"], 
                           f"{test_case['name']}: 預期{test_case['expected_days']}天，實際{days}天")
            
            print(f"  ✓ {test_case['name']}: {days}天")
        
        print("✓ 時區邊界測試通過")
        return True
    
    def test_09_date_parsing(self):
        """測試9: 日期解析測試"""
        print("\n" + "="*60)
        print("測試9: 日期解析測試")
        print("="*60)
        
        test_cases = [
            {"input": "2024-06-25", "should_succeed": True},
            {"input": "2024/06/25", "should_succeed": True},
            {"input": "2024年06月25日", "should_succeed": True},
            {"input": "1687622400000", "should_succeed": True},  # 毫秒時間戳
            {"input": "1687622400", "should_succeed": True},     # 秒時間戳
            {"input": "invalid-date", "should_succeed": False},
            {"input": "", "should_succeed": False},
            {"input": "25-06-2024", "should_succeed": False},  # 不支持的格式
        ]
        
        for test_case in test_cases:
            result = self.reminder._parse_date(test_case["input"])
            
            if test_case["should_succeed"]:
                self.assertIsNotNone(result, f"日期解析失敗: {test_case['input']}")
                print(f"  ✓ {test_case['input']} -> {result}")
            else:
                self.assertIsNone(result, f"日期解析不應該成功: {test_case['input']}")
                print(f"  ✓ {test_case['input']} -> None (預期)")
        
        print("✓ 日期解析測試通過")
        return True
    
    def test_10_comprehensive_test(self):
        """測試10: 綜合測試 - 所有邊界案例"""
        print("\n" + "="*60)
        print("測試10: 綜合測試 - 所有邊界案例")
        print("="*60)
        
        mock_tasks = [
            # 正常D-1任務
            {
                "record_id": "rec001",
                "fields": {
                    "任務標題": "正常任務1",
                    "負責人": [{"id": "ou_123456", "name": "張三"}],
                    "預計完成日期": (self.now_hkt + timedelta(days=1)).strftime('%Y-%m-%d'),
                    "任務狀態": "進行中",
                    "文檔連結": "https://example.com/doc1"
                }
            },
            # 已完成任務
            {
                "record_id": "rec002",
                "fields": {
                    "任務標題": "已完成任務",
                    "負責人": [{"id": "ou_234567", "name": "李四"}],
                    "預計完成日期": (self.now_hkt + timedelta(days=1)).strftime('%Y-%m-%d'),
                    "任務狀態": "已完成",
                    "文檔連結": "https://example.com/doc2"
                }
            },
            # 缺少日期
            {
                "record_id": "rec003",
                "fields": {
                    "任務標題": "缺少日期任務",
                    "負責人": [{"id": "ou_345678", "name": "王五"}],
                    "預計完成日期": "",
                    "任務狀態": "進行中",
                    "文檔連結": "https://example.com/doc3"
                }
            },
            # 缺少負責人
            {
                "record_id": "rec004",
                "fields": {
                    "任務標題": "缺少負責人任務",
                    "負責人": [],
                    "預計完成日期": (self.now_hkt + timedelta(days=1)).strftime('%Y-%m-%d'),
                    "任務狀態": "進行中",
                    "文檔連結": "https://example.com/doc4"
                }
            },
            # 日期不是D-1
            {
                "record_id": "rec005",
                "fields": {
                    "任務標題": "未來任務",
                    "負責人": [{"id": "ou_456789", "name": "趙六"}],
                    "預計完成日期": (self.now_hkt + timedelta(days=3)).strftime('%Y-%m-%d'),
                    "任務狀態": "進行中",
                    "文檔連結": "https://example.com/doc5"
                }
            }
        ]
        
        self.reminder._call_lark_api.side_effect = [
            {"success": True, "data": {"items": []}},
            {"success": True, "data": {"items": mock_tasks}}
        ]
        
        # 設置部分成功部分失敗
        def side_effect_send_whatsapp(message, task_id):
            if task_id == "rec001":
                return {
                    "success": True,
                    "message_id": "om_123456",
                    "chat_id": "test_chat_id",
                    "sent_at": datetime.now(self.hkt).isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": "發送失敗",
                    "traceback": "錯誤堆棧"
                }
        
        self.reminder._send_whatsapp_message.side_effect = side_effect_send_whatsapp
        
        result = self.reminder.process_tasks()
        
        # 驗證綜合結果
        self.assertEqual(result["summary"]["total_tasks"], 5)
        self.assertEqual(result["summary"]["d_minus_one_tasks"], 1)
        self.assertEqual(result["summary"]["sent_success"], 1)
        self.assertEqual(result["summary"]["skipped"], 3)
        
        # 檢查跳過原因統計
        skipped_reasons = result["summary"]["skipped_reasons"]
        self.assertEqual(skipped_reasons.get("status_completed", 0), 1)
        self.assertEqual(skipped_reasons.get("missing_due_date", 0), 1)
        self.assertEqual(skipped_reasons.get("missing_owner", 0), 1)
        
        print("✓ 綜合測試通過")
        print(f"  總任務: {result['summary']['total_tasks']}")
        print(f"  D-1任務: {result['summary']['d_minus_one_tasks']}")
        print(f"  成功發送: {result['summary']['sent_success']}")
        print(f"  跳過任務: {result['summary']['skipped']}")
        
        return result

def run_all_tests():
    """運行所有測試"""
    print("\n" + "="*60)
    print("開始運行Lark任務提醒測試套件")
    print("="*60)
    
    # 創建測試套件
    suite = unittest.TestSuite()
    
    # 添加測試用例
    test_cases = [
        TestLarkTaskReminder("test_01_normal_case_d_minus_one_task"),
        TestLarkTaskReminder("test_02_no_d_minus_one_tasks"),
        TestLarkTaskReminder("test_03_task_completed_or_cancelled"),
        TestLarkTaskReminder("test_04_missing_due_date"),
        TestLarkTaskReminder("test_05_missing_owner"),
        TestLarkTaskReminder("test_06_lark_api_failure"),
        TestLarkTaskReminder("test_07_whatsapp_send_failure"),
        TestLarkTaskReminder("test_08_timezone_boundary"),
        TestLarkTaskReminder("test_09_date_parsing"),
        TestLarkTaskReminder("test_10_comprehensive_test"),
    ]
    
    for test_case in test_cases:
        suite.addTest(test_case)
    
    # 運行測試
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 輸出測試摘要
    print("\n" + "="*60)
    print("測試套件執行完成")
    print("="*60)
    print(f"總測試數: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失敗: {len(result.failures)}")
    print(f"錯誤: {len(result.errors)}")
    
    if result.failures:
        print("\n失敗的測試:")
        for test, traceback in result.failures:
            print(f"  - {test}")
    
    if result.errors:
        print("\n錯誤的測試:")
        for test, traceback in result.errors:
            print(f"  - {test}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    # 運行所有測試
    success = run_all_tests()
    
    # 退出碼
    sys.exit(0 if success else 1)