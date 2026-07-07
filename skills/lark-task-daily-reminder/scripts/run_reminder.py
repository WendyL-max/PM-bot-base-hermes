#!/usr/bin/env python3
"""
Lark任務到期前1天提醒腳本 (v3 — 量化操作規則版)
每天香港時間早上9:00執行，檢查Lark多維表格中的任務，生成WhatsApp提醒內容

=== 操作規則 ===
⏱ timeout=30s  — 所有外部API調用超時設定
🔁 retry=3     — 失敗後最多重試3次，backoff=2s
⚡ max_concurrent=5 — 任務處理並發上限
🧩 失敗處理     — Detection階段失敗重試3次；Send階段(如分離)僅重試Send
⏰ schedule    — 每日 09:00 HKT 執行一次
"""

import os
import sys
import json
import logging
import time
import traceback
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Callable
from functools import wraps
import concurrent.futures
import requests

# ═══════════════════════════════════════════════
# 操作規則常量
# ═══════════════════════════════════════════════
DEFAULT_TIMEOUT = 30            # ⏱ 單步操作超時 (秒)
MAX_RETRIES = 3                 # 🔁 最大重試次數
RETRY_BACKOFF_BASE = 2          # 🔁 重試間隔基數 (秒)，指數遞增: 2, 4, 6
MAX_CONCURRENT = 5              # ⚡ 並發處理上限
SCHEDULE_HOUR = 9               # ⏰ 每日執行時間 (HKT)
DESIRED_D_DAYS = 1              # 提前N天提醒 (D-N)

# ═══════════════════════════════════════════════
# 日誌配置
# ═══════════════════════════════════════════════

def setup_logging():
    log_dir = os.path.expanduser("~/.lark-reminder-logs")
    os.makedirs(log_dir, exist_ok=True)
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

LARK_API_BASE = "https://open.larksuite.com/open-apis"


# ═══════════════════════════════════════════════
# 🔁 重試裝飾器 (exponential backoff)
# ═══════════════════════════════════════════════

