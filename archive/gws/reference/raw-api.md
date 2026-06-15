# Raw API Patterns

Advanced usage for when helpers don't cover your use case.

## Command Structure

```
gws <service> <resource> <method> --params '<JSON>' --json '<JSON>'
```

- `--params` → URL/query parameters (GET params, resource IDs)
- `--json` → Request body (POST/PATCH/PUT payloads)

## Pagination

```bash
# Auto-paginate all results (NDJSON output)
gws drive files list --params '{"pageSize":100}' --page-all

# Limit pages
gws drive files list --params '{"pageSize":100}' --page-all --page-limit 5

# Manual pagination
gws drive files list --params '{"pageSize":10,"pageToken":"NEXT_PAGE_TOKEN"}'
```

## File Upload (Multipart)

```bash
# Upload with metadata
gws drive files create \
  --json '{"name":"report.pdf","parents":["FOLDER_ID"]}' \
  --upload ./report.pdf

# Upload with explicit content type
gws drive files create \
  --json '{"name":"data.csv"}' \
  --upload ./data.csv \
  --upload-content-type text/csv
```

## File Download

```bash
# Download binary content
gws drive files get --params '{"fileId":"FILE_ID","alt":"media"}' --output ./file.pdf

# Export Google Doc as PDF
gws drive files export --params '{"fileId":"DOC_ID","mimeType":"application/pdf"}' --output ./doc.pdf

# Export Google Sheet as CSV
gws drive files export --params '{"fileId":"SHEET_ID","mimeType":"text/csv"}' --output ./data.csv
```

## Batch Operations (Sheets)

```bash
# Batch update spreadsheet (formatting, merges, etc.)
gws sheets spreadsheets batchUpdate --params '{"spreadsheetId":"SHEET_ID"}' \
  --json '{
    "requests": [
      {"updateCells": {"range": {"sheetId": 0, "startRowIndex": 0, "endRowIndex": 1}, "fields": "userEnteredFormat.textFormat.bold", "rows": [{"values": [{"userEnteredFormat": {"textFormat": {"bold": true}}}]}]}}
    ]
  }'
```

## Docs Batch Update

```bash
# Insert text at a specific index
gws docs documents batchUpdate --params '{"documentId":"DOC_ID"}' \
  --json '{
    "requests": [
      {"insertText": {"location": {"index": 1}, "text": "Hello world\n"}}
    ]
  }'
```

## Gmail Search Operators

Use in `--params '{"q":"..."}'` or `+triage --query '...'`:

| Operator | Example |
|----------|---------|
| `from:` | `from:alice@example.com` |
| `to:` | `to:team@example.com` |
| `subject:` | `subject:invoice` |
| `has:attachment` | Messages with attachments |
| `filename:` | `filename:pdf` |
| `after:` / `before:` | `after:2026/01/01 before:2026/04/01` |
| `is:unread` | Unread messages |
| `label:` | `label:important` |
| `larger:` / `smaller:` | `larger:5M` |

Combine with AND (space), OR, `-` (NOT): `from:boss subject:urgent -is:read`

## Drive Search Operators

Use in `--params '{"q":"..."}'`:

```bash
# By MIME type
gws drive files list --params '{"q":"mimeType=\"application/pdf\""}'

# By name
gws drive files list --params '{"q":"name contains \"report\""}'

# In specific folder
gws drive files list --params '{"q":"\"FOLDER_ID\" in parents"}'

# Modified recently
gws drive files list --params '{"q":"modifiedTime > \"2026-04-01T00:00:00\""}'

# Combine conditions
gws drive files list --params '{"q":"mimeType=\"application/pdf\" and name contains \"invoice\""}'
```

## Calendar Event Creation (Raw)

```bash
gws calendar events insert --params '{"calendarId":"primary"}' \
  --json '{
    "summary": "Team Sync",
    "description": "Weekly team sync meeting",
    "start": {"dateTime": "2026-04-05T10:00:00", "timeZone": "America/Denver"},
    "end": {"dateTime": "2026-04-05T11:00:00", "timeZone": "America/Denver"},
    "attendees": [{"email": "alice@example.com"}, {"email": "bob@example.com"}],
    "reminders": {"useDefault": false, "overrides": [{"method": "popup", "minutes": 10}]}
  }'
```

## Error Handling

| Exit Code | Meaning | Recovery |
|-----------|---------|----------|
| 0 | Success | — |
| 1 | API error | Check Google's error message in response |
| 2 | Auth error | Run `gws auth login` |
| 3 | Validation | Fix arguments/input |
| 4 | Discovery | Check service/resource name spelling |
| 5 | Internal | Report as bug |

## Schema Discovery

```bash
# Explore what parameters a method accepts
gws schema drive.files.list
gws schema gmail.users.messages.send

# Resolve nested types (see full request/response shapes)
gws schema calendar.events.insert --resolve-refs
```
