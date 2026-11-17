#!/usr/bin/env python3
"""
Generates the Work Ledger Power Platform solution package.

Output:
  src/flows/WorkLedger-DailyCapture.json   (readable flow definition)
  src/flows/WorkLedger-WeeklyDigest.json   (readable flow definition)
  solution/WorkLedger_1_0_0_0.zip          (importable unmanaged solution)

Run:  python3 build/build_solution.py
Workflow IDs are stable (uuid5) so re-builds upgrade the same flows on import.
"""
import json
import os
import uuid
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NS = uuid.UUID("6f1c2a52-3d0e-4b1a-9a57-2b7f4c9e1d01")
TZ = "Arabian Standard Time"
PREFIX = "tj"

CONNECTORS = {
    "shared_office365": "Work Ledger - Office 365 Outlook",
    "shared_office365users": "Work Ledger - Office 365 Users",
    "shared_teams": "Work Ledger - Microsoft Teams",
    "shared_excelonlinebusiness": "Work Ledger - Excel Online (Business)",
    "shared_commondataserviceforapps": "Work Ledger - Dataverse (AI prompts)",
}
CR = {k: f"{PREFIX}_{k.replace('_', '')}_wl" for k in CONNECTORS}

AUTH = "@parameters('$authentication')"
RETRY = {"type": "exponential", "count": 4, "interval": "PT15S"}
ALWAYS = ["Succeeded", "Failed", "Skipped", "TimedOut"]
CFG = "outputs('Config')"


def host(api, op):
    return {"connectionName": api, "operationId": op,
            "apiId": f"/providers/Microsoft.PowerApps/apis/{api}"}


def conn(api, op, params, after, retry=True, **extra):
    a = {"runAfter": after, "type": "OpenApiConnection",
         "inputs": {"host": host(api, op), "parameters": params, "authentication": AUTH}}
    if retry:
        a["inputs"]["retryPolicy"] = RETRY
    a.update(extra)
    return a


def compose(value, after):
    return {"runAfter": after, "type": "Compose", "inputs": value}


def cap(expr, n):
    """Safe truncation: substring only when longer than n."""
    return f"if(greater(length(coalesce({expr},'')),{n}),substring({expr},0,{n}),coalesce({expr},''))"


def excel(op, extra, after):
    p = {"source": f"@{CFG}?['excelSource']", "drive": f"@{CFG}?['excelDriveId']",
         "file": f"@{CFG}?['excelFileId']", "table": "tblLedger"}
    p.update(extra)
    return conn("shared_excelonlinebusiness", op, p, after)


def notify(subject, body, after):
    return conn("shared_office365", "SendEmailV2", {
        "emailMessage/To": "@outputs('Me')?['mail']",
        "emailMessage/Subject": subject, "emailMessage/Body": body,
        "emailMessage/Importance": "High"}, after)


CONFIG = {
    "excelSource": "me",
    "excelDriveId": "REPLACE_WITH_DRIVE_ID",
    "excelFileId": "REPLACE_WITH_FILE_ID",
    "dailyPromptId": "REPLACE_WITH_DAILY_PROMPT_ID",
    "weeklyPromptId": "REPLACE_WITH_WEEKLY_PROMPT_ID",
    "maxSentEmails": 150,
    "maxChats": 25,
    "maxMessagesPerChat": 40,
    "maxPayloadChars": 90000,
    "noteSubjectTag": "#ledger",
}

COMMON_HEAD = {
    "Config": compose(CONFIG, {}),
    "Me": {"runAfter": {"Config": ["Succeeded"]}, "type": "Compose",
           "inputs": "@body('Get_my_profile')"},
    "Local_now": compose(f"@convertFromUtc(utcNow(),'{TZ}')", {"Config": ["Succeeded"]}),
}
COMMON_HEAD["Get_my_profile"] = conn("shared_office365users", "MyProfile_V2", {}, {"Config": ["Succeeded"]})
COMMON_HEAD["Me"]["runAfter"] = {"Get_my_profile": ["Succeeded"]}
WEEK_START = ("formatDateTime(addDays(outputs('Local_now'),mul(-1,mod(add(dayOfWeek(outputs('Local_now')),6),7))),"
              "'yyyy-MM-dd')")


