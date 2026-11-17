#!/usr/bin/env python3
"""Builds template/WorkLedger.xlsx (empty, one example row) and samples/WorkLedger_SAMPLE.xlsx (demo week)."""
import os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import DataBarRule

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = "Arial"
HDR = Font(name=F, bold=True, color="FFFFFF"); HFILL = PatternFill("solid", fgColor="1F3864")
BODY = Font(name=F, size=10); BOLD = Font(name=F, size=10, bold=True)
TITLE = Font(name=F, size=16, bold=True, color="1F3864"); SUB = Font(name=F, size=10, italic=True, color="595959")
THIN = Border(bottom=Side(style="thin", color="D9D9D9"))
COLS = [("Date", 11), ("Week", 11), ("Source", 9), ("Time", 7), ("Title", 38), ("Summary", 60), ("Category", 14),
        ("Technologies", 30), ("Stakeholders", 26), ("EffortHours", 11), ("Complexity", 11), ("Level", 24),
        ("Impact", 50), ("Innovation", 11), ("Evidence", 36)]
CATS = ["Architecture", "Build", "Strategy", "Governance", "Innovation", "Integration", "Security", "Data/AI",
        "Stakeholder", "Delivery", "Support", "Learning"]
LEVELS = ["L1 Operational", "L2 Delivery", "L3 Solution Design", "L4 Enterprise Architecture", "L5 Strategic"]
TECHS = ["Java", "Spring Boot", "Oracle OIC", "Oracle ATP", "Oracle Fusion", "Oracle VBCS", "PL/SQL", "IBM APIC",
         "IBM ACE/ESB", "Dynamics 365", "Power Platform", "Power Automate", "Copilot Studio", "Microsoft 365 Copilot",
         "Azure OpenAI", "Azure", "SharePoint", "ISO 20022", "SWIFT", "FIRCO", "AML", "LangGraph", "Python",
         "Kubernetes", "Docker", "REST API", "Kafka", "Entra ID", "TOGAF", "ArchiMate"]
N = 5000  # formula range depth

def ledger_sheet(wb, rows):
    ws = wb.active; ws.title = "Ledger"
    for i, (c, w) in enumerate(COLS, 1):
        cell = ws.cell(1, i, c); cell.font = HDR; cell.fill = HFILL; cell.alignment = Alignment(vertical="center")
        ws.column_dimensions[cell.column_letter].width = w
    for r, row in enumerate(rows, 2):
        for i, v in enumerate(row, 1):
            c = ws.cell(r, i, v); c.font = BODY
            c.alignment = Alignment(wrap_text=i in (5, 6, 13), vertical="top")
            if i in (1, 2, 4): c.number_format = "@"
            if i == 10: c.number_format = "0.0"
    last = max(2, len(rows) + 1)
    t = Table(displayName="tblLedger", ref=f"A1:O{last}")
    t.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
    ws.add_table(t)
    ws.freeze_panes = "F2"
    for col in "ABD":
        for r in range(2, 300): ws[f"{col}{r}"].number_format = "@"
    dv1 = DataValidation(type="list", formula1='"' + ",".join(CATS) + '"', allow_blank=True); ws.add_data_validation(dv1); dv1.add(f"G2:G{N}")
    dv2 = DataValidation(type="list", formula1='"' + ",".join(LEVELS) + '"', allow_blank=True); ws.add_data_validation(dv2); dv2.add(f"L2:L{N}")
    ws.row_dimensions[1].height = 22

def rng(col): return f"Ledger!${col}$2:${col}${N}"

