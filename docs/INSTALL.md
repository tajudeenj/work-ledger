# Install: Work Ledger

Setup takes about 30 minutes, once. After that, everything runs on its own.

## Prerequisites

- An M365 work account with Power Automate access
- A Power Platform environment with Dataverse and AI Builder (or Copilot) credits. This is needed for the two AI prompts.
- **Licensing:** the AI prompt step runs on the Dataverse connector, which is premium. You need Power Automate Premium, a Copilot Studio license, or an environment where AI Builder credits are available. Check with the Power Platform admin.
- **DLP:** Office 365 Outlook, Office 365 Users, Microsoft Teams, Excel Online (Business) and Microsoft Dataverse must all be in the same DLP group.

## Steps

1. **Workbook:** Upload `template/WorkLedger.xlsx` to your OneDrive, e.g. `OneDrive/Documents/WorkLedger/WorkLedger.xlsx`.
2. **Daily prompt:** Go to https://make.powerautomate.com → AI hub → Prompts → **Build your own prompt**. Follow `prompts/daily-extractor.md`: set the name `Work Ledger - Daily Extractor`, choose the newest model offered (e.g., GPT-6 Luna, since GPT-4.1 mini retires on 2026-12-02), add a Text input `ActivityData`, set Output to **JSON**. Click **1 input** and paste the contents of `samples/test-input-daily.json` as the sample value, run **Test**, check that rows are returned, then Save.
3. **Weekly prompt:** In the same place, follow `prompts/weekly-report.md`: set the name `Work Ledger - Weekly Report`, add a Text input `WeekData`, set Output to **Text**. For the test sample value, paste: `Owner: Tajudeen Jalaudin. Week starting 2026-11-16. Rows: ` followed by the contents of `samples/test-input-weekly.json`. Run **Test**, then Save.
4. **Import:** Go to Solutions → **Import solution** → Browse → `solution/WorkLedger_1_0_0_0.zip` → Next. Create or select a connection for each of the five connection references → Import.
5. **Daily Capture flow:** Open Solutions → Work Ledger → **Work Ledger - Daily Capture** → Edit.
   1. Open **Check_already_logged**. Set Location to OneDrive for Business, Document Library to OneDrive, File to `/Documents/WorkLedger/WorkLedger.xlsx` and Table to `tblLedger`.
   2. Open **Process_day → Process → Write_rows → Add_ledger_row**. Select the same file and table, then confirm that each column maps to its value. Column names match the headers.
   3. Open **Process_day → Process → Run_daily_extractor_prompt** and select the prompt `Work Ledger - Daily Extractor`. Map `ActivityData` to the **Payload_text** output.
   4. Leave the Config IDs as they are once the steps above are re-selected. The selected values take precedence.
   5. Save.
6. **Weekly Digest flow:** Open **Work Ledger - Weekly Digest** → Edit.
   1. In **Get_week_rows**, select the same file and table.
   2. In **Has_rows → Report → Run_weekly_report_prompt**, select `Work Ledger - Weekly Report` and keep the `WeekData` mapping.
   3. Save.
7. **Turn on:** Turn on both flows.
8. **First test:** Open Daily Capture → **Run**. Check Run history: all four `Collect_*` scopes should show Succeeded. Then check the new rows in `WorkLedger.xlsx` → Ledger.
9. **Clean up:** Delete the example row (2026-11-16) from the Ledger tab.
10. **Habit (optional, 30 seconds):** In Outlook mobile, start a new email to yourself with the subject `#ledger strategy`, dictate what you thought about or decided, and send it.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Collect_teams` fails with 403 | Your tenant restricts Graph via the Teams connector. The other sources keep working. Ask the admin to allow it, or rely on meetings and `#ledger` notes. |
| A prompt step fails with a license error | No AI Builder or Copilot credits in the environment. See Prerequisites. |
| `Ledger_rows` fails while parsing JSON | Confirm the daily prompt's Output is set to JSON and the temperature is 0.1. |
| Duplicate rows | Make sure Date is stored as text (the template already does this). Don't reformat the column. |
| Too much or too little detail | Adjust `maxSentEmails`, `maxChats` and `maxPayloadChars` in **Config**. |

## Customize

- **Capture time:** change the trigger recurrence (default 23:30, Arabian Standard Time).
- **Report day:** change the Weekly Digest trigger (default Friday 15:00).
- **Categories and levels:** edit `prompts/daily-extractor.md` and the dropdown values in `build/build_workbook.py`.
