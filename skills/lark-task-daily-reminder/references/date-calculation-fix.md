# Date Calculation Fix History

## v1.2.0 (2026-07-06) — CRITICAL: Midnight-to-Midnight Comparison

### The Bug
`_calculate_days_remaining()` used **9:00 AM** as the "current time" baseline but **midnight** for the due date, creating a ~9-hour window mismatch:

| Scenario | Old (9am vs midnight) | Expected | Correct? |
|----------|----------------------|----------|----------|
| July 6, due July 8 | `delta = 1d 15h` → `days=1` → **D-1!** | `days=2` — not D-1 yet | ❌ fires 1 day early |
| July 7, due July 8 | `delta = 15h` → `days=1` → D-1 | `days=1` → D-1 | ✅ correct |
| Due same day | `delta = -9h` → `days=-1` | `days=0` — due today | ❌ shows negative |

### Symptoms
- **Double reminders**: Same task alerted on day X and day X+1 (once from early bug, once correct)
- **Negative days for due-today tasks**: `days_remaining_-1` in logs when task is actually due today
- **D-1 fires 1 day early**: Tasks shown as D-1 when they're actually 2 calendar days away

### The Fix
Compare **midnight-to-midnight** — remove the artificial 9-hour offset:

```python
# BEFORE (buggy):
current = now_hkt.replace(hour=9, minute=0, second=0, microsecond=0)
due = due.replace(hour=0, minute=0, second=0, microsecond=0)
delta = due - current
days = delta.days
if days == 0 and delta.total_seconds() > 0:
    days = 1

# AFTER (fixed):
today = now_hkt.replace(hour=0, minute=0, second=0, microsecond=0)
due = due.replace(hour=0, minute=0, second=0, microsecond=0)
return (due - today).days
```

### Verification
Run the standalone test suite:
```bash
python3 /tmp/test_dates_fix.py
```

All 8 test cases pass, confirming:
- Tasks due 2+ days away no longer incorrectly trigger D-1
- Due-today tasks show `days=0` instead of `-1`
- True D-1 tasks still trigger correctly

---

## Historical Note (pre-v1.2.0 approach — DO NOT USE)

The previous "fix" used 9:00 AM as a comparison anchor, which was itself the source of the offset bug. This approach has been removed. Midnight-to-midnight is the correct, stable comparison.
