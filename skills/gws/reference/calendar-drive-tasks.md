# Calendar, Drive & Tasks

## Calendar

### View Events

```bash
# Today
gws calendar +agenda --today --format table

# This week
gws calendar +agenda --week --format table

# Specific calendar
gws calendar +agenda --today --calendar 'Work' --format table

# Next N days
gws calendar +agenda --days 3 --format table
```

### Create Events

```bash
# Quick: helper command
gws calendar +insert --summary 'Dentist' --start '2026-04-05T10:00:00' --end '2026-04-05T11:00:00'

# Full: with attendees, location, reminders
gws calendar events insert --params '{"calendarId":"primary"}' \
  --json '{
    "summary": "Team Lunch",
    "location": "Downtown Cafe",
    "description": "Monthly team lunch",
    "start": {"dateTime": "2026-04-05T12:00:00", "timeZone": "America/Denver"},
    "end": {"dateTime": "2026-04-05T13:00:00", "timeZone": "America/Denver"},
    "attendees": [{"email": "friend@gmail.com"}],
    "reminders": {"useDefault": false, "overrides": [{"method": "popup", "minutes": 30}]}
  }'

# All-day event
gws calendar events insert --params '{"calendarId":"primary"}' \
  --json '{
    "summary": "Mom Birthday",
    "start": {"date": "2026-05-15"},
    "end": {"date": "2026-05-16"}
  }'
```

### Update Events

```bash
# Change event time
gws calendar events patch --params '{"calendarId":"primary","eventId":"EVENT_ID"}' \
  --json '{"start":{"dateTime":"2026-04-05T14:00:00","timeZone":"America/Denver"},"end":{"dateTime":"2026-04-05T15:00:00","timeZone":"America/Denver"}}'

# Change title
gws calendar events patch --params '{"calendarId":"primary","eventId":"EVENT_ID"}' \
  --json '{"summary":"New Title"}'
```

### Delete Events

```bash
gws calendar events delete --params '{"calendarId":"primary","eventId":"EVENT_ID"}'
```

### List Calendars

```bash
gws calendar calendarList list --format table
```

## Drive

### Find Files

```bash
# Recent files
gws drive files list --params '{"pageSize":10,"orderBy":"modifiedTime desc"}' --format table

# Search by name
gws drive files list --params '{"q":"name contains \"tax\""}' --format table

# Find PDFs
gws drive files list --params '{"q":"mimeType=\"application/pdf\""}' --format table

# Find in specific folder
gws drive files list --params '{"q":"\"FOLDER_ID\" in parents"}' --format table

# Find shared with me
gws drive files list --params '{"q":"sharedWithMe=true","pageSize":10}' --format table

# Find large files (sort by size)
gws drive files list --params '{"pageSize":20,"orderBy":"quotaBytesUsed desc","fields":"files(id,name,size,mimeType,modifiedTime)"}' --format table
```

### Upload and Download

```bash
# Upload
gws drive +upload ./photo.jpg
gws drive +upload ./report.pdf --parent FOLDER_ID
gws drive +upload ./data.csv --name 'Budget 2026.csv'

# Download
gws drive files get --params '{"fileId":"FILE_ID","alt":"media"}' --output ./downloaded.pdf

# Export Google Doc as PDF
gws drive files export --params '{"fileId":"DOC_ID","mimeType":"application/pdf"}' --output ./doc.pdf

# Export Google Sheet as CSV
gws drive files export --params '{"fileId":"SHEET_ID","mimeType":"text/csv"}' --output ./data.csv
```

### Organize Files

