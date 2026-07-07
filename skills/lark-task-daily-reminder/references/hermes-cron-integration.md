# Hermes Cron Integration Guide for Lark Task Reminder

## Overview
This document details the integration between the Lark Task Daily Reminder skill and Hermes' built-in cron system.

## Key Integration Points

### 1. Job Creation and Management
- **Job ID**: `3987627b8a50` (active deployment — replaced `b94b8cf76aef`)
- **Storage Location**: `~/.hermes/cron/jobs.json`
- **Output Directory**: `~/.hermes/cron/output/<job_id>/`
- **Log Directory**: `~/.lark-reminder-logs/`

### ⚠️ CRITICAL: deliver Setting
The `deliver` field determines WHERE the cron agent's response goes:
- `"whatsapp:120363427742617493"` → **sends to WhatsApp group** ✅
- `"local"` → **saves to file only, NEVER reaches WhatsApp** ❌
- `"origin"` → sends back to the channel that created the job (usually CLI, not WhatsApp)
- `"all"` → fans out to every connected channel

**The `deliver` field CANNOT be changed via `hermes cron update`.**
To fix a wrong `deliver`, you must delete and recreate the job:
```bash
hermes cron remove <job_id>
hermes cron create ... --deliver "whatsapp:120363427742617493"
```

Always verify with `hermes cron list` — if `deliver` is `"local"`, messages stay on disk.

### 2. Environment Variable Configuration
Hermes cron jobs can pass environment variables directly to the skill execution:

```bash
# Environment variables used by the skill
LARK_APP_ID=cli_aaa03a9afd399eea
LARK_APP_SECRET=z81dmYHofkA3FFBHLjkivhNJcEg2EW5u
LARK_TABLE_TOKEN=Fw8qb31XFaGN6assxmRl0Y5fg9c
LARK_TABLE_ID=tblvHm23ajXhrXzp
WHATSAPP_CHAT_ID=120363427742617493
```

### 3. Execution Flow (v3)
1. **Scheduler Trigger**: Hermes cron scheduler triggers at 9:00 AM HKT
2. **Skill Loading**: Loads `lark-task-daily-reminder` skill
3. **Script Execution**: Runs `run_reminder.py` (⏱ timeout=30s, 🔁 retry=3, ⚡ concurrency=5)
4. **Phased Processing**:
   - **Phase 1: Detection** — Lark API calls with retry & timeout. If all 3 retries fail → script exits code 1.
   - **Phase 2: Processing** — Tasks processed via ThreadPoolExecutor(max_workers=5). Failed tasks are isolated; detection data is preserved.
5. **JSON Output**: Saved to `~/.lark-reminder-logs/reminder_<timestamp>.json`
6. **Cron agent reads JSON**: Extracts total_tasks, d_minus_one_tasks, whatsapp_messages
7. **Auto-delivery**: Cron scheduler's `deliver` setting routes the agent's final response to the target (e.g. WhatsApp). No `send_message` tool call needed.

### 4. Monitoring and Debugging

#### Log Files
- **Hermes Agent Log**: `~/.hermes/logs/agent.log` - Contains cron execution entries
- **Cron Output**: `~/.hermes/cron/output/<job_id>/YYYY-MM-DD_HH-MM-SS.md` - Detailed execution report
- **Skill Logs**: `~/.lark-reminder-logs/reminder_YYYYMMDD_HHMMSS.*` - Script-specific logs

#### Log Analysis Commands
```bash
# Check cron job execution in agent logs
grep -i "cron.*3987627b8a50" ~/.hermes/logs/agent.log

# List all cron job outputs
ls -la ~/.hermes/cron/output/3987627b8a50/

# View latest execution summary
tail -20 ~/.lark-reminder-logs/reminder_$(date +%Y%m%d)*_summary.txt

# Check for errors in skill execution
grep -i "error\\|fail\\|exception" ~/.lark-reminder-logs/*.log
```

### 5. Common Issues and Solutions

#### Issue: Messages Never Reach WhatsApp (deliver="local")
**Symptoms**: Script runs successfully (logs show D-1 tasks), but no message appears in WhatsApp.
**Root Cause**: Cron job `deliver` is set to `"local"` instead of `"whatsapp:120363427742617493"`.
**Solution**: `deliver` cannot be changed via `update` — must delete + recreate the job:
```bash
hermes cron remove <job_id>
hermes cron create \
  --name "Lark Task Daily Reminder" \
  --schedule "0 9 * * *" \
  --skills lark-task-daily-reminder \
  --deliver "whatsapp:120363427742617493" \
  --enabled_toolsets terminal,file \
  --prompt "..."   # see SKILL.md for full prompt
```
**Verification**: `hermes cron list` — check the `deliver` field shows the WhatsApp target, not "local".

