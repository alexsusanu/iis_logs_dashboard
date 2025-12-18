# Create venv
python3 -m venv venv

# Activate
source venv/bin/activate
deactivate

# Install
pip install -r requirements.txt


# Log Dashboard

## Architecture

**Backend (Python Flask):**
- Scans folder recursively on startup
- Parses all log files into memory
- Detects format by filename (`_u_ex` = w3svc, else = trace)
- Serves REST API and HTML dashboard

**Frontend (Single HTML page):**
- Loads all parsed data once
- Client-side filtering/sorting on loaded data
- Real-time search with debouncing

## Usage

1. **Start the server:**
```bash
python app.py /path/to/logs_folder
```
source is harcoded to logs_folder

2. **Open browser:**
```
http://localhost:8888
```

## Test Data

Two test log files included:
- `test_logs/subfolderA/log_file_A.log` (trace format)
- `test_logs/subfolderB/log_file_B.log` (w3svc format)

**Run with test data:**
```bash
python app.py test_logs
```

## Filtering

**Available filters:**
- **Global search**: Searches all fields
- **Date range**: Filter by timestamp
- **Path/Message**: Substring search in path or message
- **Method**: GET, POST, etc.
- **Status**: HTTP status codes
- **IP**: IP address filter
- **Files**: Multi-select specific files

**Filter logic:**
- All filters use AND logic
- Text filters are case-insensitive
- Auto-applies after 300ms typing pause
- Manual "Apply Filters" button available

**Scenarios:**
1. Search single file: Select one file from dropdown
2. Search 4-5 files: Check multiple files in selector
3. Search all files: Check "All Files" or leave all checked
4. Combine filters: All active filters apply together

**Sorting:**
- Click any column header to sort
- Click again to reverse sort order

## Performance

- Filters 50k rows in <100ms
- Displays first 1000 rows (browser performance)
- All filtering happens client-side
- No database required

## File Format Detection

**W3SVC (IIS logs):**
- Filename contains `_u_ex`
- Space-delimited with header line

**Trace logs:**
- All other files
- Format: `YYYY-MM-DD HH:MM:SS.mmm LEVEL message`

## Memory Usage

- 500MB raw logs → ~100MB parsed in Python
- ~100MB loaded in browser
- Suitable for up to ~1GB of raw logs
# iis_logs_dashboard
