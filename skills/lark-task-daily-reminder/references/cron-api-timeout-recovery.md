# Cron Job API Timeout Recovery

## Symptom

The cron job fires at 09:00 but no message arrives in the WhatsApp group.
The gateway log shows the job started (`Running job 'Lark Task Daily Reminder'`), 
the first API call completes (slow, 60+s), but then the stream goes stale for 180s
and the connection is killed with `Broken pipe`.

## Root Cause

DeepSeek API (or the configured provider) is slow or stalls mid-stream during the
cron run. The gateway has a 180s stale-stream timeout — if no chunks arrive in
that window, the connection is killed and the retry also fails with `Broken pipe`.

## Quick Recovery

```bash
# 1. Run the detection script manually
python3 /home/lscm-admin/.hermes/skills/lark-task-daily-reminder/scripts/run_reminder.py

# 2. Read the latest JSON result
ls -t ~/.lark-reminder-logs/reminder_*.json | head -1

# 3. Send reminders to the WhatsApp group using send_message
#    Target format from send_message list output (include the parenthetical group name):
#    whatsapp:120363427742617493 (group)
```

## Detection Logs

Check gateway log for cron start-up and failure:

```bash
grep "cron_$(hermes cron list | grep 'job_id' | head -1 | grep -oP '\w{12}')" ~/.hermes/logs/agent.log
```

Key failure signatures in agent.log:
- `Stream stale for 180s` → API provider not streaming
- `Broken pipe` → connection killed after stale timeout
- `Turn ended: reason=error` → cron job never produced output

## Prevention Options

1. **Switch provider**: Use a faster/more reliable model for cron jobs
   - Set `--model` and `--provider` when creating the cron job
2. **Rate-limit workaround**: If DeepSeek is the only option, schedule well before
   peak hours (e.g. 08:30 instead of 09:00)
3. **Shorten prompt**: Trim the cron prompt to reduce context tokens
4. **no_agent mode**: For pure data-collection workloads, use `no_agent=True` 
   with a script that produces the final message text directly — skips the LLM entirely