def dashboard(wb):
    ws = wb.create_sheet("Dashboard", 0)
    ws.column_dimensions["A"].width = 30; ws.column_dimensions["B"].width = 14; ws.column_dimensions["C"].width = 12
    ws.column_dimensions["D"].width = 4; ws.column_dimensions["E"].width = 28; ws.column_dimensions["F"].width = 14; ws.column_dimensions["G"].width = 12
    ws["A1"] = "Work Ledger — Impact Dashboard"; ws["A1"].font = TITLE
    ws["A2"] = "Auto-calculated from the Ledger tab. Do not edit this sheet."; ws["A2"].font = SUB
    kpis = [("Total effort (h)", f"=SUM({rng('J')})", "0.0"),
            ("Activities logged", f"=COUNTA({rng('E')})", "#,##0"),
            ("Days covered", f"=SUMPRODUCT(({rng('A')}<>\"\")/COUNTIF({rng('A')},{rng('A')}&\"\"))", "#,##0"),
            ("Innovation items", f"=COUNTIF({rng('N')},\"Yes\")", "#,##0"),
            ("Strategic share (L4–L5 hours)", f"=IFERROR((SUMIF({rng('L')},\"L4*\",{rng('J')})+SUMIF({rng('L')},\"L5*\",{rng('J')}))/SUM({rng('J')}),0)", "0.0%"),
            ("Avg complexity (1–5)", f"=IFERROR(AVERAGE({rng('K')}),0)", "0.0")]
    for i, (k, f, nf) in enumerate(kpis, 4):
        ws[f"A{i}"] = k; ws[f"A{i}"].font = BOLD; ws[f"B{i}"] = f; ws[f"B{i}"].number_format = nf; ws[f"B{i}"].font = Font(name=F, size=12, bold=True, color="1F3864")
    def block(r0, col_l, col_v, col_s, title, items, key_col, contains=False):
        ws[f"{col_l}{r0}"] = title; ws[f"{col_l}{r0}"].font = HDR; ws[f"{col_l}{r0}"].fill = HFILL
        ws[f"{col_v}{r0}"] = "Hours"; ws[f"{col_v}{r0}"].font = HDR; ws[f"{col_v}{r0}"].fill = HFILL
        ws[f"{col_s}{r0}"] = "Share"; ws[f"{col_s}{r0}"].font = HDR; ws[f"{col_s}{r0}"].fill = HFILL
        for j, it in enumerate(items, r0 + 1):
            ws[f"{col_l}{j}"] = it; ws[f"{col_l}{j}"].font = BODY
            crit = f"\"*\"&{col_l}{j}&\"*\"" if contains else f"{col_l}{j}"
            ws[f"{col_v}{j}"] = f"=SUMIF({rng(key_col)},{crit},{rng('J')})"; ws[f"{col_v}{j}"].number_format = "0.0"; ws[f"{col_v}{j}"].font = BODY
            ws[f"{col_s}{j}"] = f"=IFERROR({col_v}{j}/$B$4,0)"; ws[f"{col_s}{j}"].number_format = "0.0%"; ws[f"{col_s}{j}"].font = BODY
        end = r0 + len(items)
        ws.conditional_formatting.add(f"{col_v}{r0+1}:{col_v}{end}", DataBarRule(start_type="num", start_value=0, end_type="max", color="5B9BD5"))
    block(11, "A", "B", "C", "Effort by Level", LEVELS, "L")
    block(11, "E", "F", "G", "Effort by Category", CATS, "G")
    ws["A18"] = "Seniority reads as: L1 Operational → L5 Strategic. Effort = meeting minutes + AI-estimated email/chat effort."; ws["A18"].font = SUB

