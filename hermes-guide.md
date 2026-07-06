# Hermes Guide

This document provides practical guidance for using Hermes in this project, including how to organize skills and how the PM bot workflow works.

---

## 1. What is Hermes?

Hermes(https://github.com/NousResearch/hermes-agent/blob/main/README.zh-CN.md) is the orchestration layer of this project. It connects user conversations from WhatsApp with structured operations in Lark, and routes requests to the correct skill based on the user’s intent.()

In this project, Hermes is responsible for:

- receiving messages from WhatsApp
- interpreting user intent
- selecting and executing the appropriate skill
- returning the result back to WhatsApp
- coordinating scheduled and interactive workflows

---

## 2. Project Overview

This project is a PM bot built on Hermes. It helps project managers manage deadlines, team capability information, and project documentation through natural language interaction.

The system combines:

- **WhatsApp** as the user interface
- **Hermes** as the AI orchestration layer
- **Lark** as the structured document and data storage layer
- **JSON documents** for team capability records

---

## 3. Core Workflow

A typical workflow looks like this:

1. A user sends a message in WhatsApp
2. Hermes receives the message
3. Hermes determines the user’s intent
4. Hermes routes the request to one of the skills
5. The skill performs the corresponding action
6. Hermes sends the result back to WhatsApp or stores it in Lark

Example:

- A PM asks: “What tasks are due soon?”
- Hermes detects a deadline reminder request
- `lark-task-daily-reminder` scans tasks and prepares a reminder
- The result is sent to WhatsApp

---

## 4. Routine maintenance and troubleshooting
### 4.1 Open Hermes in WSL
- enter `hermes` 

---

### 4.2 Check out the skills Hermes currently has
- enter`hermes skills list`

---

### 4.3 Change model/API expiration
- enter`hermes model`
- If you are replacing an existing model, you can select a model in the list
- If you directly enter the API, please select "Custom endpoint"

---

### 4.4 Create new skill
- use skill "skill-creator" ,you can refer https://blog.csdn.net/wochunyang/article/details/160411559
---

### 4.5 gateway shitting down?
- Normally, Hermes can reconnect by itself. If you want to restart manually, enter `hermes gateway restart`

---

### 4.6 To view the SKILL.md of a skill individually
- enter `cat ~/.hermes/skills/skill-name/SKILL.md`

---


