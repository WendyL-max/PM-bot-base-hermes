# Lark Integration Guide

This document explains how to connect Hermes to Lark, how to configure permissions and data structure, and how to maintain Lark-side APP settings.

---

## 1. Overview

This project uses Lark as the structured data and document layer for the Hermes PM bot.

Hermes interacts with Lark to:

- read task and project information
- write meeting notes and project updates
- store and query team capability data
- keep project documentation synchronized

This guide focuses on the Lark-side configuration needed for the integration.

---

## 2. Integration Architecture

The integration flow is generally:

1. A user sends a request through WhatsApp
2. Hermes receives the message
3. Hermes routes the request to the appropriate skill
4. The skill performs an action on Lark
5. The result is returned to the user or stored back in Lark

### Main Lark responsibilities

- provide document storage
- provide multi-dimensional table storage
- expose API access for read/write operations
- manage permissions for the Hermes app

---

## 3. Prerequisites

Before setting up the integration, make sure you have:

- a Lark developer account
- access to the target Lark workspace
- permission to create or manage Lark apps
- the target docs / bases / sheets ready for use
- Hermes already installed and available in your environment

---

## 4. Create a Lark App

Hermes creates with one click, you can refer(https://hermes-agent.nousresearch.com/docs/zh-Hans/user-guide/messaging/feishu)

---

## 5. Required Permissions

Hermes must be granted the permissions needed to read and write Lark resources.

The specific permissions depend on your implementation, but in the Lark segment you usually need permissions to access the following business sections:
- Messages and Groups
- multidimensional table(base:xxxx:xxx)
- Cloud documents


### Permission principle

When activating, both application identity and user identity need to be activated.
Only after the permissions are opened on the Lark side, Hermes can obtain subsequent APIs through dialogue.

---

## 6. Environment Variables

Store sensitive Lark credentials outside the codebase.

Example:

```bash
LARK_APP_ID=your_lark_app_id
LARK_APP_SECRET=your_lark_app_secret
LARK_DOC_ID=your_target_doc_id
LARK_BASE_ID=your_target_base_id
LARK_TABLE_ID=your_target_table_id
LARK_WEBHOOK_URL=your_webhook_url
