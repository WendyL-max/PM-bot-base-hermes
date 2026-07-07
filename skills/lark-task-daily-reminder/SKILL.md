---
name: lark-task-daily-reminder
description: A skill for setting up a daily cron job that checks Lark (Feishu) multi-dimensional table tasks and sends WhatsApp reminders one day before the due date.
tags: [lark, feishu, cron, reminder, whatsapp, productivity]
trigger: |
  When the user needs to:
  1. Set up daily automated D-1 task reminders from Lark tables to WhatsApp
  2. Check or verify the cron job for task reminders
  3. Fix or update the Lark table connection for reminders
  4. Reference the actual field names of the project task table
  Note: For on-demand (@Reminder in WhatsApp) reminders, use the
  lark-whatsapp-reminder-ondemand skill instead.
---

# Lark Task Daily Reminder Skill

## Overview
A skill for setting up a daily cron job that checks Lark (Feishu) multi-dimensional table tasks and sends WhatsApp reminders one day before the due date.

## Purpose
Automatically monitor task deadlines in Lark tables and send timely reminders to responsible persons via WhatsApp at 9:00 AM Hong Kong time every day.

## Operational Rules (v3)

All external operations in the detection script follow quantified operational rules:

| Rule | Value | Implementation |
|------|-------|---------------|
| ⏱ Timeout | `30s` | All `requests` calls use `timeout=30` |
| 🔁 Retry | `3x` | `@with_retry` decorator on all API methods |
| 🔁 Backoff | `2s` (exponential: 2, 4, 6) | `RETRY_BACKOFF_BASE * attempt` |
| ⚡ Concurrency | `max 5` | `ThreadPoolExecutor(max_workers=5)` for task processing |
| 🧩 Failure isolation | Detection ≠ Processing | If detection fails → script exits (cron retries whole job). If processing fails → only that task is retried, detection data is preserved. |
| ⏰ Schedule | `09:00 HKT` daily | Hermes cron `0 9 * * *` with `deliver=whatsapp:...` |

These constants are defined at the top of `run_reminder.py`:

```python
DEFAULT_TIMEOUT = 30            # ⏱ 單步操作超時 (秒)
MAX_RETRIES = 3                 # 🔁 最大重試次數
RETRY_BACKOFF_BASE = 2          # 🔁 重試間隔基數 (秒)
MAX_CONCURRENT = 5              # ⚡ 並發處理上限
SCHEDULE_HOUR = 9               # ⏰ 每日執行時間 (HKT)
DESIRED_D_DAYS = 1              # 提前N天提醒 (D-N)
```

The execution result JSON includes a `rules_applied` field that records which rules were active during that run, and a `phases` object that tracks detection vs processing timing and status separately.

## Requirements
- Python 3.7+
- Lark (Feishu) API access
- WhatsApp integration via Lark
- Environment variables configured

## Configuration

### Environment Variables
Set the following environment variables:

```bash
export LARK_APP_ID="your_app_id"
export LARK_APP_SECRET="your_app_secret"
export LARK_BASE_TOKEN="your_base_token"  
export LARK_TABLE_ID="your_table_id"      
export WHATSAPP_CHAT_ID="your_whatsapp_chat_id"
```

### Lark Table Structure (Verified via Open API)

The table uses **English field names** (not Chinese). Actual fields discovered via field_list API:

| Field Name | Type | Purpose | API Field ID |
|-----------|------|---------|-------------|
| `Task` | Text (Primary) | Task title | `fldGqXXXXX` |
| `Description` | Text | Task description | `fldGqXXXXX` |
| `Assignee` | MultiSelect | Responsible person(s) — values: Vincent, Frances, Man, Viola, Annabelle, SoNim, Kevin | `fldGqXXXXX` |
| `Progress Log` | Text | Progress tracking notes | `fldGqXXXXX` |
| `Priority` | MultiSelect | Task priority — values: Medium, Medium&Urgent, High, Low | `fldGqXXXXX` |
| `Status` | SingleSelect | Task status — values: 進行中, 已完成, 已停滯 | `fldGqXXXXX` |
| `Category` | MultiSelect | Task category | `fldGqXXXXX` |
| `Start Date` | DateTime (ms) | Task start date | `fldGqXXXXX` |
| `預計完成日期` | DateTime (ms) | Due date | `fldGqXXXXX` |
| `實際完成日期` | DateTime (ms) | Actual completion date | `fldGqXXXXX` |
| `是否延期` | Formula | Auto-calculated (✅正常 / 🚨已延期) | `fldGqXXXXX` |
| `父記錄` | Two-way link | Parent task link (if subtask) | `fldGqXXXXX` |

