# Google Cloud / Google Sheets service account setup

Follow these steps to allow the app to write rows to a Google Sheet using a service account.

1. Create a Google Cloud project (or use an existing one)
   - Visit https://console.cloud.google.com/
   - Create/select a project

2. Enable the Google Sheets API
   - In the Cloud Console, go to "APIs & Services" -> "Library"
   - Search for "Google Sheets API" and enable it

3. Create a Service Account and key
   - In the Cloud Console, go to "IAM & Admin" -> "Service accounts"
   - Create a new service account (name: snapproof-logger)
   - Grant no special project roles for now (you only need the key)
   - Create a JSON key for the service account and download it. Save it as `credentials.json` in your project root (or somewhere you control).

4. Create a Google Spreadsheet to receive logs
   - Go to Google Sheets and create a new spreadsheet
   - Note the spreadsheet ID from the URL: https://docs.google.com/spreadsheets/d/<SPREADSHEET_ID>/edit

5. Share the spreadsheet with the service account
   - The service account has an email like `snapproof-logger@<project>.iam.gserviceaccount.com`
   - Share the spreadsheet (via the Share button) with that email and give it Editor permission

6. Set environment variables in a `.env` file or your system environment

Example `.env`:

```
USE_SHEETS=True
GOOGLE_CREDENTIALS=credentials.json
GOOGLE_SHEETS_ID=<SPREADSHEET_ID>
```

7. Install dependencies and run

```powershell
pip install -r requirements.txt
Set-Location 'C:\Users\omjgo\OneDrive\Coding\SnapProof\snapproof'
.\venv\Scripts\Activate.ps1
streamlit run app.py
```

Notes
- If you place `credentials.json` somewhere else, update `GOOGLE_CREDENTIALS` with the path.
- The `gspread` + `oauth2client` packages are required; they are included in `requirements.txt`.
- If you run into permission errors, verify the sheet was shared with the correct service account email and that the JSON key matches that account.
