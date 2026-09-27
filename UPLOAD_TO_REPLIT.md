1. Create a new Replit (choose "Import from GitHub" if you push this repo there, or create a new Repl and upload files).
2. Ensure files in the project root include: `mtg_scanner.py`, `requirements.txt`, `.replit`.
3. In Replit's Shell, run:

```bash
pip install -r requirements.txt
python3 mtg_scanner.py
```

4. Open the webview or the provided Replit URL. Allow camera access for scanning.

Notes:
- Replit's free containers may not persist the SQLite DB between restarts unless using Replit DB or external storage.
- For better OCR performance, the app uses client-side Tesseract.js loaded from CDN; server-side OCR is not required.
