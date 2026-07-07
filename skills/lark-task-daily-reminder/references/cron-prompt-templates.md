# Cron Prompt Templates

## Core Reminder Job (Single-Skill)

Used for the daily 9 AM D-1 reminder cron job. Created with:

```bash
hermes cron create \
  --name "Lark Task Daily Reminder" \
  --schedule "0 9 * * *" \
  --skills lark-task-daily-reminder \
  --deliver "whatsapp:120363427742617493" \
  --enabled_toolsets terminal,file
```

Prompt:

```
You are a Lark task reminder automation agent. Your ONLY output is the final WhatsApp message — nothing else.

Execute these steps silently (no technical details in your final response):

1. Run the detection script: python3 /home/lscm-admin/.hermes/skills/lark-task-daily-reminder/scripts/run_reminder.py

2. Read the latest JSON result programmatically — do NOT use ls/cat/tail or show file paths in your response. Use Python code to read the file at ~/.lark-reminder-logs/ (find latest *_*.json).

3. From the JSON, extract: whatsapp_messages array, total_tasks, d_minus_one_tasks, skipped count.

YOUR FINAL RESPONSE IS THE WHATSAPP MESSAGE. The scheduler delivers your exact final text to WhatsApp. Follow these output rules STRICTLY:

DO NOT output in WhatsApp:
- ❌ Shell commands (python3, ls, cat, grep, tail, head, ps)
- ❌ File paths (/home/..., ~/.lark-reminder-logs/, etc.)
- ❌ Log content or terminal output
- ❌ Cron job IDs or execution IDs
- ❌ JSON structures or raw data
- ❌ Markdown tables, code blocks, backticks
- ❌ Any technical debugging, scanning processes, or internal analysis
- ❌ Skip "step 1..." / "step 2..." narration

ONLY output:
- ✅ The clean user-facing reminder message
- ✅ Simple bullet points with task names and assignees

Format when D-1 tasks exist:
【任務提醒】📋
今日D-1任務（明天到期）：
- {task1} — {assignees}
- {task2} — {assignees}
請相關負責人及時處理！

Format when NO D-1 tasks:
【任務提醒】📋
今日暫無D-1任務需要提醒

That's it. No extra text. No explanations. No analysis. Just the message.
```

## Key Design Rules

- `deliver` must be `whatsapp:<chat_id>` — **not** `"local"` (local = file only, no delivery)
- `enabled_toolsets` only needs `terminal,file` — the deliver setting handles routing, the agent doesn't call send_message
- The agent's final text response IS the message body — keep it clean and WhatsApp-appropriate
- **WhatsApp output rules:** The final response must contain ONLY the user-facing message. No shell commands, file paths, log content, cron job IDs, JSON data, markdown tables, code blocks, or technical narration. Use `execute_code` to read JSON programmatically instead of `ls`/`cat` in terminal.
- No `"messaging"` toolset needed — remove it to save tokens and prevent confusion
- Skills must include `lark-task-daily-reminder` so the table fields are injected into system prompt

## no_agent Mode (Alternative — More Reliable)

For cron jobs that just need to run a script and deliver its output verbatim, use
`no_agent=True` to skip the LLM entirely — no API timeout risk, no token cost.

The script must produce the final message text as stdout. Empty stdout = silent
delivery (nothing sent). The script takes over all formatting and routing logic.

```bash
hermes cron create \
  --name "Lark Task Daily Reminder (no-agent)" \
  --schedule "0 9 * * *" \
  --no_agent \
  --script /home/lscm-admin/.hermes/skills/lark-task-daily-reminder/scripts/run_reminder.py \
  --deliver "whatsapp:120363427742617493"
```

**Caveats:**
- The script must format WhatsApp-appropriate plain text output itself
- Empty stdout = silent run (nothing delivered) — design the script to be quiet when there's nothing to report
- No LLM means no reasoning — the script decides what to send
- Environment variables are read from .env or the process env, not from cron job config
