# Session Handover

## 2026-11-17: v1.0.0 initial build

**Delivered**
- `WorkLedger_1_0_0_0.zip`, a Power Platform solution with two flows:
  - *Daily Capture* (23:30 Dubai): sent email, attended meetings, Teams chats I took part in, and `#ledger` notes → AI Builder prompt → `tblLedger` in Excel
  - *Weekly Digest* (Friday 15:00): weekly rows → executive impact report email
- Prompts: `prompts/daily-extractor.md` (JSON output, L1–L5 scoring, PII guard) and `prompts/weekly-report.md` (HTML report)
- `template/WorkLedger.xlsx` with the Ledger, Dashboard, Tech Radar and How-it-works tabs, plus the sample workbook, walkthrough and weekly email in `samples/`

**Design decisions**
- Power Automate with standard M365 connectors, so nothing is installed and consent is already in place. The only premium dependency is the AI prompt (Dataverse).
- Each source is isolated in its own scope with exponential retry, and results go into top-level variables, so a failed source doesn't block the run.
- Idempotent: a day already present (Date as text) is skipped.
- Data stays in the M365 tenant. No work data in this repo.

**Open items / next**
- [ ] Import into the tenant and re-select the Excel file and table plus both prompts (see `docs/INSTALL.md`)
- [ ] Confirm the tenant allows Graph `/me/chats` through the Teams connector
- [ ] v1.1: add OneDrive/SharePoint documents I authored as a fifth source
- [ ] v1.2: a monthly "career evidence" digest and a quarterly appraisal pack (Word)

## 2026-11-17: prompt test inputs

- Added `samples/test-input-daily.json` and `samples/test-input-weekly.json` as ready-to-paste sample values for the AI prompt Test step.
- INSTALL.md now covers model selection: GPT-4.1 mini retires on 2026-12-02, so use GPT-6 Luna or the newest model available.
- The daily prompt is created and pasted in the tenant (1 input, JSON output). Next: test with the sample input, create the weekly prompt, then import the solution.
