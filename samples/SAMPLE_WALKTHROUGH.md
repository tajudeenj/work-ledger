# Sample: one day through the Work Ledger

All data below is illustrative.

## 1. What happened on Monday 2026-11-16 (nothing was typed into the ledger)

| Time | Raw signal the flow collected |
|---|---|
| 09:00–10:30 | Calendar: *"ISO 20022 MX migration – cut-over"* (organizer: me, 7 attendees, accepted) |
| 10:45 | Sent: *"RE: MPM CRM integration – design v2"* to vendor + DRB: "…cannot approve direct DB links to ATP; route through APIC and publish change events…" |
| 11:50–12:20 | Teams chat *"CBWSI alert – duplicates"*: 6 messages, 3 from me, about retry timeouts and the alert threshold |
| 12:25 | Sent: *"CBWSI alert filter – updated"* to app support |
| 18:20 | Inbox: email to myself, subject *"#ledger strategy – EA visibility"*, dictated: "Idea: auto-capture architects' work for capacity planning and a value story for the CIO…" |
| 13:00 | Sent: *"Thanks!"*. **Ignored** as noise |
| 16:00 | Calendar: *"Vendor demo"*, declined. **Ignored** |

## 2. What the nightly AI wrote to the Ledger tab (23:30)

| Source | Title | Category | Technologies | Effort (h) | Cx | Level | Innovation |
|---|---|---|---|---|---|---|---|
| Meeting | Aligned ISO 20022 cut-over sequencing with Payments | Architecture | ISO 20022, SWIFT, IBM ACE/ESB | 1.5 | 4 | L4 Enterprise Architecture | No |
| Email | Rejected point-to-point CRM integration design | Governance | IBM APIC, Dynamics 365, Oracle ATP | 0.5 | 3 | L4 Enterprise Architecture | No |
| Mixed | Fixed CBWSI log alert false positives | Support | Java | 0.8 | 2 | L2 Delivery | No |
| Note | Proposed AI work-ledger for EA team effort visibility | Innovation | Power Automate, Microsoft 365 Copilot, Excel | 0.5 | 3 | L5 Strategic | Yes |

Sample impact line: *"Prevented a non-compliant integration pattern from reaching SIT."*

The Teams chat and the follow-up email about CBWSI were merged into **one** activity (source "Mixed").

## 3. What the Dashboard shows after 3 days

Open `samples/WorkLedger_SAMPLE.xlsx`:

- Total effort **9.1 h** across **9 activities**, with **4 innovation items**
- **62.6 %** of hours at L4–L5, meaning the week skewed strategic
- Tech Radar: hours, mentions and last-used date for each technology

## 4. What arrives on Friday at 15:00

See `samples/weekly-report-SAMPLE.html` for the full email. An excerpt:

> **Week of 2026-11-16: Moved the bank's AI and payments architecture forward on three fronts.**
> **What we achieved**
> - Agreed a phased ISO 20022 cut-over with Payments, removing big-bang migration risk.
> - Secured Chief AI Officer sponsorship for a governed Copilot Studio agent pilot.
> - Authored ADR-031, which sets an AI gateway as the control point for all GenAI workloads.
>
> **Resume-ready lines**
> - Led ISO 20022 migration architecture, defining a phased cut-over strategy across payments and ESB layers.
