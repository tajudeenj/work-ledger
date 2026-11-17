# Work Ledger

**An automatic, AI-scored record of what I build, decide and influence. I don't log anything by hand.**

Senior architecture work is spread across email, meetings, Teams and the thinking that happens between them, and most of it never gets written down. Work Ledger captures it every night from the systems I already use. It classifies each activity by category, technology, effort, complexity and seniority level, writes it to an Excel ledger, and sends me an executive impact report every Friday.

## How it works

```
 Outlook Sent Items ─┐
 Calendar (attended) ┤   23:30 nightly          AI Builder prompt            Excel (OneDrive)
 Teams chats (mine) ─┼─► Daily Capture flow ──► "Daily Extractor"   ──►  WorkLedger.xlsx
 "#ledger" notes ────┘   (collect, de-noise,    (group → activities,       Ledger · Dashboard ·
                          cap, idempotent)       effort, L1–L5, impact,     Tech Radar
                                                 PII-safe)                      │
                                                                                ▼
                         Friday 15:00  Weekly Digest flow ──► "Weekly Report" prompt ──► Impact email
```

| What is captured | How | Effort basis |
|---|---|---|
| Emails I sent | Outlook Sent Items (RSVPs and auto-replies removed) | AI estimate, 0.1–0.5 h each, based on depth |
| Meetings I attended | Calendar view (declined, free and all-day events excluded) | Actual minutes |
| Teams discussions | Graph `/me/chats` → today's messages, only in chats where I posted | AI estimate |
| Strategy and ideas | Any email to myself with `#ledger` in the subject (voice dictation works) | Treated as the highest-signal source |

**Seniority scale:** L1 Operational · L2 Delivery · L3 Solution Design · L4 Enterprise Architecture · L5 Strategic

## Repository layout

| Path | Purpose |
|---|---|
| `solution/WorkLedger_1_0_0_0.zip` | Importable Power Platform solution with both flows |
| `src/flows/*.json` | Readable flow definitions (the source of truth) |
| `prompts/daily-extractor.md` | Prompt for the nightly AI classification |
| `prompts/weekly-report.md` | Prompt for the Friday executive report |
| `template/WorkLedger.xlsx` | Empty ledger with Dashboard and Tech Radar |
| `samples/` | Worked example: raw input, ledger rows, weekly email |
| `build/` | Generators for the solution and the workbook |
| `docs/INSTALL.md` | Step-by-step setup |

## Engineering notes

- **No manual input.** The only optional input is a `#ledger` note.
- **Resilient.** Each source runs in its own scope, so a failure in Teams or the calendar doesn't stop the run. Every connector call uses exponential retry, and a failure alert goes to the owner.
- **Idempotent.** A day is skipped if it's already in the ledger, so reruns never duplicate rows.
- **Bounded.** Caps apply to emails, chats, messages per chat, body lengths and total prompt payload, so a heavy day can't overflow the prompt.
- **Confidential by design.** Data stays inside the Microsoft 365 tenant (Outlook → AI Builder → OneDrive). The prompt prohibits customer identifiers, account numbers, IDs and secrets. This repository contains no work data.
- **Honest scoring.** The prompt is told to be accurate rather than flattering and not to inflate the level or effort.

## Rebuild

```bash
python3 build/build_solution.py     # regenerates src/flows and solution zip
python3 build/build_workbook.py     # regenerates template and sample workbook
```

See `docs/INSTALL.md` to deploy.
