# Hermes Cron Job Setup for Lark Task Reminder

This document details how to set up and manage the Lark task reminder system using Hermes cron jobs.

## Current Active Job

**Job ID:** `3987627b8a50`
**Schedule:** `0 9 * * *` (daily 9:00 AM HKT)
**Deliver:** `whatsapp:120XXXXXXXXXXXX7493`
**Script:** `run_reminder.py` v3 (timeout=30s, retry=3/backoff=2s, concurrency=5)
**Toolsets:** `terminal`, `file`

## ⚠️ CRITICAL: deliver Setting

The `deliver` field determines WHERE the cron agent's response goes:

| Value | Behavior |
|-------|----------|
| `whatsapp:120XXXXXXXXXXXX7493` | ✅ Sends to WhatsApp group |
| `"local"` | ❌ Saves to file only — **NEVER reaches WhatsApp** |
| `"origin"` | Sends back to the creating channel (usually CLI) |
| `"all"` | Fans out to every connected channel |

**`deliver` CANNOT be changed via `hermes cron update`.** To fix a wrong deliver setting, delete + recreate:
```bash
hermes cron remove <job_id>
hermes cron create \
  --name "Lark Task Daily Reminder" \
  --schedule "0 9 * * *" \
  --skills lark-task-daily-reminder \
  --deliver "whatsapp:120363427742617493" \
  --enabled_toolsets terminal,file \
  --prompt "..."
```

Always verify with `hermes cron list` — if `deliver` is `"local"`, messages stay on disk.

## Create a New Cron Job

```bash
hermes cron create \
  --name "Lark Task Daily Reminder" \
  --schedule "0 9 * * *" \
  --skills lark-task-daily-reminder \
  --deliver "whatsapp:120363427742617493" \
  --enabled_toolsets terminal,file \
  --prompt "You are a Lark task reminder agent..."
```

See SKILL.md for the full prompt text.

## Manage Cron Jobs

```bash
hermes cron list
hermes cron run 3987627b8a50
hermes cron pause <job_id>
hermes cron resume <job_id>
hermes cron remove <job_id>
```

## Testing

```bash
hermes cron run 3987627b8a50
ls -lt ~/.lark-reminder-logs/ | head -5
grep -a "delivered to.*whatsapp\|3987627b8a50" ~/.hermes/logs/agent.log
```

## Troubleshooting

### Messages Never Reach WhatsApp
- **Check**: `hermes cron list` — look at the `deliver` field
- **If "local"**: Must delete and recreate with `--deliver "whatsapp:120XXXXXXXXXXXX7493"`

### Script Fails
- Built-in retry (3x with backoff) handles transient failures
- Manual test: `python3 /home/lscm-admin/.hermes/skills/lark-task-daily-reminder/scripts/run_reminder.py`

### Wrong Deliver
**Cannot be fixed via `update`.** Must delete + recreate:
```bash
hermes cron remove <job_id>
hermes cron create ... --deliver "whatsapp:120363427742617493"
```
