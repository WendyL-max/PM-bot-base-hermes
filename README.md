# PM-bot-base-hermes
# Hermes PM Bot

Hermes PM Bot is an AI-powered project management assistant built on **Hermes**, integrated with **WhatsApp** and **Lark** to support conversational project tracking, task reminders, team capability management, and document operations.

It allows PMs and team members to chat with the bot on WhatsApp, automatically detect project-related content from conversations, and sync structured information into Lark bitable.

---

## Features

- **WhatsApp-first interaction**
  - Chat with the PM bot directly on WhatsApp
  - Discuss project updates, assignments, deadlines in natural language

- **Automatic project information capture**
  - Detect project-related content from conversations
  - Store structured notes and updates into Lark documents

- **Daily deadline reminders**
  - Identify tasks close to their DDL
  - Send reminder messages to WhatsApp every day at **9:00 AM**

- **Team capability management**
  - Store team members’ skills, strengths, and responsibilities in a JSON document
  - Query team capabilities through conversation
  - Support task allocation and workload discussions

- **Lark document bridge**
  - Access Lark documents from WhatsApp
  - Support CRUD operations on Lark bitable

---

## System Overview

This project uses **Hermes** as the orchestration layer connecting WhatsApp and Lark.

### Main flow

1. A user chats with the PM bot on **WhatsApp**
2. Hermes interprets the request and routes it to the correct skill
3. The skill performs the corresponding action:
   - reminder generation
   - capability lookup
   - Lark document access/update
4. Results are returned to WhatsApp and/or saved into Lark

---

## Skills

This project contains three Hermes skills:

### 1. `lark-task-daily-reminder`
Used to:
- extract tasks that are approaching their deadlines
- send reminders to WhatsApp at **9:00 AM daily**

**Typical use cases**
- daily project follow-up
- deadline risk awareness
- proactive task tracking

---

### 2. `team-capability-manager`
Used to:
- store team members’ capabilities in a JSON document
- query team skills and strengths through conversation
- support task division and team assignment discussions

**Typical use cases**
- ask who is suitable for a task
- compare team member strengths
- support PM decision-making for workload distribution

---

### 3. `whatsapp-lark-document-bridge`
Used to:
- access Lark documents through WhatsApp
- perform CRUD operations on Lark bitable
- keep project notes and discussions synchronized

**Typical use cases**
- query project records
- update task status
- create or modify project notes
- delete obsolete entries

---

## Architecture

```text
WhatsApp
   │
   ▼
Hermes
   │
   ├── lark-task-daily-reminder
   ├── team-capability-manager
   └── whatsapp-lark-document-bridge
   │
   ▼
Lark / JSON Storage
