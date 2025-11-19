import traceback
from datetime import datetime

print('Starting Google Sheets live test')
try:
    from utils import log_to_sheets
    entry = {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "task": "Sheets live test", "filename": "sheets_test.jpg"}
    res = log_to_sheets(entry)
    print('log_to_sheets returned:', res)
except Exception as e:
    print('Exception when calling log_to_sheets:')
    traceback.print_exc()
