#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) Shenzhen Yinwang Intelligent Technologies Co., Ltd. 2025. All rights reserved.


import argparse
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment


def save_to_excel(bugs, filepath):
    wb = Workbook()
    ws = wb.active
    ws.title = "Bug Report"
    
    headers = ['Severity', 'Category', 'Template ID', 'Name', 'Location', 'Pattern', 'Context (5 lines before/after)', 'Timestamp']
    
    hint_style = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
    hf = Font(bold=True, color='FFFFFF')
    
    for col, header in enumerate(headers, 1):
        cell = ws.cell(1, col, header)
        cell.fill, cell.font, cell.alignment = hint_style, hf, Alignment(horizontal='center')
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    severity_colors = {'CRITICAL': 'FFFF0000', 'HIGH': 'FFFF9900', 'MEDIUM': 'FFFFFF00', 'LOW': 'FF00FF00'}
    
    for row, bug in enumerate(bugs, 2):
        ws.cell(row, 1, bug.get('severity', 'UNKNOWN'))
        ws.cell(row, 2, bug.get('category', ''))
        ws.cell(row, 3, bug.get('template_id', ''))
        ws.cell(row, 4, bug.get('name', ''))
        ws.cell(row, 5, bug.get('location', ''))
        ws.cell(row, 6, bug.get('pattern', ''))
        
        cc = ws.cell(row, 7, bug.get('context', ''))
        cc.alignment = Alignment(horizontal='left', vertical='top', wrap_text=True)
        cc.font = Font(size=10, name='Courier New')
        
        ws.cell(row, 8, timestamp)
        ws.row_dimensions[row].height = 100
        
        severity = bug.get('severity', 'UNKNOWN').upper()
        cfill = PatternFill(start_color=severity_colors.get(severity, 'FFFFFFFF'), fill_type='solid')
        
        for col in range(1, 8):
            ws.cell(row, col).fill = cfill
    
    for col, w in [('A', 10), ('B', 12), ('C', 20), ('D', 25), ('E', 30), ('F', 25), ('G', 80), ('H', 20)]:
        ws.column_dimensions[col].width = w
    
    wb.save(filepath)
    print(f"\nBug report saved to: {filepath}")
    return True

def main():
    import json
    parser = argparse.ArgumentParser(description='Excel Output Helper')
    parser.add_argument('--bugs-file', help='JSON file with bugs list')
    parser.add_argument('--output', '-o', help='Output Excel file (default: bug_report.xlsx)')
    
    args = parser.parse_args()
    bugs = json.load(open(args.bugs_file)) if args.bugs_file else []
    
    if bugs and save_to_excel(bugs, args.output or 'bug_report.xlsx'):
        print(f"Total issues: {len(bugs)}")
        return 0
    print("No bugs to save" if not bugs else "Failed to save")
    return 1

if __name__ == '__main__':
    import sys
    sys.exit(main())
