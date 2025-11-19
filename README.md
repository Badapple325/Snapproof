# SnapProof

Local Streamlit app that generates timestamped PDF proofs from images.

Quick start (PowerShell):

```powershell
Set-Location 'C:\Users\omjgo\OneDrive\Coding\SnapProof\snapproof'
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Files created:
- `app.py` – the Streamlit app
- `requirements.txt` – Python dependencies

If PowerShell blocks venv activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

Optional add-ons: email delivery, Google Sheets logging, Stripe payments, Firebase Auth. Ask me to scaffold any of these.

Google Sheets logging (optional)
--------------------------------
To enable cloud logging to Google Sheets instead of the local CSV, set the environment variable `USE_SHEETS` to `True` (or `1`) and provide the service account credentials and the target sheet ID:

1. Create a `.env` file in the project root with at least:

```
USE_SHEETS=True
GOOGLE_CREDENTIALS=credentials.json
GOOGLE_SHEETS_ID=<your-spreadsheet-id>
```

2. Install the extra deps (already added to `requirements.txt`):

```powershell
pip install -r requirements.txt
```

3. Follow `gcloud_setup.md` for creating a service account and sharing the sheet with the service account email.

The app will attempt Google Sheets logging when `USE_SHEETS` is set; if Sheets logging fails it will fall back to the local `proof_log.csv`.