# --------------------------------------------------------------------------- daily
def daily_flow():
    a = dict(COMMON_HEAD)
    a["Today"] = compose("@formatDateTime(outputs('Local_now'),'yyyy-MM-dd')", {"Local_now": ["Succeeded"]})
    a["Day_start_utc"] = compose(f"@convertToUtc(startOfDay(outputs('Local_now')),'{TZ}')", {"Today": ["Succeeded"]})
    a["Week_start"] = compose(f"@{WEEK_START}", {"Day_start_utc": ["Succeeded"]})

    a["Init_vars"] = {"runAfter": {"Week_start": ["Succeeded"]}, "type": "InitializeVariable", "inputs": {"variables": [
        {"name": "SentItems", "type": "array", "value": []},
        {"name": "Meetings", "type": "array", "value": []},
        {"name": "TeamsItems", "type": "array", "value": []},
        {"name": "Notes", "type": "array", "value": []}]}}

    # Idempotency: skip if today is already in the ledger
    a["Check_already_logged"] = excel("GetItems", {"$filter": "@concat('Date eq ''',outputs('Today'),'''')", "$top": 1},
                                      {"Init_vars": ["Succeeded"], "Me": ["Succeeded"]})
    gate_after = {"Check_already_logged": ["Succeeded"]}

    # ---- Source 1: sent email
    sent = {
        "Get_sent_items": conn("shared_office365", "GetEmailsV3", {
            "folderPath": "SentItems", "importance": "Any", "fetchOnlyWithAttachment": False,
            "includeAttachments": False, "top": f"@{CFG}?['maxSentEmails']"}, {}),
        "Sent_today": {"runAfter": {"Get_sent_items": ["Succeeded"]}, "type": "Query", "inputs": {
            "from": "@coalesce(body('Get_sent_items')?['value'],json('[]'))",
            "where": "@greaterOrEquals(ticks(item()?['receivedDateTime']),ticks(outputs('Day_start_utc')))"}},
        "Sent_shaped": {"runAfter": {"Sent_today": ["Succeeded"]}, "type": "Select", "inputs": {
            "from": "@body('Sent_today')",
            "select": {
                "time": f"@formatDateTime(convertFromUtc(item()?['receivedDateTime'],'{TZ}'),'HH:mm')",
                "subject": "@item()?['subject']",
                "to": "@item()?['toRecipients']", "cc": "@item()?['ccRecipients']",
                "hasAttachments": "@item()?['hasAttachments']",
                "preview": "@item()?['bodyPreview']"}}},
        "Sent_clean": {"runAfter": {"Sent_shaped": ["Succeeded"]}, "type": "Query", "inputs": {
            "from": "@body('Sent_shaped')",
            "where": "@not(or(startsWith(coalesce(item()?['subject'],''),'Accepted:'),startsWith(coalesce(item()?['subject'],''),'Declined:'),startsWith(coalesce(item()?['subject'],''),'Tentative:'),startsWith(coalesce(item()?['subject'],''),'Automatic reply')))"}},
        "Set_sent": {"runAfter": {"Sent_clean": ["Succeeded"]}, "type": "SetVariable",
                     "inputs": {"name": "SentItems", "value": "@body('Sent_clean')"}},
    }
    a["Collect_sent_email"] = {"runAfter": gate_after, "type": "Scope", "actions": sent}

    # ---- Source 2: meetings (real effort data)
    mtg = {
        "Get_today_events": conn("shared_office365", "GetEventsCalendarViewV3", {
            "calendarId": "Calendar",
            "startDateTimeOffset": "@outputs('Day_start_utc')",
            "endDateTimeOffset": "@addDays(outputs('Day_start_utc'),1)"}, {}),
        "Attended_events": {"runAfter": {"Get_today_events": ["Succeeded"]}, "type": "Query", "inputs": {
            "from": "@coalesce(body('Get_today_events')?['value'],json('[]'))",
            "where": "@and(not(equals(item()?['isAllDay'],true)),not(equals(toLower(coalesce(item()?['responseType'],'')),'declined')),not(equals(item()?['showAs'],'free')))"}},
        "Meetings_shaped": {"runAfter": {"Attended_events": ["Succeeded"]}, "type": "Select", "inputs": {
            "from": "@body('Attended_events')",
            "select": {
                "start": f"@formatDateTime(convertFromUtc(item()?['start'],'{TZ}'),'HH:mm')",
                "minutes": "@div(sub(ticks(item()?['end']),ticks(item()?['start'])),600000000)",
                "subject": "@item()?['subject']",
                "organizer": "@item()?['organizer']",
                "attendees": "@item()?['requiredAttendees']",
                "agenda": "@" + cap("item()?['bodyPreview']", 400)}}},
        "Set_meetings": {"runAfter": {"Meetings_shaped": ["Succeeded"]}, "type": "SetVariable",
                         "inputs": {"name": "Meetings", "value": "@body('Meetings_shaped')"}},
    }
    a["Collect_meetings"] = {"runAfter": gate_after, "type": "Scope", "actions": mtg}

    # ---- Source 3: Teams chats (Graph via Teams connector, delegated)
    teams = {
        "List_recent_chats": conn("shared_teams", "HttpRequest", {
            "Uri": f"@concat('https://graph.microsoft.com/v1.0/me/chats?$expand=lastMessagePreview&$top=',string({CFG}?['maxChats']))",
            "Method": "GET", "ContentType": "application/json"}, {}),
        "Chats_active_today": {"runAfter": {"List_recent_chats": ["Succeeded"]}, "type": "Query", "inputs": {
            "from": "@coalesce(body('List_recent_chats')?['value'],json('[]'))",
            "where": "@greaterOrEquals(ticks(coalesce(item()?['lastMessagePreview']?['createdDateTime'],'1900-01-01T00:00:00Z')),ticks(outputs('Day_start_utc')))"}},
        "For_each_active_chat": {"runAfter": {"Chats_active_today": ["Succeeded"]}, "type": "Foreach",
            "foreach": "@body('Chats_active_today')",
            "runtimeConfiguration": {"concurrency": {"repetitions": 5}},
            "actions": {
                "Get_chat_messages": conn("shared_teams", "HttpRequest", {
                    "Uri": f"@concat('https://graph.microsoft.com/v1.0/chats/',items('For_each_active_chat')?['id'],'/messages?$top=',string({CFG}?['maxMessagesPerChat']))",
                    "Method": "GET", "ContentType": "application/json"}, {}),
                "Messages_today": {"runAfter": {"Get_chat_messages": ["Succeeded"]}, "type": "Query", "inputs": {
                    "from": "@coalesce(body('Get_chat_messages')?['value'],json('[]'))",
                    "where": "@and(equals(item()?['messageType'],'message'),greaterOrEquals(ticks(item()?['createdDateTime']),ticks(outputs('Day_start_utc'))))"}},
                "Messages_shaped": {"runAfter": {"Messages_today": ["Succeeded"]}, "type": "Select", "inputs": {
                    "from": "@body('Messages_today')",
                    "select": {
                        "fromMe": "@equals(item()?['from']?['user']?['id'],outputs('Me')?['id'])",
                        "time": f"@formatDateTime(convertFromUtc(item()?['createdDateTime'],'{TZ}'),'HH:mm')",
                        "text": "@" + cap("item()?['body']?['content']", 500)}}},
                "Add_chat_if_I_participated": {"runAfter": {"Messages_shaped": ["Succeeded"]}, "type": "If",
                    "expression": {"and": [{"contains": ["@string(body('Messages_shaped'))", "\"fromMe\":true"]}]},
                    "actions": {"Append_chat": {"runAfter": {}, "type": "AppendToArrayVariable", "inputs": {
                        "name": "TeamsItems",
                        "value": {"chat": "@coalesce(items('For_each_active_chat')?['topic'],items('For_each_active_chat')?['chatType'])",
                                  "messages": "@body('Messages_shaped')"}}}},
                    "else": {"actions": {}}}}},
    }
    a["Collect_teams"] = {"runAfter": gate_after, "type": "Scope", "actions": teams}

    # ---- Source 4: notes / voice dictation emailed to self with #ledger
    notes = {
        "Get_ledger_notes": conn("shared_office365", "GetEmailsV3", {
            "folderPath": "Inbox", "subjectFilter": f"@{CFG}?['noteSubjectTag']", "importance": "Any",
            "fetchOnlyWithAttachment": False, "includeAttachments": False, "top": 25}, {}),
        "Notes_today": {"runAfter": {"Get_ledger_notes": ["Succeeded"]}, "type": "Query", "inputs": {
            "from": "@coalesce(body('Get_ledger_notes')?['value'],json('[]'))",
            "where": "@greaterOrEquals(ticks(item()?['receivedDateTime']),ticks(outputs('Day_start_utc')))"}},
        "Notes_shaped": {"runAfter": {"Notes_today": ["Succeeded"]}, "type": "Select", "inputs": {
            "from": "@body('Notes_today')",
            "select": {"subject": "@item()?['subject']", "note": "@" + cap("item()?['body']", 3000)}}},
        "Set_notes": {"runAfter": {"Notes_shaped": ["Succeeded"]}, "type": "SetVariable",
                      "inputs": {"name": "Notes", "value": "@body('Notes_shaped')"}},
    }
    a["Collect_notes"] = {"runAfter": gate_after, "type": "Scope", "actions": notes}

    collected = {k: ALWAYS for k in ["Collect_sent_email", "Collect_meetings", "Collect_teams", "Collect_notes"]}

    a["Activity_payload"] = compose({
        "date": "@outputs('Today')",
        "owner": "@outputs('Me')?['displayName']",
        "ownerTitle": "@outputs('Me')?['jobTitle']",
        "sentEmails": "@variables('SentItems')",
        "meetings": "@variables('Meetings')",
        "teamsChats": "@variables('TeamsItems')",
        "personalNotes": "@variables('Notes')",
        "sourceHealth": {
            "email": "@result('Collect_sent_email')?[0]?['status']",
            "meetings": "@result('Collect_meetings')?[0]?['status']",
            "teams": "@result('Collect_teams')?[0]?['status']",
            "notes": "@result('Collect_notes')?[0]?['status']"}},
        collected)
    a["Payload_text"] = compose("@" + cap("string(outputs('Activity_payload'))", "outputs('Config')?['maxPayloadChars']"),
                                {"Activity_payload": ["Succeeded"]})
    a["Has_activity"] = compose(
        "@greater(add(add(length(variables('SentItems')),length(variables('Meetings'))),add(length(variables('TeamsItems')),length(variables('Notes')))),0)",
        {"Payload_text": ["Succeeded"]})

    process = {
        "Run_daily_extractor_prompt": conn("shared_commondataserviceforapps", "aibuilderpredict_customprompt", {
            "recordId": f"@{CFG}?['dailyPromptId']",
            "item/requestv2/ActivityData": "@outputs('Payload_text')"}, {}, retry=True),
        "Ledger_rows": compose(
            "@json(trim(replace(replace(body('Run_daily_extractor_prompt')?['responsev2']?['predictionOutput']?['text'],'```json',''),'```','')))",
            {"Run_daily_extractor_prompt": ["Succeeded"]}),
        "Write_rows": {"runAfter": {"Ledger_rows": ["Succeeded"]}, "type": "Foreach",
            "foreach": "@coalesce(outputs('Ledger_rows')?['rows'],json('[]'))",
            "runtimeConfiguration": {"concurrency": {"repetitions": 1}},
            "actions": {"Add_ledger_row": excel("AddRowV2", {"item": {
                "Date": "@outputs('Today')",
                "Week": "@outputs('Week_start')",
                "Source": "@items('Write_rows')?['source']",
                "Time": "@items('Write_rows')?['time']",
                "Title": "@items('Write_rows')?['title']",
                "Summary": "@items('Write_rows')?['summary']",
                "Category": "@items('Write_rows')?['category']",
                "Technologies": "@join(coalesce(items('Write_rows')?['technologies'],json('[]')),', ')",
                "Stakeholders": "@join(coalesce(items('Write_rows')?['stakeholders'],json('[]')),', ')",
                "EffortHours": "@items('Write_rows')?['effortHours']",
                "Complexity": "@items('Write_rows')?['complexity']",
                "Level": "@items('Write_rows')?['level']",
                "Impact": "@items('Write_rows')?['impact']",
                "Innovation": "@if(equals(items('Write_rows')?['isInnovation'],true),'Yes','No')",
                "Evidence": "@items('Write_rows')?['evidence']"}}, {})}},
    }
    a["Process_day"] = {"runAfter": {"Has_activity": ["Succeeded"]}, "type": "If",
        "expression": {"and": [
            {"equals": ["@length(coalesce(body('Check_already_logged')?['value'],json('[]')))", 0]},
            {"equals": ["@outputs('Has_activity')", True]}]},
        "actions": {
            "Process": {"runAfter": {}, "type": "Scope", "actions": process},
            "Notify_failure": notify("Work Ledger: daily capture FAILED @{outputs('Today')}",
                "<p>Daily capture failed. Source status: @{string(outputs('Activity_payload')?['sourceHealth'])}</p><p>Run: @{workflow()?['run']?['name']}</p>",
                {"Process": ["Failed", "TimedOut"]}),
            "Fail_run": {"runAfter": {"Notify_failure": ["Succeeded", "Failed"]}, "type": "Terminate",
                         "inputs": {"runStatus": "Failed", "runError": {"code": "LedgerCaptureFailed", "message": "See notification email"}}}},
        "else": {"actions": {"Nothing_to_log": {"runAfter": {}, "type": "Terminate", "inputs": {"runStatus": "Succeeded"}}}}}

    trigger = {"Every_night_2330_Dubai": {"type": "Recurrence", "recurrence": {
        "frequency": "Day", "interval": 1, "timeZone": TZ,
        "schedule": {"hours": ["23"], "minutes": [30]}}}}
    return wrap(trigger, a)


