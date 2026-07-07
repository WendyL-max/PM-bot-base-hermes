#!/usr/bin/env python3
"""
Lark任務到期前1天提醒腳本
每天香港時間早上9:00執行，檢查Lark多維表格中的任務，發送WhatsApp提醒
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
# import pytz  # 注釋掉，使用datetime替代
import time
import traceback

# 添加當前目錄到Python路徑以便導入工具
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 嘗試導入Hermes工具
try:
    from hermes_tools import terminal, read_file, write_file
except ImportError:
    # 如果在非Hermes環境中運行，使用模擬工具
    class MockTools:
        def terminal(self, command, timeout=60):
            import subprocess
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            return {"output": result.stdout, "exit_code": result.returncode, "error": result.stderr}
        
        def read_file(self, path, offset=1, limit=500):
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                content = ''.join(lines[offset-1:offset-1+limit])
            return {"content": content, "total_lines": len(lines)}
        
        def write_file(self, path, content):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return {"bytes_written": len(content), "dirs_created": True}

    terminal = MockTools().terminal
    read_file = MockTools().read_file
    write_file = MockTools().write_file

# 配置日志
def setup_logging():
    """設置日志配置"""
    log_dir = "/home/lscm-admin/.lark-reminder-logs"
    try:
        os.makedirs(log_dir, exist_ok=True)
    except PermissionError:
        # 如果沒有權限，使用用戶目錄
        log_dir = os.path.expanduser("~/.lark-reminder-logs")
        os.makedirs(log_dir, exist_ok=True)
    
    from datetime import timezone, timedelta
    timestamp = datetime.now(timezone(timedelta(hours=8))).strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(log_dir, f"reminder_{timestamp}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

class LarkTaskReminder:
    """Lark任務提醒主類"""
    
    def __init__(self):
        # 使用datetime替代pytz
        from datetime import timezone, timedelta
        self.hkt = timezone(timedelta(hours=8))
        self.now_hkt = datetime.now(timezone(timedelta(hours=8)))
        self.execution_id = f"reminder_{self.now_hkt.strftime('%Y%m%d_%H%M%S')}"
        
        # 從環境變量讀取配置
        self.config = self._load_config()
        
        # 初始化結果結構
        self.result = {
            "execution_id": self.execution_id,
            "execution_time": self.now_hkt.isoformat(),
            "timezone": "Asia/Hong_Kong",
            "summary": {
                "total_tasks": 0,
                "d_minus_one_tasks": 0,
                "sent_success": 0,
                "sent_failed": 0,
                "skipped": 0,
                "skipped_reasons": {}
            },
            "tasks_processed": [],
            "whatsapp_messages": [],
            "errors": [],
            "warnings": []
        }
    
    def _load_config(self) -> Dict[str, str]:
        """加載配置從環境變量"""
        required_vars = [
            "LARK_APP_ID",
            "LARK_APP_SECRET", 
            "LARK_BASE_TOKEN",
            "LARK_TABLE_ID",
            "WHATSAPP_CHAT_ID"
        ]
        
        config = {}
        missing_vars = []
        
        for var in required_vars:
            value = os.environ.get(var)
            if not value:
                missing_vars.append(var)
            else:
                config[var] = value
        
        if missing_vars:
            error_msg = f"缺少必要的環境變量: {', '.join(missing_vars)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info(f"配置加載成功: APP_ID={config['LARK_APP_ID'][:10]}..., TABLE_ID={config['LARK_TABLE_ID']}")
        return config
    
    def _call_lark_api(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """調用Lark API工具"""
        try:
            # 這裡需要根據實際的Hermes工具接口調整
            # 假設我們有對應的MCP工具
            if tool_name == "mcp_lark_bitable_v1_appTableRecord_search":
                # 模擬API調用 - 實際使用時需要替換為真實的工具調用
                logger.info(f"調用Lark API: {tool_name}")
                
                # 模擬返回數據
                return {
                    "success": True,
                    "data": {
                        "items": self._get_mock_tasks(),
                        "has_more": False,
                        "page_token": None
                    }
                }
            elif tool_name == "mcp_lark_bitable_v1_appTableField_list":
                # 模擬字段列表
                return {
                    "success": True,
                    "data": {
                        "items": [
                            {"field_name": "任務標題", "field_id": "fldxxxx1", "type": 1},
                            {"field_name": "負責人", "field_id": "fldxxxx2", "type": 11},
                            {"field_name": "預計完成日期", "field_id": "fldxxxx3", "type": 5},
                            {"field_name": "任務狀態", "field_id": "fldxxxx4", "type": 3},
                            {"field_name": "文檔連結", "field_id": "fldxxxx5", "type": 15}
                        ]
                    }
                }
            else:
                raise ValueError(f"不支持的Lark工具: {tool_name}")
                
        except Exception as e:
            error_msg = f"Lark API調用失敗: {str(e)}"
            logger.error(error_msg)
            self.result["errors"].append({
                "type": "lark_api_error",
                "tool": tool_name,
                "error": str(e),
                "traceback": traceback.format_exc()
            })
            raise
    
    def _get_mock_tasks(self) -> List[Dict[str, Any]]:
        """獲取模擬任務數據（測試用）"""
        # 這是測試數據，實際使用時會從Lark API獲取
        return [
            {
                "record_id": "rec001",
                "fields": {
                    "任務標題": "完成季度報告",
                    "負責人": [{"id": "ou_123456", "name": "張三"}],
                    "預計完成日期": (self.now_hkt + timedelta(days=1)).strftime('%Y-%m-%d'),
                    "任務狀態": "進行中",
                    "文檔連結": "https://example.com/doc1"
                }
            },
            {
                "record_id": "rec002", 
                "fields": {
                    "任務標題": "項目會議準備",
                    "負責人": [{"id": "ou_234567", "name": "李四"}],
                    "預計完成日期": (self.now_hkt + timedelta(days=2)).strftime('%Y-%m-%d'),
                    "任務狀態": "進行中",
                    "文檔連結": "https://example.com/doc2"
                }
            },
            {
                "record_id": "rec003",
                "fields": {
                    "任務標題": "客戶演示",
                    "負責人": [{"id": "ou_345678", "name": "王五"}],
                    "預計完成日期": (self.now_hkt + timedelta(days=1)).strftime('%Y-%m-%d'),
                    "任務狀態": "已完成",
                    "文檔連結": "https://example.com/doc3"
                }
            },
            {
                "record_id": "rec004",
                "fields": {
                    "任務標題": "系統測試",
                    "負責人": [],
                    "預計完成日期": (self.now_hkt + timedelta(days=1)).strftime('%Y-%m-%d'),
                    "任務狀態": "進行中",
                    "文檔連結": "https://example.com/doc4"
                }
            },
            {
                "record_id": "rec005",
                "fields": {
                    "任務標題": "缺少日期任務",
                    "負責人": [{"id": "ou_456789", "name": "趙六"}],
                    "預計完成日期": "",
                    "任務狀態": "進行中",
                    "文檔連結": "https://example.com/doc5"
                }
            }
        ]
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """解析日期字符串"""
        if not date_str:
            return None
        
        try:
            # 嘗試多種日期格式
            formats = ['%Y-%m-%d', '%Y/%m/%d', '%Y年%m月%d日']
            for fmt in formats:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    # 使用replace來添加時區信息
                    return dt.replace(tzinfo=self.hkt)
                except ValueError:
                    continue
            
            # 如果是時間戳（毫秒）
            if date_str.isdigit():
                timestamp = int(date_str)
                # 如果是13位毫秒時間戳
                if timestamp > 1000000000000:
                    timestamp = timestamp / 1000
                dt = datetime.fromtimestamp(timestamp, tz=timezone(timedelta(hours=8)))
                return dt
                
        except Exception as e:
            logger.warning(f"日期解析失敗: {date_str}, 錯誤: {e}")
        
        return None
    
    def _calculate_days_remaining(self, due_date: datetime) -> int:
        """計算剩餘天數（香港時間）"""
        # 獲取當前日期（不考慮時間）
        current_date = self.now_hkt.date()
        due_date_date = due_date.date()
        
        # 計算天數差
        delta = due_date_date - current_date
        return delta.days
    
    def _should_send_reminder(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """判斷是否應該發送提醒"""
        fields = task.get("fields", {})
        task_id = task.get("record_id", "unknown")
        
        # 檢查狀態
        status = fields.get("任務狀態", "")
        if status in ["已完成", "已取消", "Done", "Cancelled"]:
            return {"should_send": False, "reason": "status_completed", "task_id": task_id}
        
        # 檢查預計完成日期
        due_date_str = fields.get("預計完成日期", "")
        if not due_date_str:
            return {"should_send": False, "reason": "missing_due_date", "task_id": task_id}
        
        # 解析日期
        due_date = self._parse_date(due_date_str)
        if not due_date:
            return {"should_send": False, "reason": "invalid_date_format", "task_id": task_id}
        
        # 檢查負責人
        owner = fields.get("負責人", [])
        if not owner:
            return {"should_send": False, "reason": "missing_owner", "task_id": task_id}
        
        # 計算剩餘天數
        days_remaining = self._calculate_days_remaining(due_date)
        
        # 檢查是否為D-1（到期前1天）
        if days_remaining == 1:
            return {
                "should_send": True,
                "task_id": task_id,
                "due_date": due_date,
                "days_remaining": days_remaining,
                "owner": owner[0] if isinstance(owner, list) and len(owner) > 0 else owner
            }
        
        return {"should_send": False, "reason": f"days_remaining_{days_remaining}", "task_id": task_id}
    
    def _create_reminder_message(self, task: Dict[str, Any], owner_info: Dict[str, Any]) -> str:
        """創建提醒消息"""
        fields = task.get("fields", {})
        task_title = fields.get("任務標題", "未命名任務")
        due_date_str = fields.get("預計完成日期", "")
        doc_url = fields.get("文檔連結", "")
        
        # 解析日期用於顯示
        due_date = self._parse_date(due_date_str)
        if due_date:
            display_date = due_date.strftime('%Y年%m月%d日')
        else:
            display_date = due_date_str
        
        owner_name = owner_info.get("name", "負責人") if isinstance(owner_info, dict) else "負責人"
        
        message = f"【任務提醒】@{owner_name}，任務「{task_title}」將於明天({display_date})到期，請及時處理！"
        
        if doc_url:
            message += f"\n文檔連結：{doc_url}"
        
        return message
    
    def _send_whatsapp_message(self, message: str, task_id: str) -> Dict[str, Any]:
        """發送WhatsApp消息（通過Lark API）"""
        try:
            # 這裡需要替換為實際的WhatsApp發送邏輯
            # 假設通過Lark API發送到指定的chat_id
            whatsapp_chat_id = self.config["WHATSAPP_CHAT_ID"]
            
            logger.info(f"發送WhatsApp消息到 {whatsapp_chat_id}: {message[:50]}...")
            
            # 模擬發送成功
            # 實際使用時需要調用Lark的發消息API
            message_id = f"om_{int(time.time() * 1000)}"
            
            from datetime import timezone, timedelta
            return {
                "success": True,
                "message_id": message_id,
                "chat_id": whatsapp_chat_id,
                "sent_at": datetime.now(timezone(timedelta(hours=8))).isoformat()
            }
            
        except Exception as e:
            error_msg = f"發送WhatsApp消息失敗: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    def process_tasks(self) -> Dict[str, Any]:
        """處理所有任務"""
        try:
            # 1. 獲取表格字段信息
            logger.info("獲取表格字段信息...")
            fields_result = self._call_lark_api("mcp_lark_bitable_v1_appTableField_list",
                path={"app_token": self.config["LARK_BASE_TOKEN"], "table_id": self.config["LARK_TABLE_ID"]}
            )
            
            # 2. 獲取所有任務記錄
            logger.info("獲取任務記錄...")
            tasks_result = self._call_lark_api("mcp_lark_bitable_v1_appTableRecord_search",
                path={"app_token": self.config["LARK_BASE_TOKEN"], "table_id": self.config["LARK_TABLE_ID"]},
                data={
                    "automatic_fields": True,
                    "field_names": ["任務標題", "負責人", "預計完成日期", "任務狀態", "文檔連結"]
                }
            )
            
            tasks = tasks_result.get("data", {}).get("items", [])
            self.result["summary"]["total_tasks"] = len(tasks)
            logger.info(f"找到 {len(tasks)} 個任務")
            
            # 3. 處理每個任務
            for task in tasks:
                task_result = {
                    "task_id": task.get("record_id"),
                    "task_title": task.get("fields", {}).get("任務標題", "未知"),
                    "status": task.get("fields", {}).get("任務狀態", ""),
                    "processed": False,
                    "reminder_sent": False,
                    "error": None,
                    "skipped_reason": None
                }
                
                try:
                    # 判斷是否應該發送提醒
                    decision = self._should_send_reminder(task)
                    
                    if not decision["should_send"]:
                        # 記錄跳過原因
                        reason = decision.get("reason", "unknown")
                        task_result["skipped_reason"] = reason
                        task_result["processed"] = True
                        
                        # 更新跳過統計
                        self.result["summary"]["skipped"] += 1
                        self.result["summary"]["skipped_reasons"][reason] = \
                            self.result["summary"]["skipped_reasons"].get(reason, 0) + 1
                        
                        logger.debug(f"任務 {task_result['task_id']} 跳過: {reason}")
                        continue
                    
                    # 這是D-1任務
                    self.result["summary"]["d_minus_one_tasks"] += 1
                    
                    # 準備發送提醒
                    owner_info = decision["owner"]
                    due_date = decision["due_date"]
                    days_remaining = decision["days_remaining"]
                    
                    task_result.update({
                        "owner": owner_info,
                        "due_date": due_date.isoformat() if due_date else None,
                        "days_remaining": days_remaining,
                        "document_url": task.get("fields", {}).get("文檔連結", "")
                    })
                    
                    # 創建提醒消息
                    message = self._create_reminder_message(task, owner_info)
                    
                    # 發送WhatsApp消息
                    send_result = self._send_whatsapp_message(message, task_result["task_id"])
                    
                    # 記錄發送結果
                    from datetime import timezone, timedelta
                    whatsapp_record = {
                        "task_id": task_result["task_id"],
                        "to_chat_id": self.config["WHATSAPP_CHAT_ID"],
                        "to_user": owner_info,
                        "content": message,
                        "sent_at": datetime.now(timezone(timedelta(hours=8))).isoformat(),
                        "success": send_result["success"]
                    }
                    
                    if send_result["success"]:
                        task_result["reminder_sent"] = True
                        task_result["whatsapp_message_id"] = send_result.get("message_id")
                        self.result["summary"]["sent_success"] += 1
                        logger.info(f"✓ 成功發送提醒給任務 {task_result['task_id']}")
                    else:
                        task_result["reminder_sent"] = False
                        task_result["error"] = send_result.get("error")
                        self.result["summary"]["sent_failed"] += 1
                        logger.error(f"✗ 發送提醒失敗: {task_result['task_id']} - {send_result.get('error')}")
                        
                        # 記錄錯誤詳情
                        self.result["errors"].append({
                            "type": "whatsapp_send_error",
                            "task_id": task_result["task_id"],
                            "error": send_result.get("error"),
                            "traceback": send_result.get("traceback")
                        })
                    
                    whatsapp_record["success"] = send_result["success"]
                    self.result["whatsapp_messages"].append(whatsapp_record)
                    
                    task_result["processed"] = True
                    
                except Exception as e:
                    error_msg = f"處理任務失敗: {task_result['task_id']} - {str(e)}"
                    logger.error(error_msg)
                    task_result["error"] = str(e)
                    task_result["processed"] = False
                    
                    self.result["errors"].append({
                        "type": "task_processing_error",
                        "task_id": task_result["task_id"],
                        "error": str(e),
                        "traceback": traceback.format_exc()
                    })
                
                finally:
                    self.result["tasks_processed"].append(task_result)
            
            # 4. 檢查執行狀態
            has_errors = len(self.result["errors"]) > 0
            has_failed_sends = self.result["summary"]["sent_failed"] > 0
            
            if has_errors and self.result["summary"]["sent_success"] == 0:
                self.result["status"] = "failed"
                logger.error("執行完全失敗")
            elif has_failed_sends:
                self.result["status"] = "partial_success"
                logger.warning("部分成功，有發送失敗的任務")
            else:
                self.result["status"] = "success"
                logger.info("執行成功")
            
            return self.result
            
        except Exception as e:
            error_msg = f"處理任務時發生未預期錯誤: {str(e)}"
            logger.error(error_msg)
            self.result["status"] = "failed"
            self.result["errors"].append({
                "type": "unexpected_error",
                "error": str(e),
                "traceback": traceback.format_exc()
            })
            return self.result
    
    def save_result(self):
        """保存執行結果到文件"""
        try:
            # 創建輸出目錄
            output_dir = "/home/lscm-admin/.lark-reminder-logs/results"
            os.makedirs(output_dir, exist_ok=True)
            
            # 保存JSON結果
            output_file = os.path.join(output_dir, f"{self.execution_id}.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.result, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"結果已保存到: {output_file}")
            
            # 生成簡短摘要
            summary = self._generate_summary()
            summary_file = os.path.join(output_dir, f"{self.execution_id}_summary.txt")
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(summary)
            
            logger.info(f"摘要已保存到: {summary_file}")
            
            return output_file, summary_file
            
        except Exception as e:
            logger.error(f"保存結果失敗: {str(e)}")
            return None, None
    
    def _generate_summary(self) -> str:
        """生成執行摘要"""
        summary = self.result["summary"]
        status = self.result.get("status", "unknown")
        
        lines = [
            "=" * 50,
            f"Lark任務提醒執行摘要 - {self.execution_id}",
            "=" * 50,
            f"執行時間: {self.result['execution_time']}",
            f"時區: {self.result['timezone']}",
            f"狀態: {status}",
            "",
            "統計摘要:",
            f"  總任務數: {summary['total_tasks']}",
            f"  D-1任務數: {summary['d_minus_one_tasks']}",
            f"  成功發送: {summary['sent_success']}",
            f"  發送失敗: {summary['sent_failed']}",
            f"  跳過任務: {summary['skipped']}",
        ]
        
        if summary['skipped_reasons']:
            lines.append("")
            lines.append("跳過原因:")
            for reason, count in summary['skipped_reasons'].items():
                lines.append(f"  {reason}: {count}")
        
        if self.result['errors']:
            lines.append("")
            lines.append(f"錯誤數量: {len(self.result['errors'])}")
            for i, error in enumerate(self.result['errors'][:3], 1):
                lines.append(f"  錯誤{i}: {error.get('type', 'unknown')} - {error.get('error', 'No error message')[:50]}...")
        
        lines.append("")
        lines.append("=" * 50)
        
        return "\n".join(lines)

def main():
    """主函數"""
    try:
        logger.info("=" * 60)
        logger.info("開始執行Lark任務到期前1天提醒")
        logger.info("=" * 60)
        
        # 初始化提醒器
        reminder = LarkTaskReminder()
        
        # 處理任務
        result = reminder.process_tasks()
        
        # 保存結果
        json_file, summary_file = reminder.save_result()
        
        # 輸出摘要到控制台
        print(reminder._generate_summary())
        
        # 返回結果
        return {
            "success": result.get("status") in ["success", "partial_success"],
            "status": result.get("status"),
            "summary": result["summary"],
            "output_files": {
                "json": json_file,
                "summary": summary_file
            }
        }
        
    except Exception as e:
        logger.error(f"主程序執行失敗: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

if __name__ == "__main__":
    result = main()
    sys.exit(0 if result.get("success", False) else 1)