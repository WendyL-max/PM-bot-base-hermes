# WhatsApp Group Behavior Configuration

This reference documents the WhatsApp group noise-reduction and 3-tier response
configuration that was set up for this Hermes instance.

## Overview

WhatsApp group chats are configured to follow three tiers of behavior:
1. @Hermes mention → full response
2. Work-related (no mention) → silent Lark update via MCP tools
3. General chat → read only, no response

## Config Settings

### 1. `display.platforms.whatsapp` (in config.yaml)

```yaml
display:
  platforms:
    whatsapp:
      tool_progress: off             # No individual tool call notifications
      streaming: false               # No intermediate text streaming
      interim_assistant_messages: true  # Allow brief start/confirmation notices
      long_running_notifications: false # No "still working" pings
      busy_ack_detail: false         # Minimal busy indicators
      cleanup_progress: true         # Clean up intermediate bubbles on success
```

### 2. `agent.system_prompt` (in config.yaml)

The system prompt includes WhatsApp group behavior rules covering the three tiers.

### 3. Silence Mechanism

Hermes has a built-in `intentional silence` mechanism:
- When the agent outputs exactly `NO_REPLY`, `[SILENT]`, or `SILENT`
  (defined in `LIVE_GATEWAY_SILENT_MARKERS` in `gateway/response_filters.py`),
  the gateway suppresses delivery entirely
- The agent result must not be a `failed` status for silence to work
- This is used for Tier 2 (work-related) and Tier 3 (general chat) messages

## Why NOT `require_mention`

The `require_mention` + `mention_patterns` approach was considered but rejected
for this use case because:
- It drops non-mentioned messages before the agent sees them
- This prevents Tier 2 (work-related → silent Lark update) from working
- The agent needs to see ALL group messages to decide which tier applies

Instead, `require_mention` is unset so all messages reach the agent. The agent
uses the system prompt rules and `NO_REPLY` marker to handle non-mentioned
messages silently.
