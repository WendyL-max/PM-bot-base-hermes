#!/usr/bin/env python3
"""
WhatsApp-Lark Bridge 健康檢查腳本
用於監控服務狀態和自動恢復
"""

import os
import sys
import time
import json
import logging
import requests
import sqlite3
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/whatsapp-lark-bridge/logs/health_check.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HealthChecker:
    """健康檢查器"""
    
    def __init__(self, config_path: str = '/opt/whatsapp-lark-bridge/.env'):
        self.config_path = config_path
        self.config = self.load_config()
        self.app_url = f"http://localhost:{self.config.get('APP_PORT', 5000)}"
        
    def load_config(self) -> Dict:
        """加載配置文件"""
        config = {}
        try:
            with open(self.config_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            config[key.strip()] = value.strip().strip('"\'')
        except FileNotFoundError:
            logger.error(f"配置文件不存在: {self.config_path}")
        return config
    
    def check_service_status(self) -> Tuple[bool, str]:
        """檢查服務狀態"""
        try:
            response = requests.get(f"{self.app_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'healthy':
                    return True, "服務正常運行"
                else:
                    return False, f"服務狀態異常: {data}"
            else:
                return False, f"HTTP 錯誤: {response.status_code}"
        except requests.exceptions.RequestException as e:
            return False, f"連接失敗: {str(e)}"
    
    def check_database(self) -> Tuple[bool, str]:
        """檢查數據庫連接"""
        db_path = self.config.get('DATABASE_URL', '').replace('sqlite:///', '')
        if not db_path:
            db_path = '/opt/whatsapp-lark-bridge/app.db'
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 檢查表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            # 檢查數據完整性
            cursor.execute("SELECT COUNT(*) FROM users;")
            user_count = cursor.fetchone()[0]
            
            conn.close()
            
            return True, f"數據庫正常，{len(tables)} 張表，{user_count} 個用戶"
        except Exception as e:
            return False, f"數據庫錯誤: {str(e)}"
    
    def check_redis(self) -> Optional[Tuple[bool, str]]:
        """檢查 Redis 連接"""
        redis_url = self.config.get('REDIS_URL')
        if not redis_url:
            return None
        
        try:
            import redis
            from urllib.parse import urlparse
            
            parsed = urlparse(redis_url)
            host = parsed.hostname or 'localhost'
            port = parsed.port or 6379
            password = parsed.password
            
            r = redis.Redis(
                host=host,
                port=port,
                password=password,
                decode_responses=True
            )
            
            # 測試連接
            r.ping()
            
            # 檢查內存使用
            info = r.info()
            used_memory = info.get('used_memory_human', 'N/A')
            connected_clients = info.get('connected_clients', 0)
            
            return True, f"Redis 正常，內存使用: {used_memory}, 連接數: {connected_clients}"
        except Exception as e:
            return False, f"Redis 錯誤: {str(e)}"
    
    def check_disk_space(self) -> Tuple[bool, str]:
        """檢查磁盤空間"""
        try:
            import shutil
            
            total, used, free = shutil.disk_usage('/')
            free_gb = free / (1024**3)
            free_percent = (free / total) * 100
            
            if free_gb < — 5 or free_percent < 10:
                return False, f"磁盤空間不足: {free_gb:.1f}GB ({free_percent:.1f}%)"
            else:
                return True, f"磁盤空間充足: {free_gb:.1f}GB ({free_percent:.1f}%)"
        except Exception as e:
            return False, f"磁盤檢查錯誤: {str(e)}"
    
    def check_memory_usage(self) -> Tuple[bool, str]:
        """檢查內存使用"""
        try:
            import psutil
            
            memory = psutil.virtual_memory()
            used_percent = memory.percent
            available_gb = memory.available / (1024**3)
            
            if used_percent > 90:
                return False, f"內存使用過高: {used_percent}% ({available_gb:.1f}GB 可用)"
            else:
                return True, f"內存使用正常: {used_percent}% ({available_gb:.1f}GB 可用)"
        except Exception as e:
            return False, f"內存檢查錯誤: {str(e)}"
    
    def check_processes(self) -> Tuple[bool, str]:
        """檢查相關進程"""
        processes = [
            'gunicorn',
            'nginx',
            'redis-server',
            'supervisord'
        ]
        
        running = []
        missing = []
        
        for proc in processes:
            try:
                result = subprocess.run(
                    ['pgrep', '-f', proc],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    running.append(proc)
                else:
                    missing.append(proc)
            except Exception:
                missing.append(proc)
        
        if missing:
            return False, f"缺失進程: {', '.join(missing)}"
        else:
            return True, f"所有進程正常運行: {', '.join(running)}"
    
    def check_log_errors(self) -> Tuple[bool, str]:
        """檢查日誌錯誤"""
        log_files = [
            '/opt/whatsapp-lark-bridge/logs/error.log',
            '/opt/whatsapp-lark-bridge/logs/app.log'
        ]
        
        recent_errors = []
        cutoff_time = datetime.now() - timedelta(hours=1)
        
        for log_file in log_files:
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r') as f:
                        for line in f:
                            if 'ERROR' in line or 'CRITICAL' in line:
                                # 提取時間戳（簡單實現）
                                try:
                                    log_time_str = line.split()[0]
                                    log_time = datetime.strptime(log_time_str, '%Y-%m-%d')
                                    if log_time > cutoff_time:
                                        recent_errors.append(line.strip())
                                except:
                                    # 如果解析失敗，假設是最近錯誤
                                    recent_errors.append(line.strip())
                except Exception as e:
                    logger.error(f"讀取日誌文件失敗 {log_file}: {e}")
        
        if recent_errors:
            error_count = len(recent_errors)
            sample = recent_errors[-3:]  # 最近3個錯誤
            return False, f"最近1小時發現 {error_count} 個錯誤，示例: {sample}"
        else:
            return True, "最近1小時無錯誤"
    
    def check_external_apis(self) -> Tuple[bool, str]:
        """檢查外部 API 連接"""
        apis = [
            ('Lark API', 'https://open.feishu.cn/open-apis'),
            ('WhatsApp API', 'https://graph.facebook.com/v18.0')
        ]
        
        results = []
        for name, url in apis:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code < 500:
                    results.append(f"{name}: 正常")
                else:
                    results.append(f"{name}: HTTP {response.status_code}")
            except requests.exceptions.RequestException as e:
                results.append(f"{name}: 連接失敗 - {str(e)}")
        
        return True, "; ".join(results)
    
    def run_all_checks(self) -> Dict:
        """運行所有檢查"""
        checks = [
            ('服務狀態', self.check_service_status),
            ('數據庫', self.check_database),
            ('Redis', self.check_redis),
            ('磁盤空間', self.check_disk_space),
            ('內存使用', self.check_memory_usage),
            ('進程狀態', self.check_processes),
            ('日誌錯誤', self.check_log_errors),
            ('外部API', self.check_external_apis)
        ]
        
        results = []
        all_healthy = True
        
        for name, check_func in checks:
            start_time = time.time()
            try:
                result = check_func()
                if result is None:
                    status = 'skipped'
                    message = '未配置'
                    healthy = True
                else:
                    healthy, message = result
                    status = 'healthy' if healthy else 'unhealthy'
                    if not healthy:
                        all_healthy = False
            except Exception as e:
                status = 'error'
                message = f"檢查異常: {str(e)}"
                healthy = False
                all_healthy = False
            
            duration = time.time() - start_time
            
            results.append({
                'name': name,
                'status': status,
                'healthy': healthy,
                'message': message,
                'duration': round(duration,构成句子
                 
                # 檢查是否需要自動恢復
                if not healthy and name in ['服務狀態', '進程狀態']:
                    self.attempt_recovery(name, message)
            
            logger.info(f"{name}: {status} - {message} ({duration:.2f}s)")
        
        return {
            'timestamp': datetime.now().isoformat(),
            'overall_healthy': all_healthy,
            'checks': results
        }
    
    def attempt_recovery(self, component: str, error_message: str):
        """嘗試自動恢復"""
        logger.warning(f"嘗試恢復 {component}: {error_message}")
        
        recovery_actions = {
            '服務狀態': self.restart_service,
            '進程狀態': self.restart_processes,
            '數據庫': self.repair_database
        }
        
        if component in recovery_actions:
            try:
                success, message = recovery_actions[component]()
                if success:
                    logger.info(f"{component} 恢復成功: {message}")
                else:
                    logger.error(f"{component} 恢復失敗: {message}")
            except Exception as e:
                logger.error(f"{component} 恢復異常: {str(e)}")
    
    def restart_service(self) -> Tuple[bool, str]:
        """重啟服務"""
        try:
            subprocess.run(['supervisorctl', 'restart', 'whatsapp-lark-bridge'], 
                          check=True, capture_output=True, text=True)
            time.sleep(5)  # 等待服務啟動
            
            # 驗證重啟是否成功
            healthy, message = self.check_service_status()
            if healthy:
                return True, "服務重啟成功"
            else:
                return False, f"服務重啟後仍然異常: {message}"
        except subprocess.CalledProcessError as e:
            return False, f"重啟命令失敗: {e.stderr}"
    
    def restart_processes(self) -> Tuple[bool, str]:
        """重啟相關進程"""
        processes = ['nginx', 'redis-server', 'supervisord']
        results = []
        
        for proc in processes:
            try:
                subprocess.run(['systemctl', 'restart', proc], 
                              check=True, capture_output=True, text=True)
                results.append(f"{proc}: 重啟成功")
            except subprocess.CalledProcessError as e:
                results.append(f"{proc}: 重啟失敗 - {e.stderr}")
        
        return True, "; ".join(results)
    
    def repair_database(self) -> Tuple[bool, str]:
        """修復數據庫"""
        db_path = self.config.get('DATABASE_URL', '').replace('sqlite:///', '')
        if not db_path:
            db_path = '/opt/whatsapp-lark-bridge/app.db'
        
        try:
            # 備份數據庫
            backup_path = f"{db_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            import shutil
            shutil.copy2(db_path, backup_path)
            
            # 嘗試修復
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 檢查並修復表
            cursor.execute("PRAGMA integrity_check;")
            integrity_result = cursor.fetchone()[0]
            
            if integrity_result == 'ok':
                return True, "數據庫完整性檢查通過"
            else:
                # 嘗試重建索引
                cursor.execute("REINDEX;")
                conn.commit()
                return True, f"數據庫已重建索引，原檢查結果: {integrity_result}"
        except Exception as e:
            return False, f"數據庫修復失敗: {str(e)}"
    
    def generate_report(self, results: Dict) -> str:
        """生成報告"""
        report = []
        report.append("=" * - 60)
        report.append(f"WhatsApp-Lark Bridge 健康檢查報告")
        report.append(f"時間: {results['timestamp']}")
        report.append(f"總體狀態: {'健康' if results['overall_healthy'] else '異常'}")
        report.append("=" * 60)
        
        for check in results['checks']:
            status_icon = '✅' if check['healthy'] else '❌'
            if check['status'] == 'skipped':
                status_icon = '⚠️'
            report.append(f"{status_icon} {check['name']}: {check['message']} ({check['duration']}s)")
        
        report.append("=" * 60)
        return "\n".join(report)
    
    def save_results(self, results: Dict):
        """保存檢查結果"""
        try:
            results_dir = '/opt/whatsapp-lark-bridge/health_results'
            os.makedirs(results_dir, exist_ok=True)
            
            filename = f"health_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(results_dir, filename)
            
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            # 保留最近30天的結果
            cutoff = datetime.now() - timedelta(days=30)
            for old_file in os.listdir(results_dir):
                old_path = os.path.join(results_dir, old_file)
                if os.path.isfile(old_path):
                    file_time = datetime.fromtimestamp(os.path.getmtime(old_path))
                    if file_time < cutoff:
                        os.remove(old_path)
        except Exception as e:
            logger.error(f"保存檢查結果失敗: {str(e)}")

def main():
    """主函數"""
    # 解析命令行參數
    import argparse
    parser = argparse.ArgumentParser(description='WhatsApp-Lark Bridge 健康檢查')
    parser.add_argument('--config', default='/opt/whatsapp-lark-bridge/.env',
                       help='配置文件路徑')
    parser.add_argument('--interval', type=int, default=300,
                       help='檢查間隔（秒），0表示只運行一次')
    parser.add_argument('--alert', action='store_true',
                       help='啟用警報通知')
    parser.add_argument('--verbose', action='store_true',
                       help='詳細輸出')
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    checker = HealthChecker(args.config)
    
    if args.interval == 0:
        # 單次運行
        results = checker.run_all_checks()
        report = checker.generate_report(results)
        print(report)
        checker.save_results(results)
    else:
        # 定時運行
        logger.info(f"啟動健康檢查，間隔: {args.interval}秒")
        try:
            while True:
                results = checker.run_all_checks()
                report = checker.generate_report(results)
                
                if args.verbose or not results['overall_healthy']:
                    print(report)
                
                checker.save_results(results)
                
                # 如果需要警報且狀態異常
                if args.alert and not results['overall_healthy']:
                    checker.send_alert(results)
                
                time.sleep(args.interval)
        except KeyboardInterrupt:
            logger.info("健康檢查已停止")

if __name__ == '__main__':
    main()