def radar(wb):
    ws = wb.create_sheet("Tech Radar", 1)
    ws["A1"] = "Technology Radar — where your effort actually goes"; ws["A1"].font = TITLE
    ws["A2"] = "Add any technology in column A (blue cells); hours and mentions recalculate automatically."; ws["A2"].font = SUB
    for c, h, w in [("A", "Technology", 26), ("B", "Hours", 10), ("C", "Mentions", 11), ("D", "Last used", 12)]:
        ws[f"{c}4"] = h; ws[f"{c}4"].font = HDR; ws[f"{c}4"].fill = HFILL; ws.column_dimensions[c].width = w
    for i, t in enumerate(TECHS, 5):
        ws[f"A{i}"] = t; ws[f"A{i}"].font = Font(name=F, size=10, color="0000FF")
        ws[f"B{i}"] = f"=SUMIF({rng('H')},\"*\"&A{i}&\"*\",{rng('J')})"; ws[f"B{i}"].number_format = "0.0"
        ws[f"C{i}"] = f"=COUNTIF({rng('H')},\"*\"&A{i}&\"*\")"
        ws[f"D{i}"] = f"=IFERROR(LOOKUP(2,1/ISNUMBER(SEARCH(A{i},{rng('H')})),{rng('A')}),\"—\")"
        for c in "BCD": ws[f"{c}{i}"].font = BODY
    end = 4 + len(TECHS) + 20
    for i in range(5 + len(TECHS), end + 1):
        ws[f"A{i}"].font = Font(name=F, size=10, color="0000FF")
        ws[f"B{i}"] = f"=IF(A{i}=\"\",\"\",SUMIF({rng('H')},\"*\"&A{i}&\"*\",{rng('J')}))"; ws[f"B{i}"].number_format = "0.0"
        ws[f"C{i}"] = f"=IF(A{i}=\"\",\"\",COUNTIF({rng('H')},\"*\"&A{i}&\"*\"))"
        ws[f"D{i}"] = f"=IF(A{i}=\"\",\"\",IFERROR(LOOKUP(2,1/ISNUMBER(SEARCH(A{i},{rng('H')})),{rng('A')}),\"—\"))"
    ws.conditional_formatting.add(f"B5:B{end}", DataBarRule(start_type="num", start_value=0, end_type="max", color="70AD47"))
    ws.freeze_panes = "A5"

def guide(wb):
    ws = wb.create_sheet("How it works")
    ws.column_dimensions["A"].width = 110
    lines = ["Work Ledger — how it works",
             "",
             "• The Ledger tab is filled AUTOMATICALLY every night at 23:30 (Dubai) by the 'Work Ledger - Daily Capture' flow.",
             "• Sources: your Sent Items, attended meetings (actual minutes), Teams chats you took part in, and any email you send yourself with '#ledger' in the subject.",
             "• Capture strategy thinking with zero effort: in Outlook mobile, new email to yourself → subject '#ledger strategy' → dictate by voice → send.",
             "• Every Friday at 15:00 you receive the weekly impact report by email ('Work Ledger - Weekly Digest').",
             "• Keep the table name 'tblLedger' and the column headers unchanged — the flows write to them by name.",
             "• Date and Week are stored as text (yyyy-MM-dd); Week = the Monday of that week.",
             "• You may edit any row (correct a level, add effort). Delete the example row in a new file once the first real day is captured.",
             "• Blue cells on Tech Radar are inputs: add technologies you want tracked.",
             "• Confidentiality: the AI is instructed never to record customer names, account/card numbers, IDs or secrets. Keep this file in your ADIB OneDrive only."]
    for i, l in enumerate(lines, 1):
        ws[f"A{i}"] = l; ws[f"A{i}"].font = TITLE if i == 1 else BODY; ws[f"A{i}"].alignment = Alignment(wrap_text=True)

EXAMPLE = [["2026-11-16", "2026-11-16", "Email", "09:12", "Example: designed approval-gated attachment sharing agent",
            "Designed and packaged a Power Automate agent that saves sandbox attachments, shares them read-only with the requester and replies after explicit approval.",
            "Innovation", "Power Automate, SharePoint, Copilot Studio", "EA team", 2.5, 3, "L3 Solution Design",
            "Removes a repetitive manual task while keeping human approval for every external share.", "Yes", "Sandbox Download Agent"]]