**Important for the reminder script:**
- Filter by `Status = "進行中"`
- Check `預計完成日期` for D-1 tasks (millisecond timestamps)
- `Assignee` uses option names as MultiSelect values (e.g., `["Vincent", "Man"]`)
- `Task` is a Text array: `[{"text": "Task title", "type": "text"}]`

## Usage

### Manual Execution
```bash
# Run the detection script (standalone — outputs results to ~/.lark-reminder-logs/)
python /home/lscm-admin/.hermes/skills/lark-task-daily-reminder/scripts/run_reminder.py
```

### Hermes Cron Job (Current Setup)

Current live cron job (run `hermes cron list` to verify):
- **Job ID:** `3987627b8a50`
- **Schedule:** `0 9 * * *` (daily 9:00 AM HKT)
- **Skills:** `lark-task-daily-reminder`
- **Toolsets:** `terminal`, `file`
- **Deliver:** `whatsapp:120XXXXXXXXXXXX7493` (sends directly to WhatsApp group)
- **Next run:** daily at 2026-07-07T09:00:00+08:00

The cron agent:
1. Runs the detection script (Python) via terminal
2. Reads the JSON output programmatically (no ls/cat/file paths exposed)
3. Its final text response IS the WhatsApp message — delivered automatically via the `deliver` setting
4. Format: **clean plain text only** — no markdown, no code blocks, no technical details

**WhatsApp Output Rules (strict):**
- NO shell commands (python3, ls, cat, grep, tail, head, ps)
- NO file paths (/home/..., ~/.lark-reminder-logs/)
- NO log content, terminal output, or JSON raw data
- NO cron job IDs or execution IDs
- NO markdown tables, code blocks, or backticks
- NO technical debugging or "step 1..." narration
- ONLY the clean user-facing reminder message
- Simple bullet points with task names and assignees
- **Broader rules apply**: See `cross-channel-behavior-rules` → `references/whatsapp-output-rules.md` for the full user-authored rule set covering ALL WhatsApp delivery.

**CRITICAL: Set `--deliver` to `whatsapp:120XXXXXXXXXXXX7493` when creating the job.**
If you set `deliver: "local"` (the implicit default), the message is saved to a file and NEVER reaches WhatsApp.

To recreate:
```bash
hermes cron create \
  --name "Lark Task Daily Reminder" \
  --schedule "0 9 * * *" \
  --skills lark-task-daily-reminder \
  --deliver "whatsapp:120XXXXXXXXXXXX7493" \
  --enabled_toolsets terminal,file
```
The full prompt text is in `references/cron-prompt-templates.md`. Use `--prompt "$(cat /home/lscm-admin/.hermes/skills/lark-task-daily-reminder/references/cron-prompt-templates.md | sed -n '/^Prompt:/,/^##/p' | tail -n +2)"` to load it directly, or copy it manually.

Note: 0 9 * * * = 9:00 AM Hong Kong time (Asia/Hong_Kong)

### Traditional Cron Setup (Alternative)
Add to crontab for daily execution at 9:00 AM Hong Kong time:

```bash
# Edit crontab
crontab -e

# Add this line (adjust path as needed)
0 1 * * * /usr/bin/env bash -c 'source /home/lscm-admin/.hermes/skills/lark-task-daily-reminder/env.sh && python /home/lscm-admin/.hermes/skills/lark-task-daily-reminder/scripts/run_reminder.py >> /var/log/lark-reminder/cron.log 2>&1'
```

Note: 1:00 UTC = 9:00 HKT (Hong Kong Time)

### Testing
Run the comprehensive test suite:

```bash
python /home/lscm-admin/.hermes/skills/lark-task-daily-reminder/scripts/test_reminder.py
```

## How It Works

### Architecture (Detection-Only Script + Hermes Cron Agent)
The system uses a **two-phase architecture**:
1. **Detection script** (`run_reminder.py`): Runs via Python, calls Lark Open API directly using `requests`. Queries the table, filters by Status=進行中, calculates D-1 from 預計完成日期. Outputs results to `~/.lark-reminder-logs/` as JSON. Does NOT send messages.
2. **Hermes cron agent**: Runs the script via `terminal`, reads the JSON output, and its final text response IS the WhatsApp message — delivered automatically by the cron scheduler's `deliver` setting. No `send_message` tool call needed; the agent just produces clean plain-text output and the scheduler routes it to the target. This avoids the complexity of Lark IM API chat_id routing and eliminates the risk of the agent forgetting to call send_message.

