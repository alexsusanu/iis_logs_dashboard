#!/usr/bin/env python3
import os
import re
import json
from pathlib import Path
from flask import Flask, jsonify, send_from_directory
from datetime import datetime

app = Flask(__name__, static_folder='.')

# Global variable to store parsed logs
parsed_logs = []

def parse_trace_log(filepath, content):
    """Parse trace format logs (non-w3svc)"""
    logs = []
    lines = content.split('\n')
    
    for line in lines:
        if not line.strip():
            continue
            
        # Match: 2025-12-18 00:00:03.5805 TRACE Start function InstrumentDownloadProcesses.RegisterProxy
        match = re.match(r'^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d+)\s+(\w+)\s+(.+)$', line)
        if match:
            timestamp, level, message = match.groups()
            
            # Extract additional fields from message
            function = ""
            params = ""
            system_name = ""
            
            if "Start function" in message or "Function" in message:
                func_match = re.search(r'function\s+([\w.]+)', message)
                if func_match:
                    function = func_match.group(1)
            
            if "systemName:" in message:
                sys_match = re.search(r'systemName:\s*([\w.-]+)', message)
                if sys_match:
                    system_name = sys_match.group(1)
            
            if "Parameters:" in message:
                params = "Yes"
            
            logs.append({
                'file': str(filepath),
                'format': 'trace',
                'timestamp': timestamp,
                'level': level,
                'message': message,
                'function': function,
                'system_name': system_name,
                'has_params': params
            })
    
    return logs

def parse_w3svc_log(filepath, content):
    """Parse W3SVC IIS format logs"""
    logs = []
    lines = content.split('\n')
    
    headers = []
    for line in lines:
        if not line.strip():
            continue
        
        # Extract headers if present
        if line.startswith('#'):
            if line.startswith('#Fields:'):
                headers = line[8:].strip().split()
            continue
        
        # Parse data line
        parts = line.split()
        if len(parts) < 2:
            continue
        
        # Build log entry
        log_entry = {
            'file': str(filepath),
            'format': 'w3svc'
        }
        
        # Use headers if available, otherwise generic column names
        if headers:
            for i, header in enumerate(headers):
                if i < len(parts):
                    log_entry[header.replace('-', '_')] = parts[i]
        else:
            # No headers - use generic field names and auto-detect
            for i, part in enumerate(parts):
                log_entry[f'field_{i}'] = part
        
        # Combine date and time into timestamp if present
        if 'date' in log_entry and 'time' in log_entry:
            log_entry['timestamp'] = f"{log_entry['date']} {log_entry['time']}"
        elif 'field_0' in log_entry and 'field_1' in log_entry:
            # Try to build timestamp from first two fields
            log_entry['timestamp'] = f"{log_entry['field_0']} {log_entry['field_1']}"
        
        logs.append(log_entry)
    
    return logs

def scan_and_parse_logs(root_folder):
    """Recursively scan folder and parse all log files"""
    all_logs = []
    root_path = Path(root_folder)
    
    if not root_path.exists():
        print(f"Error: Folder {root_folder} does not exist")
        return all_logs
    
    print(f"Scanning folder: {root_folder}")
    
    for log_file in root_path.rglob('*.log'):
        print(f"Processing: {log_file}")
        
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Detect format based on filename
            relative_path = log_file.relative_to(root_path)
            
            if '_u_ex' in log_file.name:
                # W3SVC format
                logs = parse_w3svc_log(str(relative_path), content)
            else:
                # Trace format
                logs = parse_trace_log(str(relative_path), content)
            
            all_logs.extend(logs)
            print(f"  Parsed {len(logs)} entries")
            
        except Exception as e:
            print(f"Error parsing {log_file}: {e}")
    
    print(f"Total entries parsed: {len(all_logs)}")
    return all_logs

@app.route('/')
def index():
    """Serve the main dashboard HTML"""
    return send_from_directory('.', 'dashboard.html')

@app.route('/api/data')
def get_data():
    """Return all parsed log data as JSON"""
    return jsonify(parsed_logs)

@app.route('/api/stats')
def get_stats():
    """Return statistics about loaded data"""
    files = set(log['file'] for log in parsed_logs)
    return jsonify({
        'total_entries': len(parsed_logs),
        'total_files': len(files),
        'files': sorted(list(files))
    })

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python app.py <logs_folder_path>")
        sys.exit(1)
    
    logs_folder = sys.argv[1]
    
    print("Starting log parser...")
    parsed_logs = scan_and_parse_logs(logs_folder)
    
    if not parsed_logs:
        print("No logs parsed. Exiting.")
        sys.exit(1)
    
    print(f"\nStarting web server on http://localhost:8888")
    print("Open browser and go to http://localhost:8888")
    app.run(debug=True, port=8888, host='0.0.0.0')