SAMPLE = [
 ["2026-11-16","2026-11-16","Meeting","09:00","Aligned ISO 20022 cut-over sequencing with Payments","Led the working session that agreed a phased MX cut-over for outbound pacs.008 flows, with coexistence handled in the ESB translation layer until the SWIFT deadline.","Architecture","ISO 20022, SWIFT, IBM ACE/ESB","Payments team, Operations",1.5,4,"L4 Enterprise Architecture","Unblocked the migration plan and avoided a big-bang cut-over risk.","No","ISO 20022 MX migration – cut-over"],
 ["2026-11-16","2026-11-16","Email","10:45","Rejected point-to-point CRM integration design","Returned the vendor design for rework, requiring APIC-mediated APIs and event-based sync instead of direct database links.","Governance","IBM APIC, Dynamics 365, Oracle ATP","Vendor – CRM, DRB",0.5,3,"L4 Enterprise Architecture","Prevented a non-compliant integration pattern from reaching SIT.","No","RE: MPM CRM integration – design v2"],
 ["2026-11-16","2026-11-16","Mixed","12:10","Fixed CBWSI log alert false positives","Tuned the CBWSI exception filter and alert thresholds with the support team after duplicate alerts on timeout retries.","Support","Java","Application support",0.8,2,"L2 Delivery","Reduced alert noise so on-call staff see only actionable failures.","No","CBWSI alert – duplicates"],
 ["2026-11-16","2026-11-16","Note","18:20","Proposed AI work-ledger for EA team effort visibility","Outlined a governed agent that auto-captures architects' email, meetings and chats into an effort and seniority ledger for capacity planning.","Innovation","Power Automate, Microsoft 365 Copilot, Excel","EA team, CIO office",0.5,3,"L5 Strategic","Creates objective evidence of architecture capacity and value for leadership.","Yes","#ledger strategy – EA visibility"],
 ["2026-11-17","2026-11-17","Meeting","10:00","Presented agent governance standard to Chief AI Officer","Walked through identity, DLP and human-in-the-loop controls for Copilot Studio agents and agreed a pilot scope.","Strategy","Copilot Studio, Entra ID, Power Platform","Chief AI Officer office",1.0,5,"L5 Strategic","Secured executive sponsorship for a governed agent pilot.","Yes","Agent Governance Standard – review"],
 ["2026-11-17","2026-11-17","Teams","11:30","Resolved OIC adapter timeout in SIT","Diagnosed the connection-pool exhaustion behind OIC REST adapter timeouts and agreed new pool and retry settings with the integration team.","Integration","Oracle OIC, REST API","Integration team",0.6,3,"L3 Solution Design","Restored the SIT test cycle without a schedule slip.","No","OIC SIT – timeouts"],
 ["2026-11-17","2026-11-17","Email","14:05","Drafted ADR for AI gateway placement","Authored an ADR that positions an AI gateway in front of Azure OpenAI for token quotas, PII redaction and audit logging.","Data/AI","Azure OpenAI, Azure","EA team, Security",1.2,4,"L4 Enterprise Architecture","Sets a reusable control point for every future GenAI workload.","Yes","ADR-031 AI Gateway"],
 ["2026-11-18","2026-11-18","Meeting","09:30","Reviewed FIRCO screening tuning results","Assessed false-positive reduction from the revised FIRCO fuzzy-match thresholds with Compliance and set the validation criteria.","Security","FIRCO, AML","Compliance",1.0,4,"L4 Enterprise Architecture","Lowered analyst workload while keeping regulatory risk within appetite.","No","FIRCO tuning – results"],
 ["2026-11-18","2026-11-18","Mixed","15:00","Built LangGraph triage prototype for SOC alerts","Built a working LangGraph prototype that enriches and prioritizes SOC alerts with retrieval over past incidents.","Innovation","LangGraph, Python, Azure OpenAI","Security operations",2.0,4,"L3 Solution Design","Shows a path to faster alert triage with explainable prioritization.","Yes","SOC triage agent – prototype"],
]

def build(path, rows):
    wb = Workbook(); ledger_sheet(wb, rows); dashboard(wb); radar(wb); guide(wb)
    for ws in wb.worksheets: ws.sheet_view.showGridLines = ws.title == "Ledger"
    wb.active = 0; wb.save(path); print("built", path)

build(os.path.join(ROOT, "template", "WorkLedger.xlsx"), EXAMPLE)
build(os.path.join(ROOT, "samples", "WorkLedger_SAMPLE.xlsx"), SAMPLE)