### 1. Task Filtering Logic
The detection script filters tasks based on:
- **Status**: Only tasks where `Status = "進行中"` are considered
- **Due Date**: Tasks due tomorrow (D-1) based on Hong Kong time, using the `預計完成日期` field (millisecond timestamp format)
- **Assignee**: Tasks must have at least one person assigned in the `Assignee` MultiSelect field
- **Date Calculation**: `days = (due_midnight - today_midnight).days` — pure calendar day comparison (see v1.2.0 bug fix).

### 2. Timezone Handling
- All calculations use Hong Kong timezone (Asia/Hong_Kong)
- Comparison is done at 9:00 AM HKT for consistency
- Supports various date formats in Lark tables

### 3. WhatsApp Integration
- Sends reminders via Lark's WhatsApp integration
- Message format: `【任務提醒】@{負責人}，任務「{任務標題}」將於明天({預計完成日期})到期，請及時處理！`
- Includes document link if available
- Uses @mention format for better visibility

### 4. Logging and Monitoring
- Detailed logs in `/var/log/lark-reminder/`
- JSON results for each execution
- Summary reports
- Error tracking and alerting

## Files

### Main Script
- `/home/lscm-admin/.hermes/skills/lark-task-daily-reminder/scripts/run_reminder.py` - Main execution script

### Test Script
- `/home/lscm-admin/.hermes/skills/lark-task-daily-reminder/scripts/test_reminder.py` - Comprehensive test suite

### Configuration Template
- `/home/lscm-admin/.hermes/skills/lark-task-daily-reminder/env.sh.template` - Environment variable template

### Skill Documentation
- `/home/lscm-admin/.hermes/skills/lark-task-daily-reminder/SKILL.md` - This file

### References
- `references/cronjob-setup.md` - Detailed Hermes cron job setup guide
- `references/date-calculation-fix.md` - Fix for D-1 task detection logic
- `references/hermes-cron-integration.md` - Complete guide to Hermes cron system integration, monitoring, and troubleshooting
- `references/cron-api-timeout-recovery.md` - Cron job silent failure from API timeout, manual recovery procedure
- `references/cron-prompt-templates.md` - Full cron job prompt text and design rules for recreation

## Testing Coverage

The test suite covers:
1. **Normal D-1 tasks** - Valid tasks that should trigger reminders
2. **No D-1 tasks** - Tasks that shouldn't trigger reminders
3. **Completed/cancelled tasks** - Filtered out by status
4. **Missing due dates** - Tasks without due dates
5. **Missing owners** - Tasks without assigned persons
6. **Lark API failures** - Network or authentication issues
7. **WhatsApp send failures** - Message delivery issues
8. **Timezone boundaries** - Edge cases around time calculations
9. **Date parsing** - Various date formats and timestamps
10. **Comprehensive scenarios** - Mixed conditions

### Important Test Fix

**CRITICAL BUG FOUND & FIXED (2026-07-06):** The date calculation in `_calculate_days_remaining()` used `now.replace(hour=9, ...)` vs `due.replace(hour=0, ...)`, creating a 9-hour window shift. This caused:

1. **D-1 reminders firing one day early** (e.g. July 6 would flag a July 8 task as D-1)
2. **Due-today tasks returning `-1` days** instead of `0`
3. **Potential double reminders** (once from the early bug, once on the correct day)

The fix: both comparisons now use midnight (`hour=0`), so delta is exact calendar days.

```python
# BAD (removed):
current = now_hkt.replace(hour=9, minute=0, ...)  # 9AM shift
delta = due_midnight - current_9am
if days == 0 and delta.total_seconds() > 0:
    days = 1

# GOOD (current):
today = now_hkt.replace(hour=0, minute=0, ...)  # midnight baseline
return (due_midnight - today_midnight).days
```
The date calculation logic was refined to properly handle D-1 tasks. The original calculation returned 0 days when comparing today at 9:00 AM with tomorrow at midnight. The fix ensures that any positive time difference less than 24 hours is counted as 1 day remaining.

