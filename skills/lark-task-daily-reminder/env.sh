#!/bin/bash
# Environment variables for Lark Task Daily Reminder

# Lark API credentials
export LARK_APP_ID="cliXXXXXXXXXXXXXXXXXXXXXXX"
export LARK_APP_SECRET="zXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
export LARK_BASE_TOKEN="FwXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
export LARK_TABLE_ID="tbXXXXXXXXXXXXXXXXX"

# WhatsApp configuration
export WHATSAPP_CHAT_ID="your_whatsapp_chat_id_here"

# Optional: Logging configuration
export LOG_LEVEL="INFO"  # DEBUG, INFO, WARNING, ERROR
export LOG_DIR="/var/log/lark-reminder"

# Optional: Timezone (default: Asia/Hong_Kong)
export TZ="Asia/Hong_Kong"

# Optional: Retry configuration
export MAX_RETRIES="3"
export RETRY_DELAY="5"

echo "Environment variables set for Lark Task Daily Reminder"