# --------------------------------------------------------------------------- weekly
def weekly_flow():
    a = dict(COMMON_HEAD)
    a["Week_start"] = compose(f"@{WEEK_START}", {"Local_now": ["Succeeded"]})
    a["Get_week_rows"] = excel("GetItems", {"$filter": "@concat('Week eq ''',outputs('Week_start'),'''')", "$top": 2000},
                               {"Week_start": ["Succeeded"], "Me": ["Succeeded"]})
    a["Week_rows"] = compose("@coalesce(body('Get_week_rows')?['value'],json('[]'))", {"Get_week_rows": ["Succeeded"]})
    report = {
        "Run_weekly_report_prompt": conn("shared_commondataserviceforapps", "aibuilderpredict_customprompt", {
            "recordId": f"@{CFG}?['weeklyPromptId']",
            "item/requestv2/WeekData": "@concat('Owner: ',outputs('Me')?['displayName'],' (',outputs('Me')?['jobTitle'],'). Week starting ',outputs('Week_start'),'. Rows: ',string(outputs('Week_rows')))"}, {}),
        "Send_weekly_report": conn("shared_office365", "SendEmailV2", {
            "emailMessage/To": "@outputs('Me')?['mail']",
            "emailMessage/Subject": "Work Ledger | Week of @{outputs('Week_start')} | @{string(length(outputs('Week_rows')))} activities",
            "emailMessage/Body": "@body('Run_weekly_report_prompt')?['responsev2']?['predictionOutput']?['text']",
            "emailMessage/Importance": "Normal"}, {"Run_weekly_report_prompt": ["Succeeded"]}),
    }
    a["Has_rows"] = {"runAfter": {"Week_rows": ["Succeeded"]}, "type": "If",
        "expression": {"and": [{"greater": ["@length(outputs('Week_rows'))", 0]}]},
        "actions": {
            "Report": {"runAfter": {}, "type": "Scope", "actions": report},
            "Notify_failure": notify("Work Ledger: weekly digest FAILED",
                "<p>Weekly digest failed for week @{outputs('Week_start')}. Run: @{workflow()?['run']?['name']}</p>",
                {"Report": ["Failed", "TimedOut"]})},
        "else": {"actions": {}}}
    trigger = {"Every_Friday_1500_Dubai": {"type": "Recurrence", "recurrence": {
        "frequency": "Week", "interval": 1, "timeZone": TZ,
        "schedule": {"weekDays": ["Friday"], "hours": ["15"], "minutes": [0]}}}}
    return wrap(trigger, a)