**Key learning**: When calculating days remaining between a fixed morning time (9:00 AM) and a midnight deadline, use this logic:
```python
delta = due_date_start - current_date
days = delta.days
if days == 0 and delta.total_seconds() > 0:
    days = 1  # Less than 24 hours but still positive
return days
```

## Error Handling

### Graceful Degradation
- Continues processing other tasks if one fails
- Logs detailed error information
- Provides actionable error messages

### Retry Logic (v3 — Implemented)
All external API calls are wrapped with `@with_retry` decorator:
- **Max retries**: 3
- **Backoff**: Exponential (2s, 4s, 6s)
- **Scope**: Auth, GET, POST — all Lark API operations
- **Detection vs Processing isolation**: If detection API fails → 3 retries, then script exits for cron to retry whole job. If processing fails → only that task entry is marked as error, other tasks continue.

### Alerting
- Logs errors to `/var/log/lark-reminder/error.log`
- Can be extended to send alerts via email or webhook

## Performance Considerations

### Batch Processing
- Fetches records in batches of up to 500 records via Lark paginated API
- Processes tasks concurrently with `ThreadPoolExecutor(max_workers=5)` (⚡ concurrency limit)
- Each processing thread has a 30s timeout to prevent hung workers

### Memory Usage
- Streams large result sets
- Cleans up temporary objects
- Uses efficient data structures

## Security

### Credential Management
- Environment variables (not hardcoded)
- Secure logging (masks sensitive data)
- File permissions (restrict access to logs)

### API Security
- Uses HTTPS for all Lark API calls
- Validates SSL certificates
- Rate limiting awareness

## Maintenance

### Log Rotation
Set up log rotation in `/etc/logrotate.d/lark-reminder`:

```bash
/var/log/lark-reminder/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
}
```

### Health Checks
Monitor script execution:
```bash
# Check last execution
tail -n 20 /var/log/lark-reminder/cron.log

# Check for errors
grep -i error /var/log/lark-reminder/*.log

# Verify cron job is running
systemctl status cron
```

## Troubleshooting

### Common Issues

1. **Authentication Failures**
   - Verify Lark API credentials
   - Check token expiration
   - Ensure proper permissions

### 2. Cron Job Fires But No WhatsApp Message Arrives (API Timeout / Stale Stream)

The cron job may start successfully at 09:00 but the API provider stalls mid-stream,
causing a 180s stale-stream timeout → `Broken pipe` → silent failure (no output,
no delivery).

**Quick recovery:**
```bash
# Run detection manually, then send via Hermes agent
python3 /home/lscm-admin/.hermes/skills/lark-task-daily-reminder/scripts/run_reminder.py
ls -t ~/.lark-reminder-logs/reminder_*.json | head -1
```

Then use `send_message` with the group target from `send_message(action='list')`
(e.g. `whatsapp:120XXXXXXXXXXXX7493 (group)`).

**Full reference:** `references/cron-api-timeout-recovery.md`

### 3. Date Parsing and D-1 Calculation

#### CRITICAL FIX (2026-07-06): Midnight-to-Midnight Comparison

The `_calculate_days_remaining()` method was using **9:00 AM** as the "now" baseline but **midnight** for the due date. This created a ~9-hour window mismatch:

| Scenario | Old (9am vs midnight) | New (midnight vs midnight) | 
|----------|----------------------|---------------------------|
| July 6, due July 8 | `delta = 1day 15h` → `days=1` → **wrong D-1** | `delta = 2 days` → `days=2` → ✅ correct |
| July 7, due July 8 | `delta = 15h` → `days=1` → D-1 ✅ | `delta = 1 day` → `days=1` → D-1 ✅ |
| Due same day | `delta = -9h` → `days=-1` ❌ | `delta = 0` → `days=0` ✅ |

**Symptoms of the bug:**
- Reminders fire **one day too early** for tasks due 2+ days away
- Same task may get **double reminders** (once early + once on correct day)
- Due-today tasks show as `-1` days remaining

**Fix applied in v1.2.0**: Replace `now.replace(hour=9,...)` with `now.replace(hour=0,...)`, removing the artificial 9-hour offset.

```python
# OLD (buggy):
current = now_hkt.replace(hour=9, minute=0, ...)
delta = due_midnight - current_9am  # offset mismatch!

# NEW (fixed):
current = now_hkt.replace(hour=0, minute=0, ...)
delta = due_midnight - today_midnight  # same reference point
```

Verify date calculation with the test suite:
```bash
python3 /tmp/test_dates_fix.py
```
   - Verify date format in Lark table
   - Check timezone settings
   - Test with sample dates