#### Issue: Duplicate Cron Jobs
**Symptoms**: Multiple jobs with same schedule, conflicting executions
**Solution**: 
```bash
# List all cron jobs
hermes cron list

# Remove duplicates
hermes cron remove <duplicate_job_id>
```

#### Issue: Environment Variables Not Passed
**Symptoms**: Script fails with authentication errors
**Solution**:
```bash
# Update job with correct environment variables
hermes cron update 3987627b8a50 \
  --env LARK_APP_ID=cli_aaa03a9afd399eea \
  --env LARK_APP_SECRET=actual_secret \
  --env WHATSAPP_CHAT_ID=actual_chat_id
```

#### Issue: Timezone Mismatch
**Symptoms**: Reminders sent at wrong time
**Solution**:
```bash
# Verify system timezone
timedatectl status

# Update schedule if needed (adjust for your timezone)
hermes cron update b94b8cf76aef --schedule "0 1 * * *"  # 1:00 UTC = 9:00 HKT
```

#### Issue: Permission Denied for Log Directory
**Symptoms**: Script fails to write logs
**Solution**:
```bash
# Create and set permissions for log directory
mkdir -p ~/.lark-reminder-logs
chmod 755 ~/.lark-reminder-logs
```

### 6. Testing and Validation

#### Manual Test Execution
```bash
# Test the cron job manually
hermes cron run 3987627b8a50

# Check test results
ls -la ~/.lark-reminder-logs/ | tail -5
cat ~/.lark-reminder-logs/reminder_$(date +%Y%m%d)*_summary.txt
```

#### Verification Steps
1. **Job Status**: `hermes cron list` shows job as "scheduled"
2. **Next Run**: Verify next run time is correct
3. **Environment**: Confirm environment variables are set
4. **Permissions**: Check log directory permissions
5. **Connectivity**: Test Lark API connectivity manually

### 7. Maintenance Procedures

#### Regular Maintenance
```bash
# Monthly: Clean old logs (keep last 30 days)
find ~/.lark-reminder-logs -name "*.log" -mtime +30 -delete
find ~/.lark-reminder-logs -name "*.json" -mtime +30 -delete

#### Quarterly: Verify cron job configuration
hermes cron list
hermes cron run 3987627b8a50

# Biannually: Update environment variables if changed
hermes cron update 3987627b8a50 --env LARK_APP_SECRET=new_secret
```

#### Troubleshooting Checklist
- [ ] Cron job exists in `hermes cron list`
- [ ] `deliver` is set to `whatsapp:120363427742617493` (NOT "local")
- [ ] Environment variables are correct
- [ ] Log directory exists and writable
- [ ] Lark API credentials valid
- [ ] WhatsApp chat ID correct
- [ ] Timezone set to Asia/Hong_Kong
- [ ] Hermes agent running
- [ ] Network connectivity to Lark API

### 8. Integration Best Practices

1. **Single Source of Truth**: Store environment variables in one place
2. **Regular Testing**: Test cron job monthly
3. **Log Rotation**: Implement log rotation for skill logs
4. **Alerting**: Set up monitoring for failed executions
5. **Documentation**: Keep this guide updated with any changes
6. **Backup**: Regularly backup `~/.hermes/cron/jobs.json`

### 9. Example Successful Deployment (v3)

From actual deployment:
- **Job ID**: `3987627b8a50` (replaced `b94b8cf76aef`)
- **Schedule**: `0 9 * * *` (9:00 AM HKT)
- **Skills**: `lark-task-daily-reminder`
- **Toolsets**: `terminal`, `file`
- **Deliver**: `whatsapp:120363427742617493` (sends to WhatsApp group)
- **Script**: `run_reminder.py` v3 (timeout=30s, retry=3/backoff=2s, concurrency=5)
- **Output**: JSON logs in `~/.lark-reminder-logs/`
- **Status**: Detects D-1 tasks and delivers to WhatsApp daily at 9:00 AM HKT

### 10. Related Skills and Tools
- `lark-bitable-practical-guide` - Lark table operations
- `lark-webhook-deployment` - Lark webhook setup
- `cronjob` tool - Hermes cron management
- `process` tool - Background process monitoring