def wrap(trigger, actions):
    used = sorted({v["inputs"]["host"]["connectionName"] for v in walk(actions)})
    return {"properties": {
        "connectionReferences": {k: {"runtimeSource": "embedded",
                                     "connection": {"connectionReferenceLogicalName": CR[k]},
                                     "api": {"name": k}} for k in used},
        "definition": {
            "$schema": "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#",
            "contentVersion": "1.0.0.0",
            "parameters": {"$connections": {"defaultValue": {}, "type": "Object"},
                           "$authentication": {"defaultValue": {}, "type": "SecureObject"}},
            "triggers": trigger, "actions": actions},
        "templateName": ""}, "schemaVersion": "1.0.0.0"}


def walk(actions):
    for v in actions.values():
        if v.get("type") == "OpenApiConnection":
            yield v
        for key in ("actions",):
            if key in v:
                yield from walk(v[key])
        if "else" in v:
            yield from walk(v["else"].get("actions", {}))


# --------------------------------------------------------------------------- package
FLOWS = [("WorkLedger-DailyCapture", "Work Ledger - Daily Capture", daily_flow,
          "Nightly: reads sent email, meetings, Teams chats and #ledger notes; AI scores effort, level and impact; writes to WorkLedger.xlsx."),
         ("WorkLedger-WeeklyDigest", "Work Ledger - Weekly Digest", weekly_flow,
          "Friday: summarizes the week from WorkLedger.xlsx into an executive impact report emailed to the owner.")]


