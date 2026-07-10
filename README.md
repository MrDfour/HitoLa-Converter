# HitoLa PDF & CBZ Downloader & Converter

A lightweight, modern Windows desktop utility built in Python to download comic/doujinshi galleries from **Hitomi.la** and compile them into single **PDF** files or **CBZ** comic book archives.

---

## Key Features

- **Dynamic CDN Key Resolution**: Automatically fetches the live `gg.js` CDN engine at runtime to extract rotating access keys (`gg.b`) and subdomain mapping tables (`gg.m`). **This ensures the app stays functional even when Hitomi.la rotates their CDN keys.**
- **Subdomain Fallback Engine**: Attempts to download pages from the primary calculated CDN node (`w1`/`w2`/`w3`). If a node throws a `404 Not Found` (due to edge synchronization delays), it automatically tries alternative frontends, guaranteeing near-zero download failure rates.
- **Safety Throttling**: Implements a standard **1-second request delay** when downloading images to respect Hitomi's DDoS detection thresholds and protect your IP from rate limits.
- **Format Toggle**: Compiles downloaded pages into a structured **PDF Document** (using `Pillow`) or a standard compressed **Comic Book Zip (CBZ)** archive (using native Python `zipfile`).
- **Responsive Dark GUI**: Features a sleek, responsive Tkinter dark theme. All heavy networking and file processing runs in a background thread to prevent the UI from freezing.
- **Bulk Queue Processing**: Supports downloading multiple gallery URLs sequentially (one-by-one) simply by toggling the bulk downloader switch.

---

## Requirements

The application runs on Python 3 and requires only two lightweight external packages:

- **requests** (For API calls and binary downloads)
- **Pillow** (For WebP reading and PDF conversion)

### Quick Installation

```bash
pip install -r requirements.txt
```

---

## How to Run

Launch the GUI by running:

```bash
python app.py
```

### GUI Instructions
1. Paste a single Hitomi gallery URL (e.g. `https://hitomi.la/reader/4037348.html`) or switch the **Download Multiple URLs** toggle to paste several URLs (one per line).
2. Choose your desired output folder.
3. Select the target file format (**PDF** or **CBZ**).
4. Click **Start Download**. The progress bar and logging console will give you real-time feedback.

---

## How it Works (Under the Hood)

```
[User Input URL] ──> Extract Gallery ID (e.g. 4037348)
                          │
                          ▼
[Metadata API]   ──> Fetch JSON file list (https://ltn.gold-.../4037348.js)
                          │
                          ▼
[CDN Engine]     ──> Live download https://ltn.gold-.../gg.js
                     (Retrieves current CDN token and switch-case map)
                          │
                          ▼
[Resolver]       ──> Translate image hash + token into active URLs
                     (e.g., w2.gold-usergeneratedcontent.net/...)
                          │
                          ▼
[Downloader]     ──> Sequentially fetches WebP files with 1s throttling
                     (Includes w1/w2/w3 auto-fallback if 404 is hit)
                          │
                          ▼
[Compiler]       ──> Package files to PDF or CBZ & Purge temporary files
```

---

## Creating a Standalone `.exe` (Optional)

If you wish to distribute the program as a standalone Windows executable that doesn't require Python to be installed on target computers, compile it using `PyInstaller`:

```bash
pip install pyinstaller
pyinstaller --noconsole --onefile --name "HitoLa-Converter" app.py
```
Find your compiled executable in the newly created `dist/` directory.