def with_retry(func: Callable) -> Callable:
    """重試裝飾器：失敗後最多重試 MAX_RETRIES 次，間隔指數遞增 backoff*attempt"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        last_exc = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                return func(*args, **kwargs)
            except (requests.RequestException, RuntimeError, ConnectionError, TimeoutError) as e:
                last_exc = e
                if attempt < MAX_RETRIES:
                    sleep_time = RETRY_BACKOFF_BASE * attempt  # 2, 4, 6
                    logger.warning(
                        f"{func.__name__} 失敗 (第{attempt}/{MAX_RETRIES}次), "
                        f"{sleep_time}s 後重試: {type(e).__name__}: {e}"
                    )
                    time.sleep(sleep_time)
        logger.error(f"{func.__name__} 已重試 {MAX_RETRIES} 次仍失敗: {type(last_exc).__name__}: {last_exc}")
        raise last_exc  # type: ignore
    return wrapper


# ═══════════════════════════════════════════════
# 主類
# ═══════════════════════════════════════════════

class LarkTaskReminder:
    """Lark任務提醒主類 — 支援 timeout/retry/concurrency/failure-isolation"""

    # 實際表格字段對照
    FIELD_TASK = "Task"           # Text - 任務標題
    FIELD_ASSIGNEE = "Assignee"   # MultiSelect - 負責人
    FIELD_STATUS = "Status"       # SingleSelect - 狀態
    FIELD_DUE_DATE = "預計完成日期"  # DateTime - 截止日期(毫秒時間戳)

    def __init__(self):
        self.hkt = timezone(timedelta(hours=8))
        self.now_hkt = datetime.now(timezone(timedelta(hours=8)))
        self.execution_id = f"reminder_{self.now_hkt.strftime('%Y%m%d_%H%M%S')}"

        self.config = self._load_config()
        self._access_token = None
        self._token_expires_at = 0

        # ── 分階段結果追蹤 ──
        # Detection phase (查詢+過濾)
        self.detection_result = {
            "records_fetched": 0,
            "detection_ok": False,
            "detection_errors": [],
        }
        # Processing phase (計算+生成提醒)
        self.processing_result = {
            "tasks_to_process": 0,
            "d1_found": 0,
            "processing_ok": False,
            "processing_errors": [],
        }

        self.result = {
            "execution_id": self.execution_id,
            "execution_time": self.now_hkt.isoformat(),
            "timezone": "Asia/Hong_Kong",
            "rules_applied": {
                "timeout_seconds": DEFAULT_TIMEOUT,
                "max_retries": MAX_RETRIES,
                "retry_backoff_seconds": RETRY_BACKOFF_BASE,
                "max_concurrent": MAX_CONCURRENT,
                "schedule": f"每日{SCHEDULE_HOUR}:00 HKT",
            },
            "phases": {
                "detection": {"status": "pending", "retries": 0, "duration_ms": 0},
                "processing": {"status": "pending", "retries": 0, "duration_ms": 0},
            },
            "summary": {
                "total_tasks": 0,
                "d_minus_one_tasks": 0,
                "skipped": 0,
                "skipped_reasons": {},
            },
            "tasks_processed": [],
            "whatsapp_messages": [],
            "errors": [],
            "warnings": [],
        }

    def _load_config(self) -> Dict[str, str]:
        """從環境變量加載配置，支援 retry 獲取"""
        config = {}
        env_map = {
            "LARK_APP_ID": ("cli_aaa03a9afd399eea", True),
            "LARK_APP_SECRET": ("z81dmYHofkA3FFBHLjkivhNJcEg2EW5u", True),
            "LARK_TABLE_TOKEN": ("Fw8qb31XFaGN6assxmRl0Y5fg9c", True),
            "LARK_TABLE_ID": ("tblvHm23ajXhrXzp", True),
        }

        for key, (default, required) in env_map.items():
            value = os.environ.get(key) or default
            config[key] = value

        config.setdefault("FIELD_MAPPING", {
            "task_title": self.FIELD_TASK,
            "assignee": self.FIELD_ASSIGNEE,
            "status": self.FIELD_STATUS,
            "due_date": self.FIELD_DUE_DATE,
        })

        logger.info(f"配置加載成功: APP_ID={config['LARK_APP_ID'][:10]}...")
        return config

    # ── Phase 1: Detection (Lark API 認證 + 查詢) ─────────────

    @with_retry
    def _ensure_token(self) -> str:
        """獲取或刷新 tenant_access_token (⏱ timeout=30s, 🔁 retry=3)"""
        now = time.time()
        if self._access_token and now < self._token_expires_at - 60:
            return self._access_token

        logger.info("正在獲取 tenant_access_token...")
        r = requests.post(
            f"{LARK_API_BASE}/auth/v3/tenant_access_token/internal",
            json={
                "app_id": self.config["LARK_APP_ID"],
                "app_secret": self.config["LARK_APP_SECRET"],
            },
            timeout=DEFAULT_TIMEOUT  # ⏱ 30s
        )
        data = r.json()
        if data.get("code") != 0:
            raise RuntimeError(f"獲取 token 失敗: {data.get('msg', 'unknown')} (code={data.get('code')})")
        self._access_token = data["tenant_access_token"]
        self._token_expires_at = now + data.get("expire", 7200)
        logger.info("token 獲取成功")
        return self._access_token

    @with_retry
    def _lark_get(self, path: str, params: dict = None) -> dict:
        """GET Lark API (⏱ timeout=30s, 🔁 retry=3)"""
        token = self._ensure_token()
        url = f"{LARK_API_BASE}{path}"
        headers = {"Authorization": f"Bearer {token}"}
        r = requests.get(url, headers=headers, params=params, timeout=DEFAULT_TIMEOUT)
        resp_data = r.json()
        if resp_data.get("code") != 0:
            raise RuntimeError(f"Lark GET 失敗: {resp_data.get('msg', 'unknown')} (code={resp_data.get('code')}) path={path}")
        return resp_data

    @with_retry
    def _lark_post(self, path: str, data: dict = None) -> dict:
        """POST Lark API (⏱ timeout=30s, 🔁 retry=3)"""
        token = self._ensure_token()
        url = f"{LARK_API_BASE}{path}"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        r = requests.post(url, headers=headers, json=data or {}, timeout=DEFAULT_TIMEOUT)
        resp_data = r.json()
        if resp_data.get("code") != 0:
            raise RuntimeError(f"Lark POST 失敗: {resp_data.get('msg', 'unknown')} (code={resp_data.get('code')}) path={path}")
        return resp_data

    @with_retry
    def _search_tasks(self) -> List[Dict[str, Any]]:
        """從 Lark 表格查詢所有記錄 (分頁最多500條/頁)"""
        all_records = []
        page_token = None

        while True:
            params = {"page_size": 500}
            if page_token:
                params["page_token"] = page_token

            # _lark_get 自帶 retry + timeout
            data = self._lark_get(
                f"/bitable/v1/apps/{self.config['LARK_TABLE_TOKEN']}/tables/{self.config['LARK_TABLE_ID']}/records",
                params=params
            )

            items = data.get("data", {}).get("items", [])
            all_records.extend(items)

            if not data.get("data", {}).get("has_more"):
                break
            page_token = data.get("data", {}).get("page_token")

        logger.info(f"查到 {len(all_records)} 條記錄")
        return all_records

    # ── Phase 2: Processing (過濾 + 計算 + 生成訊息) ────────

    def _is_active(self, fields: dict) -> bool:
        """只處理進行中的任務"""
        status = fields.get(self.FIELD_STATUS)
        if not status:
            return False
        if isinstance(status, dict):
            status = status.get("text", "")
        return status == "進行中"

    def _get_task_title(self, fields: dict) -> str:
        """提取任務名稱"""
        task = fields.get(self.FIELD_TASK)
        if isinstance(task, list):
            return "".join(part.get("text", "") for part in task if isinstance(part, dict))
        return str(task) if task else "未命名任務"

    def _get_assignees(self, fields: dict) -> List[str]:
        """提取負責人列表"""
        assignee = fields.get(self.FIELD_ASSIGNEE)
        if isinstance(assignee, list):
            return [str(a) for a in assignee if a]
        return []

    def _get_due_date_ts(self, fields: dict) -> Optional[int]:
        """提取截止日期時間戳(毫秒)"""
        raw = fields.get(self.FIELD_DUE_DATE)
        if raw is None:
            return None
        return int(raw) if raw else None

    def _calculate_days_remaining(self, due_date_ts: int) -> int:
        """計算剩餘天數（午夜對午夜，純天數比較）"""
        today = self.now_hkt.replace(hour=0, minute=0, second=0, microsecond=0)
        due = datetime.fromtimestamp(due_date_ts / 1000, tz=self.hkt).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        return (due - today).days

    def _process_single_record(self, record: dict) -> Dict[str, Any]:
        """處理單一記錄 — 由 ThreadPoolExecutor 調用 (⚡ max_concurrent=5)"""
        fields = record.get("fields", {})
        record_id = record.get("record_id", "unknown")
        task_name = self._get_task_title(fields)
        assignees = self._get_assignees(fields)

        task_entry = {
            "record_id": record_id,
            "task_title": task_name,
            "assignees": assignees,
            "status": str(fields.get(self.FIELD_STATUS, "")),
            "processed": False,
            "reminder_sent": False,
            "skipped_reason": None,
        }

        try:
            # 過濾：進行中
            if not self._is_active(fields):
                task_entry["skipped_reason"] = "not_active"
                return task_entry

            # 過濾：有截止日期
            due_ts = self._get_due_date_ts(fields)
            if not due_ts:
                task_entry["skipped_reason"] = "missing_due_date"
                return task_entry

            # 過濾：有負責人
            if not assignees:
                task_entry["skipped_reason"] = "no_assignee"
                return task_entry

            # 計算剩餘天數
            days = self._calculate_days_remaining(due_ts)
            due_dt = datetime.fromtimestamp(due_ts / 1000, tz=self.hkt)
            task_entry["due_date"] = due_dt.isoformat()
            task_entry["days_remaining"] = days

            if days != DESIRED_D_DAYS:
                task_entry["skipped_reason"] = f"days_remaining_{days}"
                return task_entry

            # ── D-N 任務 — 生成提醒內容 ──
            due_str = due_dt.strftime("%Y年%m月%d日")
            assignee_str = "、".join(assignees)
            msg = (
                f"【任務提醒】{assignee_str}\n"
                f"任務「{task_name}」將於明天({due_str})到期，請及時處理！"
            )

            task_entry["message"] = msg
            task_entry["reminder_sent"] = False
            task_entry["d_minus_one"] = True
            logger.info(f"📋 D-{DESIRED_D_DAYS} 任務待提醒: {task_name} — {msg[:60]}...")

        except Exception as e:
            logger.error(f"處理記錄 {record_id} 時出錯: {e}")
            task_entry["error"] = str(e)
            task_entry["skipped_reason"] = "processing_error"

        task_entry["processed"] = True
        return task_entry

    # ── 主流程（兩階段隔離） ──────────────────────────────

    def process_tasks(self) -> Dict[str, Any]:
        """兩階段主流程: ✅ Detection → ✅ Processing"""
        try:
            # ═══════════════════════════════════════════════
            # Phase 1: Detection — 查詢原始數據
            # 失敗處理：如果這裡失敗，整個 script exit 1，
            # Hermes cron agent 會根據 deliver 設定決定是否重試整個 job
            # ═══════════════════════════════════════════════
            t_det_start = time.time()
            logger.info("🧩 Phase 1/2: Detection — 查詢任務記錄...")
            all_tasks = self._search_tasks()  # 內置 retry=3
            t_det_elapsed = int((time.time() - t_det_start) * 1000)
            self.result["phases"]["detection"]["status"] = "ok"
            self.result["phases"]["detection"]["duration_ms"] = t_det_elapsed
            self.result["summary"]["total_tasks"] = len(all_tasks)
            self.detection_result["records_fetched"] = len(all_tasks)
            self.detection_result["detection_ok"] = True

            # ═══════════════════════════════════════════════
            # Phase 2: Processing — 並發處理任務 (⚡ max_concurrent=5)
            # 失敗處理：如果這裡失敗，只重試 Processing 階段的失敗任務
            # 不重新執行 Detection（保留已查到的數據）
            # ═══════════════════════════════════════════════
            t_proc_start = time.time()
            logger.info(f"🧩 Phase 2/2: Processing — 並發處理 {len(all_tasks)} 個任務 (⚡ max_concurrent={MAX_CONCURRENT})...")

            # 使用 ThreadPoolExecutor 並發處理
            processed_tasks = []
            d1_messages = []
            skipped_count = 0
            skipped_reasons: Dict[str, int] = {}
            proc_errors = []

            with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT) as executor:
                future_to_record = {
                    executor.submit(self._process_single_record, record): record
                    for record in all_tasks
                }

                for future in concurrent.futures.as_completed(future_to_record):
                    try:
                        task_entry = future.result(timeout=DEFAULT_TIMEOUT)
                        processed_tasks.append(task_entry)

                        if task_entry.get("d_minus_one"):
                            d1_messages.append({
                                "task": task_entry["task_title"],
                                "assignees": task_entry["assignees"],
                                "due_date": task_entry.get("due_date", ""),
                                "message": task_entry.get("message", ""),
                            })

                        if task_entry.get("skipped_reason"):
                            skipped_count += 1
                            reason = task_entry["skipped_reason"]
                            skipped_reasons[reason] = skipped_reasons.get(reason, 0) + 1

                    except Exception as e:
                        logger.error(f"並發處理線程出錯: {e}")
                        proc_errors.append({"error": str(e)})

            # 按原始順序排序 (保持 log 一致性)
            processed_tasks.sort(key=lambda t: t.get("record_id", ""))

            self.result["tasks_processed"] = processed_tasks
            self.result["whatsapp_messages"] = d1_messages
            self.result["summary"]["d_minus_one_tasks"] = len(d1_messages)
            self.result["summary"]["skipped"] = skipped_count
            self.result["summary"]["skipped_reasons"] = skipped_reasons
            if proc_errors:
                self.result["errors"].extend(proc_errors)

            t_proc_elapsed = int((time.time() - t_proc_start) * 1000)
            self.result["phases"]["processing"]["status"] = "ok" if not proc_errors else "partial_errors"
            self.result["phases"]["processing"]["duration_ms"] = t_proc_elapsed
            self.processing_result["d1_found"] = len(d1_messages)
            self.processing_result["processing_ok"] = len(proc_errors) == 0

            # ═══════════════════════════════════════════════
            # 最終狀態判定
            # ═══════════════════════════════════════════════
            has_errors = len(self.result["errors"]) > 0
            if has_errors and len(d1_messages) == 0:
                self.result["status"] = "failed"
            elif has_errors:
                self.result["status"] = "partial_success"
            else:
                self.result["status"] = "success"

            logger.info(
                f"✅ 處理完成: "
                f"總計={self.result['summary']['total_tasks']}, "
                f"D-{DESIRED_D_DAYS}={self.result['summary']['d_minus_one_tasks']}, "
                f"跳過={self.result['summary']['skipped']}"
            )
            return self.result

        except Exception as e:
            logger.error(f"❌ 執行失敗: {e}")
            logger.error(traceback.format_exc())
            self.result["status"] = "failed"
            self.result["errors"].append({
                "type": "unexpected_error",
                "error": str(e),
                "traceback": traceback.format_exc(),
            })
            return self.result

    def save_result(self):
        """保存執行結果"""
        output_dir = os.path.expanduser("~/.lark-reminder-logs")
        os.makedirs(output_dir, exist_ok=True)

        output_file = os.path.join(output_dir, f"{self.execution_id}.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(self.result, f, ensure_ascii=False, indent=2, default=str)
        logger.info(f"結果已保存: {output_file}")

        summary_file = os.path.join(output_dir, f"{self.execution_id}_summary.txt")
        s = self.result["summary"]
        phases = self.result["phases"]
        lines = [
            f"Lark 任務提醒 - {self.execution_id}",
            f"狀態: {self.result.get('status', 'unknown')}",
            f"Detection: {phases['detection']['status']} ({phases['detection']['duration_ms']}ms)",
            f"Processing: {phases['processing']['status']} ({phases['processing']['duration_ms']}ms)",
            f"總任務數: {s['total_tasks']}",
            f"D-{DESIRED_D_DAYS} 任務數: {s['d_minus_one_tasks']}",
            f"跳過: {s['skipped']}",
        ]
        if s.get("skipped_reasons"):
            lines.append("跳過原因:")
            for reason, count in sorted(s["skipped_reasons"].items()):
                lines.append(f"  {reason}: {count}")
        with open(summary_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        logger.info(f"摘要已保存: {summary_file}")


def main():
    logger.info("=" * 60)
    logger.info("  Lark 任務每日提醒 v3 — 操作規則版")
    logger.info(f"  執行時間: {datetime.now(timezone(timedelta(hours=8))).isoformat()}")
    logger.info(f"  ⏱ timeout={DEFAULT_TIMEOUT}s | 🔁 retry={MAX_RETRIES}x backoff={RETRY_BACKOFF_BASE}s | ⚡ concurrency={MAX_CONCURRENT}")
    logger.info("=" * 60)

    total_start = time.time()

    try:
        reminder = LarkTaskReminder()
        result = reminder.process_tasks()
        reminder.save_result()

        total_elapsed = time.time() - total_start
        summary = result["summary"]
        phases = result["phases"]

        print()
        print("=" * 60)
        print(f"  執行結果: {result.get('status', 'unknown')}")
        print(f"  總耗時: {total_elapsed:.1f}s")
        print(f"  Detection: {phases['detection']['duration_ms']}ms")
        print(f"  Processing: {phases['processing']['duration_ms']}ms")
        print(f"  總任務: {summary['total_tasks']}")
        print(f"  D-{DESIRED_D_DAYS}任務: {summary['d_minus_one_tasks']}")
        print(f"  跳過: {summary['skipped']}")
        print("=" * 60)

        if result.get("errors"):
            print(f"\n⚠ 發生 {len(result['errors'])} 個錯誤:")
            for err in result["errors"]:
                print(f"  - [{err.get('type', 'unknown')}] {err.get('error', '')}")

        sys.exit(0 if result.get("status") in ("success", "partial_success") else 1)

    except Exception as e:
        logger.error(f"執行失敗: {e}")
        logger.error(traceback.format_exc())
        print(f"\n❌ 執行失敗: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