def workflow_xml(wid, name, json_path, desc):
    return f"""    <Workflow WorkflowId="{{{wid}}}" Name="{name}">
      <JsonFileName>/{json_path}</JsonFileName>
      <Type>1</Type>
      <Subprocess>0</Subprocess>
      <Category>5</Category>
      <Mode>0</Mode>
      <Scope>4</Scope>
      <OnDemand>0</OnDemand>
      <TriggerOnCreate>0</TriggerOnCreate>
      <TriggerOnDelete>0</TriggerOnDelete>
      <AsyncAutodelete>0</AsyncAutodelete>
      <SyncWorkflowLogOnFailure>0</SyncWorkflowLogOnFailure>
      <StateCode>0</StateCode>
      <StatusCode>1</StatusCode>
      <RunAs>1</RunAs>
      <IsTransacted>1</IsTransacted>
      <IntroducedVersion>1.0.0.0</IntroducedVersion>
      <IsCustomizable>1</IsCustomizable>
      <BusinessProcessType>0</BusinessProcessType>
      <IsCustomProcessingStepAllowedForOtherPublishers>1</IsCustomProcessingStepAllowedForOtherPublishers>
      <PrimaryEntity>none</PrimaryEntity>
      <LocalizedNames>
        <LocalizedName languagecode="1033" description="{name}" />
      </LocalizedNames>
      <Descriptions>
        <Description languagecode="1033" description="{desc}" />
      </Descriptions>
    </Workflow>
"""