```bash
# Create folder
gws drive files create --json '{"name":"Tax Documents","mimeType":"application/vnd.google-apps.folder"}'

# Create subfolder
gws drive files create --json '{"name":"2026","mimeType":"application/vnd.google-apps.folder","parents":["PARENT_FOLDER_ID"]}'

# Move file to folder
gws drive files update --params '{"fileId":"FILE_ID","addParents":"FOLDER_ID","removeParents":"OLD_PARENT_ID"}'

# Rename file
gws drive files update --params '{"fileId":"FILE_ID"}' --json '{"name":"New Name.pdf"}'

# Trash a file (recoverable)
gws drive files update --params '{"fileId":"FILE_ID"}' --json '{"trashed":true}'

# Permanently delete (careful!)
gws drive files delete --params '{"fileId":"FILE_ID"}'
```

### Sharing

```bash
# Share with someone (editor)
gws drive permissions create --params '{"fileId":"FILE_ID"}' \
  --json '{"role":"writer","type":"user","emailAddress":"friend@gmail.com"}'

# Share read-only
gws drive permissions create --params '{"fileId":"FILE_ID"}' \
  --json '{"role":"reader","type":"user","emailAddress":"friend@gmail.com"}'

# Share via link (anyone with link can view)
gws drive permissions create --params '{"fileId":"FILE_ID"}' \
  --json '{"role":"reader","type":"anyone"}'

# See who has access
gws drive permissions list --params '{"fileId":"FILE_ID"}' --format table

# Remove someone's access
gws drive permissions delete --params '{"fileId":"FILE_ID","permissionId":"PERMISSION_ID"}'
```

### Drive Cleanup Guide

When the user wants to clean up Drive:

1. **Find large files**: Sort by size, review what's eating storage
2. **Find old files**: Modified more than a year ago, probably stale
3. **Find duplicates**: Search by name patterns
4. **Review shared files**: Files shared externally that shouldn't be
5. **Organize into folders**: Create a folder structure, move files

```bash
# Storage hogs
gws drive files list --params '{"pageSize":20,"orderBy":"quotaBytesUsed desc","fields":"files(id,name,size,mimeType)"}' --format table

# Old files
gws drive files list --params '{"q":"modifiedTime < \"2025-01-01\"","pageSize":20}' --format table

# Files shared externally
gws drive files list --params '{"q":"sharedWithMe=false and visibility=\"anyoneWithLink\"","pageSize":20}' --format table
```

## Tasks

### View Tasks

```bash
# List task lists
gws tasks tasklists list --format table

# Show tasks in default list
gws tasks tasks list --params '{"tasklist":"@default","showCompleted":false}' --format table

# Show all tasks including completed
gws tasks tasks list --params '{"tasklist":"@default"}' --format table
```

### Create Tasks

```bash
# Simple task
gws tasks tasks insert --params '{"tasklist":"@default"}' \
  --json '{"title":"Call dentist"}'

# Task with notes and due date
gws tasks tasks insert --params '{"tasklist":"@default"}' \
  --json '{"title":"Pay rent","notes":"Transfer to landlord","due":"2026-04-01T00:00:00.000Z"}'

# Create a task list
gws tasks tasklists insert --json '{"title":"Shopping List"}'
```

### Update Tasks

```bash
# Mark complete
gws tasks tasks patch --params '{"tasklist":"@default","task":"TASK_ID"}' \
  --json '{"status":"completed"}'

# Update title
gws tasks tasks patch --params '{"tasklist":"@default","task":"TASK_ID"}' \
  --json '{"title":"New title"}'

# Add due date
gws tasks tasks patch --params '{"tasklist":"@default","task":"TASK_ID"}' \
  --json '{"due":"2026-04-10T00:00:00.000Z"}'
```

### Delete Tasks

```bash
gws tasks tasks delete --params '{"tasklist":"@default","task":"TASK_ID"}'
```

## Cross-Service Workflows

```bash
# Morning briefing: today's meetings + tasks
gws workflow +standup-report --format table

# Prep for next meeting
gws workflow +meeting-prep

# Turn email into task
gws workflow +email-to-task --message-id MSG_ID

# Week overview
gws workflow +weekly-digest --format table
```
