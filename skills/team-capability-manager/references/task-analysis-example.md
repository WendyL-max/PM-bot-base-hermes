# Task Analysis Example: Q3 Customer Feedback Review

Captured from session 2026-07-03. Use as a concrete template for the Task Analysis & Assignment Suggestion Workflow.

## Original Input

User received a task: "Q3 Customer Feedback Review"
Three issues reported:
1. New users find onboarding too long and confusing
2. Peak-hour page load 5-8s, mobile is worse than desktop
3. Export report numbers don't match page display — cache or sync delay?

## Analysis Output

| Issue | Root Cause Hypothesis | Suggested Action | Skill Needed | Suggested Lead | Support |
|-------|----------------------|------------------|-------------|---------------|---------|
| Onboarding confusion | Too many steps, weak guidance, no progress indicator | User journey mapping, identify drop-off points, add tooltip + skip option | UI/UX | Designer | — |
| Slow page load (5-8s) | Large frontend bundle, slow API/DB, no CDN, images unoptimized | Lighthouse benchmark, check DB query bottleneck, lazy load, code splitting | Backend + Frontend | Backend Dev | Frontend Dev |
| Export data mismatch | Cache vs live DB discrepancy, async computation not completed | Compare query sources, add data timestamp on export, unify read path | Backend | Backend Dev | — |

## Lark Registration

Registered in bitable (Fw8qb31XFaGN6assxmRl0Y5fg9c / tblvHm23ajXhrXzp):
- Task: "Q3 Customer Feedback Review"
- Category: Others
- Priority: High
- Status: 進行中
- Description: Full analysis with 3 issues + suggested actions
- Start Date: 2026-07-03
- Record ID: recvoiL5kmCPIB