NIL_ADDR = "".join(f"<{t} xsi:nil=\"true\"></{t}>" for t in [
    "City", "County", "Country", "Fax", "FreightTermsCode", "ImportSequenceNumber", "Latitude", "Line1", "Line2",
    "Line3", "Longitude", "Name", "PostalCode", "PostOfficeBox", "PrimaryContactName"])
NIL_ADDR2 = "".join(f"<{t} xsi:nil=\"true\"></{t}>" for t in [
    "StateOrProvince", "Telephone1", "Telephone2", "Telephone3", "TimeZoneRuleVersionNumber", "UPSZone",
    "UTCOffset", "UTCConversionTimeZoneCode"])


def address(n):
    return (f"<Address><AddressNumber>{n}</AddressNumber><AddressTypeCode>1</AddressTypeCode>{NIL_ADDR}"
            f"<ShippingMethodCode>1</ShippingMethodCode>{NIL_ADDR2}</Address>")


def main():
    files, wf_xml, roots = {}, "", ""
    for slug, name, fn, desc in FLOWS:
        wid = str(uuid.uuid5(NS, slug))
        definition = fn()
        with open(os.path.join(ROOT, "src", "flows", f"{slug}.json"), "w") as f:
            json.dump(definition, f, indent=2)
        path = f"Workflows/{slug.replace('-', '')}-{wid.upper()}.json"
        files[path] = json.dumps(definition, indent=2)
        wf_xml += workflow_xml(wid, name, path, desc)
        roots += f'      <RootComponent type="29" id="{{{wid}}}" behavior="0" />\n'

    crs = "".join(f"""
    <connectionreference connectionreferencelogicalname="{CR[k]}">
      <connectionreferencedisplayname>{v}</connectionreferencedisplayname>
      <connectorid>/providers/Microsoft.PowerApps/apis/{k}</connectorid>
      <iscustomizable>1</iscustomizable>
      <statecode>0</statecode>
      <statuscode>1</statuscode>
    </connectionreference>""" for k, v in CONNECTORS.items())

    ver = 'OrganizationVersion="9.2.25101.180" OrganizationSchemaType="Standard" CRMServerServiceabilityVersion="9.2.25101.00180"'
    files["customizations.xml"] = f"""<?xml version="1.0" encoding="utf-8"?>
<ImportExportXml xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" {ver}>
  <Entities />
  <Roles />
  <Workflows>
{wf_xml}  </Workflows>
  <FieldSecurityProfiles />
  <Templates />
  <EntityMaps />
  <EntityRelationships />
  <OrganizationSettings />
  <optionsets />
  <CustomControls />
  <EntityDataProviders />
  <connectionreferences>{crs}
  </connectionreferences>
  <Languages>
    <Language>1033</Language>
  </Languages>
</ImportExportXml>
"""
    files["solution.xml"] = f"""<?xml version="1.0" encoding="utf-8"?>
<ImportExportXml version="9.2.25101.180" SolutionPackageVersion="9.2" languagecode="1033" generatedBy="CrmLive" {ver} xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <SolutionManifest>
    <UniqueName>WorkLedger</UniqueName>
    <LocalizedNames>
      <LocalizedName description="Work Ledger" languagecode="1033" />
    </LocalizedNames>
    <Descriptions />
    <Version>1.0.0.0</Version>
    <Managed>0</Managed>
    <Publisher>
      <UniqueName>tajudeenj</UniqueName>
      <LocalizedNames>
        <LocalizedName description="Tajudeen Jalaudin" languagecode="1033" />
      </LocalizedNames>
      <Descriptions />
      <EMailAddress xsi:nil="true"></EMailAddress>
      <SupportingWebsiteUrl xsi:nil="true"></SupportingWebsiteUrl>
      <CustomizationPrefix>{PREFIX}</CustomizationPrefix>
      <CustomizationOptionValuePrefix>47600</CustomizationOptionValuePrefix>
      <Addresses>{address(1)}{address(2)}</Addresses>
    </Publisher>
    <RootComponents>
{roots}    </RootComponents>
    <MissingDependencies />
  </SolutionManifest>
</ImportExportXml>
"""
    files["[Content_Types].xml"] = ('<?xml version="1.0" encoding="utf-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                                    '<Default Extension="xml" ContentType="application/octet-stream" />'
                                    '<Default Extension="json" ContentType="application/octet-stream" /></Types>')
    out = os.path.join(ROOT, "solution", "WorkLedger_1_0_0_0.zip")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for n in ["[Content_Types].xml", "solution.xml", "customizations.xml"] + [p for p in files if p.startswith("Workflows/")]:
            z.writestr(n, files[n])
    print("built", out)


if __name__ == "__main__":
    main()