3. **No WhatsApp message received**
   - **Most likely cause**: Cron job `deliver` is set to `"local"` instead of `"whatsapp:120XXXXXXXXXXXX7493"`
   - Fix: Delete the cron job and recreate with `--deliver "whatsapp:120XXXXXXXXXXXX7493"`
   - Verify with `hermes cron list` — check the `deliver` field
   - Lark chat IDs (`42864XXXXXX222@lid`) are NOT WhatsApp targets; use the plain numeric ID from `send_message(action='list')` (e.g. `whatsapp:120XXXXXXXXXXXX7493`)
   - Test manual delivery: `send_message(target="whatsapp:<id>", message="test")`

4. **Cron Job Not Running**
   - Check cron service status
   - Verify environment variables
   - Check file permissions

5. **Hermes Cron Job Issues**
   - Use `hermes cron list` to check job status
   - Update schedule with `hermes cron update <job_id> --schedule "0 9 * * *"`
   - Manually test with `hermes cron run <job_id>`

### Debug Mode
Enable debug logging by modifying the script:
```python
logging.basicConfig(level=logging.DEBUG, ...)
```

## Limitations

### Overdue Tasks Are Silently Skipped
The script only checks for tasks with exactly 1 day remaining (D-1). Tasks that are already past their due date (days_remaining < 0, e.g. -1, -7) are logged in `skipped_reasons` but produce no alert. If the project needs visibility on overdue items, either:
- Extend the script to flag overdue tasks with a separate message prefix (e.g. "⚠️ 已過期"), or
- Add a second cron job that runs the same data with an overdue filter.

### No Escalation for Repeatedly Missed D-1
If a D-1 task is ignored and becomes overdue, the next day's run will see it as days_remaining < 0 and silently skip it again — it won't re-remind. Consider adding a grace-period flag or checking the `是否延期` formula field for automated overdue detection.

### Dependency on Assignee Field
Tasks with no assignee (`[]`) are always skipped regardless of due date. If a task is assigned later in the day, the next 9 AM run picks it up.

### Custom Message Templates
Modify `_create_reminder_message()` method for different message formats.

### Additional Notifications
Extend to support:
- Email notifications
- Lark chat messages
- SMS alerts

### Advanced Filtering
Add support for:
- Custom status filters
- Priority-based reminders
- Escalation rules

## Dependencies

### Python Packages
- `pytz` - Timezone handling
- Built-in libraries only (no external dependencies)

### System Requirements
- Cron daemon
- Sufficient disk space for logs
- Network access to Lark API

## Version History

### v1.0.0 (Initial Release)
- Basic task filtering and reminder logic
- WhatsApp integration via Lark
- Comprehensive test suite
- Logging and monitoring

### v3.0.0 (2026-07-06) — 量化操作規則版
- ⏱ **Timeout**: 所有API調用統一 `timeout=30s`
- 🔁 **Retry**: 失敗後最多重試3次，指數backoff (2s, 4s, 6s)
- ⚡ **Concurrency**: `ThreadPoolExecutor(max_workers=5)` 並發處理任務
- 🧩 **Failure isolation**: Detection階段失敗 → 重試整個job；Processing階段失敗 → 只重試該任務，不重新Detection
- ⏰ **Schedule**: 預設每日 9:00 HKT
- Added `rules_applied` 和 `phases` 欄位到執行結果JSON
- 記錄每個階段的耗時和狀態

### v1.2.0 (2026-07-06) — CRITICAL BUG FIX
- **Fixed `_calculate_days_remaining()`**: Removed 9am vs midnight offset mismatch
  - Old: D-1 reminder fires 1 day early (double reminder bug)
  - New: midnight-to-midnight comparison, accurate D-1 detection
- Fixed cron job `deliver` from `"local"` to `"whatsapp:120XXXXXXXXXXXX7493"` (messages now actually reach WhatsApp)
- Added standalone date calculation test suite

### v1.1.0 (Updated)
- Added Hermes cron job setup instructions
- Fixed date calculation logic
- Added @mention format in messages
- Improved documentation

## Support

For issues or questions:
1. Check the logs in `/var/log/lark-reminder/`
2. Review environment variable configuration
3. Verify Lark API permissions
4. Test with the provided test suite
5. Use `hermes cron list` to check Hermes cron jobs

## License
This skill is provided as-is for use with Hermes Agent.
