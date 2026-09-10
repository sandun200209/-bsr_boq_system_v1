# BSR Rate Hub – Sri Lanka BOQ Data System

> **Production-Ready Local & Office LAN Construction Rate Management System**  
> Designed for Sri Lankan Building Schedule of Rates (BSR), Provincial Rate Books, Multi-Format Document Extraction, Trigram Search, Cross-Provincial Rate Comparisons, and BOQ Estimating Workflows.

---

## 🏗 System Capabilities

- **Multi-Format Extraction Pipeline**: Dedicated format parsers for **PDF** (PyMuPDF & pdfplumber native text/table extraction with multi-line description stitching), **Excel** (`.xlsx`, `.xlsm` with formula evaluation), **Word** (`.docx` tables & paragraphs), **CSV/TSV** (automatic delimiter detection), and **Plain Text** (`.txt`).
- **Cryptographic & Permanent Traceability**: Every uploaded file is assigned a unique UUID and SHA-256 hash, permanently organized under `/data/uploads/{Province}/{District}/{Year}/{Revision}/`. Original source files are never deleted or overwritten.
- **Verification & Review Queue**: Automated validation checks for missing codes, non-standard units, zero/negative rates, duplicates, and suspicious price thresholds with an editable review table and bulk approval.
- **Lightning-Fast Live Search**: Powered by PostgreSQL 16 with `pg_trgm` GIN trigram indexes for instant substring and keyword matching across 100,000+ construction items.
- **Cross-Provincial Rate Comparison**: Compare rates across multiple provinces, districts, and years simultaneously. Calculate rate difference in LKR, percentage variance, min, max, average, and designate any row as the baseline.
- **Canonical Master Item Mapping**: Map differing provincial codes (e.g. Southern `BK01`, Uva `D-15`, Central `BR-04`) to a single canonical master item for cross-island cost intelligence.
- **Office LAN Ready**: Pre-configured to serve all PCs on your office Wi-Fi or Ethernet on Port `8080`.

---

## 🚀 Quick Start Guide (Windows)

### Prerequisites
1. **Windows 10 or 11 (64-bit)**
2. **Docker Desktop for Windows**  
   If you don't have Docker Desktop installed, download and install it from:  
   👉 [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)  
   *(Make sure Docker Desktop is started and shows a green "Engine running" icon in your system tray).*

---

### Step 1: Launch the System
1. Open the project folder in Windows File Explorer:
   ```
   C:\Users\SANDUN\Downloads\bsr_boq_system_v1
   ```
2. **Double-click** on:
   ```
   start_windows.bat
   ```
3. A command window will appear. It will automatically:
   - Check if Docker Desktop is running.
   - Create persistent folders (`data/uploads` and `data/backups`).
   - Build and start PostgreSQL 16, the FastAPI backend, and Nginx/React frontend.
   - Run database schema migrations (`alembic upgrade head`).
   - Automatically open your default web browser to:
     ```
     http://localhost:8080
     ```

---

## 🛑 How to Stop, Restart, and Manage

All management scripts are located directly in the project folder for easy double-clicking:

| Action | Script to Run / Double-Click | Description |
| :--- | :--- | :--- |
| **Start / Launch** | `start_windows.bat` | Starts all services, runs migrations, and opens your browser. |
| **Stop System** | `stop_windows.bat` | Safely stops containers. Database and uploaded files remain intact. |
| **Restart** | `restart_windows.bat` | Reboots all containers quickly. |
| **Backup Everything** | `backup_database.bat` | Generates a timestamped SQL dump and copies all uploaded documents to `data/backups/`. |
| **Restore Database** | `restore_database.bat` | Restores database tables from a specified `.sql` backup file. |

---

## 🌐 How Other PCs on Your Office LAN Can Access the System

The BSR Rate Hub is bound to `0.0.0.0:8080`, allowing multiple quantity surveyors and engineers on the same office network to access the system simultaneously.

1. On the **Host PC** (where Docker is running):
   - Press `Windows Key + R`, type `cmd`, and press Enter.
   - Type `ipconfig` and press Enter.
   - Locate your **IPv4 Address** (for example: `192.168.1.105`).
2. On **Any Other PC or Laptop** connected to the same office Wi-Fi or Ethernet cable:
   - Open Chrome, Edge, or Firefox.
   - Enter your host PC's IP address followed by `:8080`:
     ```
     http://192.168.1.105:8080
     ```
