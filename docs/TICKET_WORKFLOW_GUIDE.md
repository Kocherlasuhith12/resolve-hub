# ResolveHub End-to-End Ticket Lifecycle & Operational Guide

Welcome to the **ResolveHub Service Management Platform**. This guide explains the complete end-to-end workflow for creating, triaging, resolving, and closing tickets, including AI Copilot integration, SLA tracking, and ITSM escalations.

---

## 🏗️ 1. Architecture Overview

ResolveHub enforces strict multi-tenant isolation. Every ticket, user, comment, asset, and audit log belongs to an **Organisation (`organisation_id`)**.

```mermaid
flowchart TD
    A[Customer / Requester] -->|1. Submit Ticket| B(ResolveHub Portal)
    B -->|2. Scoped POST /api/v1/organisations/{id}/tickets| C{FastAPI Backend}
    C -->|3. Save Ticket & Compute SLA| D[(PostgreSQL DB)]
    C -->|4. Trigger AI Triage| E[Gemini AI Copilot]
    E -->|5. Match KB Articles & Recommendations| B
    C -->|6. Triage Queue| F[Agent Workspace]
    F -->|7. Investigate & Transition Status| G{State Machine}
    G -->|P1 Escalation| H[Incidents / Outage Command]
    G -->|Root Cause| I[Problems & RCA]
    G -->|Code / Config Deploy| J[Change Advisory Board]
    G -->|8. Mark Resolved| K[Customer CSAT & Analytics]
```

---

## 📝 2. Step 1: Ticket Creation

### A. Submitting a Ticket (Requester Flow)
1. Log in to your ResolveHub workspace at `https://resolvehub-frontend-suhith.onrender.com`.
2. Navigate to **Requests** in the side navigation bar or press **`Cmd + K`** to open the Command Palette.
3. In the **Submit a request** form:
   - **Category**: Select the service area (e.g. *Infrastructure*, *Billing*, *Payment Gateway*).
   - **Title**: A brief summary of the issue (e.g. *Payment Gateway returning 502 errors*).
   - **Description**: Detailed description, steps to reproduce, or error messages.
   - **Priority**: Choose from **P1 - Critical**, **P2 - High**, **P3 - Medium**, or **P4 - Low**.
4. Click **Submit request**.

### B. What Happens Under the Hood
- The browser calls `POST /api/v1/organisations/{organisation_id}/tickets` with a unique `Idempotency-Key` header.
- FastAPI validates tenant membership and persists the ticket to PostgreSQL with status `NEW`.

---

## ⏱️ 3. Step 2: Automated SLA Calculation & AI Copilot Triage

### A. SLA Timer Initialization
Upon creation, the SLA engine evaluates the ticket priority:
- **P1 Critical**: First response within **15 mins**, Resolution within **4 hours**.
- **P2 High**: First response within **30 mins**, Resolution within **8 hours**.
- **P3 Medium**: First response within **2 hours**, Resolution within **24 hours**.
- **P4 Low**: First response within **4 hours**, Resolution within **48 hours**.

### B. Gemini AI Copilot Integration
- The AI Engine scans ticket title and body to calculate an **AI Confidence Score**.
- It automatically suggests **Knowledge Base articles** (`/knowledge`) to the requester for immediate self-service resolution.
- Agents receive recommended resolution steps and automated category tags.

---

## 🛠️ 4. Step 3: Agent Queue & Ticket Investigation

### A. Accessing the Agent Workspace
1. Agents open **Requests** (`/requests`).
2. Toggle between **List View** and **Kanban Board View** to visualize incoming workload.
3. Filter tickets by **Status** (*New*, *Triaged*, *In Progress*, *Resolved*, *Closed*) or **Priority**.

### B. Assigning & Triage
1. Click on any ticket to open the **Ticket Detail & Side Drawer**.
2. Click **Assign to Me** or select an agent from the candidate dropdown list.
3. Add **Internal Notes** (visible only to team agents) or **Public Responses** (notifies the requester).
4. Upload file attachments or diagnostic logs.

---

## 🚨 5. Step 4: ITSM Module Escalations

When dealing with major outages or complex software changes, tickets can be linked directly to dedicated ITSM modules:

| ITSM Module | Route | When to Use |
| :--- | :--- | :--- |
| **Incidents** | `/incidents` | For P1/P2 service outages. Opens a Major Incident Command Room with assigned Incident Commanders and status updates. |
| **Problems** | `/problems` | For recurring tickets. Enables Root Cause Analysis (RCA) tracking and workaround documentation. |
| **Changes** | `/changes` | For software deployments or infrastructure modifications requiring Change Advisory Board (CAB) approval. |
| **Assets** | `/assets` | Links impacted hardware, software licenses, or cloud infrastructure items directly to the ticket. |

---

## ✅ 6. Step 5: Resolving & Closing Tickets

### A. State Machine Transitions
Tickets progress through formal state transitions:

```text
[ NEW ] ➔ [ TRIAGED ] ➔ [ IN PROGRESS ] ➔ [ RESOLVED ] ➔ [ CLOSED ]
```

1. Agent updates status from `IN_PROGRESS` to `RESOLVED`.
2. Agent enters a mandatory **Resolution Summary** explaining the fix.
3. The requester receives notification and can accept the resolution or reopen the ticket if issues persist.
4. Resolved tickets automatically move to `CLOSED` after the review window.

---

## 📊 7. Step 6: Realtime Analytics & Reporting

Navigating to **Analytics** (`/analytics`) provides live operational visibility:
- **Mean Time to First Response (MTTR)**
- **SLA Compliance Rate (%)**
- **Ticket Volume by Category & Priority**
- **Agent Workload Distribution**

---

*ResolveHub Engineering Documentation — Last Updated July 2026*