3. If the page does not open from another PC, ensure Windows Defender Firewall allows inbound connections on Port **8080**.

---

## 💾 Database & Source Document Backups

### To Create a Backup:
1. Double-click `backup_database.bat`.
2. A new timestamped folder will be created under:
   ```
   data\backups\backup_YYYYMMDD_HHMMSS\
       ├── database.sql
       └── uploads\
   ```
3. This creates a full SQL dump of all rate items, master mappings, and source metadata, plus a complete copy of every uploaded PDF/Excel/Word file.

### To Restore from a Backup:
1. Open Command Prompt in the project folder:
   ```cmd
   restore_database.bat data\backups\backup_20260909_153000\database.sql
   ```
2. Type `Y` to confirm. The script will restore your database state.

---

## 🛠 Troubleshooting Common Issues

### 1. "Docker Desktop is not running"
- **Cause**: Docker Desktop has not been started on Windows.
- **Solution**: Open Docker Desktop from the Windows Start menu. Wait 30 seconds until the bottom-left status indicator turns green, then re-run `start_windows.bat`.

### 2. "Port 8080 is already in use"
- **Cause**: Another application (e.g. IIS, Jenkins, or a local server) is using port 8080.
- **Solution**:
  1. Open `docker-compose.yml` in Notepad.
  2. Under `frontend:`, change `"0.0.0.0:8080:80"` to `"0.0.0.0:8085:80"`.
  3. Save the file and restart using `start_windows.bat`. You can now access the system at `http://localhost:8085`.

### 3. "413 Request Entity Too Large"
- **Cause**: Attempting to upload a file larger than the configured limit.
- **Solution**: Nginx and the backend are pre-configured to support up to **250 MB** uploads (`client_max_body_size 250M;`). If you encounter this error, ensure you are accessing the application through port 8080, where Nginx handles streaming.

### 4. "Database Container Unhealthy"
- **Cause**: PostgreSQL did not finish initializing within the retry window.
- **Solution**:
  1. Run `stop_windows.bat`.
  2. Run `docker compose down -v` to reset data volumes if this is a fresh setup.
  3. Re-run `start_windows.bat`.

### 5. "Scanned PDF (OCR Required)"
- **Cause**: The uploaded PDF is a scanned image without an embedded digital text layer.
- **Solution**: The system identifies this and marks the document as `OCR_REQUIRED`. For best results, use official digital PDFs or convert the document through an OCR utility before uploading.

---

## 🏛 System Architecture

```
bsr-rate-hub/
│
├── docker-compose.yml          # PostgreSQL 16, FastAPI, and Nginx React frontend
├── .env.example                # Environment settings template
├── README.md                   # Complete Windows user guide
│
├── frontend/                   # React 18 + TypeScript + Vite + Tailwind CSS
│   ├── Dockerfile
│   ├── nginx.conf              # 250M upload size, 600s timeouts, API proxy
│   └── src/
│       ├── api/client.ts       # Typed API client
│       ├── components/         # Desktop layout, navy sidebar, header
│       ├── pages/              # Dashboard, Import Center, Search, Compare, Review, Sources, Master Items
│       └── constants/          # Sri Lanka 9 Provinces & 25 Districts cascading data
│
├── backend/                    # Python 3.11 / FastAPI / SQLAlchemy / Alembic
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic/                # Database migrations (initial schema & pg_trgm)
│   └── app/
│       ├── main.py             # FastAPI entry, CORS, lifespan
│       ├── database.py         # SQLAlchemy connection pooling
│       ├── models/             # SourceFile, ImportJob, RateItem, MasterItem
│       ├── schemas/            # Pydantic v2 schemas
│       ├── services/           # Storage, validation, and comparison calculations
│       ├── importers/          # PDF, Excel, DOCX, CSV, TXT format extractors
│       └── api/                # REST endpoints
│
├── scripts/                    # Windows automation batch scripts
│   ├── start_windows.bat
│   ├── stop_windows.bat
│   ├── restart_windows.bat
│   ├── backup_database.bat
│   └── restore_database.bat
│
└── data/
    ├── uploads/                # Structured source storage (host persistent)
    └── backups/                # Automated database and document archives
```
