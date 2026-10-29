# Yahoo Mail Order Management & Intelligent Order Extraction System

A production-ready order management application that connects to real Yahoo Mail accounts via authorized SSL IMAP / OAuth 2.0, incrementally retrieves customer purchase order emails, extracts purchase orders and line items from subjects, bodies, and multi-format attachments (PDF, Excel, Word, CSV), and presents them in a structured bilingual dashboard (English & Bengali) and native Android Application (APK).

---

## 🌟 Key Capabilities

1. **Intelligent Multi-Modal Extraction Engine**:
   - **Subject Parser**: Correctly extracts Booking Number, PO Number, Buyer Name, and Order Type. Specifically validated against complex industry formats like:
     ```
     "Elastic booking for CCKL-01734/26& PO-2100011291 of VDE buyer"
     -> Booking: CCKL-01734/26
     -> PO Number: PO-2100011291
     -> Buyer: VDE
     -> Order Type: Elastic Booking
     ```
   - **Body & HTML Content Parser**: Extracts delivery dates, currency, quantities, order totals, and table rows from HTML tables.
   - **Attachment Parser**: Automatically extracts text and tabular line items from:
     - **PDF** documents (`PyMuPDF` / `pypdf`)
     - **Excel** spreadsheets (`.xlsx`, `.xls` via `openpyxl`)
     - **Word** documents (`.docx` via `python-docx`)
     - **CSV** / Delimited files
   - **Confidence Scoring & Duplicate Detection**: Calculates 0.0 to 1.0 confidence score and uses SHA-256 fingerprinting across PO + Booking + Buyer to flag duplicate orders.

2. **Secure Yahoo Mail Integration**:
   - **Zero Plaintext Password Storage**: All credentials and tokens are encrypted with Fernet AES-128-CBC / PBKDF2 HMAC-SHA256 (`backend/app/services/crypto.py`).
   - **Incremental Synchronization**: Uses IMAP SSL (`imap.mail.yahoo.com:993`) and trackable `UID` intervals (`UID {last_uid + 1}:*`) to ensure zero duplicated email downloads.
   - **Dual Authorization Support**: Supports Yahoo App Passwords and Yahoo OAuth 2.0 XOAUTH2.
   - **Background Sync Scheduler**: Automated recurring synchronization daemon + on-demand manual "Sync Now" trigger.

3. **Responsive Bilingual Web Dashboard**:
   - English and Bengali (**বাংলা**) instant language toggle.
   - Live KPI cards: Total Orders, Confirmed, Review Needed, Total Units.
   - Search & filtering by PO Number, Booking Reference, Buyer Name, or Status.
   - Order Inspector: View source email, extracted line items, inspect attachments, edit and override values.
   - One-Click Data Export to **Excel (`.xlsx`)** and **CSV**.
   - Built-in Android APK download link directly in the top navbar.

4. **Android Mobile Application (APK)**:
   - Built with Jetpack Compose & Kotlin targeting Android 14+ (SDK 36, minSdk 24).
   - Consumes the same backend REST API (`/api/v1/orders`, `/api/v1/sync/trigger`).
   - Offline-capable cache and mobile order search.
   - Pre-compiled APK available at `android_app/app/build/outputs/apk/debug/app-debug.apk` and downloadable from the web app at `/static/YahooOrderManager.apk`.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.12+
- OpenJDK 17 (for Android build)

### 2. Starting the Backend & Web Application
Run the unified launcher:
```bash
python run_backend.py
```
- **Web Dashboard**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Direct APK Download**: [http://localhost:8000/static/YahooOrderManager.apk](http://localhost:8000/static/YahooOrderManager.apk)

### 3. Yahoo Mail Setup Instructions
To connect your real Yahoo Mail account:
1. Go to your [Yahoo Account Security Settings](https://login.yahoo.com/account/security).
2. Click on **Generate app password** (or "Manage app passwords").
3. Enter an app name (e.g. `OrderManager`) and click **Generate password**.
4. Open the Web Dashboard at [http://localhost:8000](http://localhost:8000), click **Mail Settings** in the top-right corner.
5. Enter your Yahoo email and paste the generated 16-character app password.
6. Click **Test Connection** followed by **Save & Connect**.
7. Click **Sync Now** to pull unread order emails!

---

## 🧪 Automated Test Suite

Run the unit and integration tests:

```bash
# Test 1: Regex & Intelligent Extraction Engine
python backend/tests/test_extraction.py

# Test 2: API Endpoints, Security Encryption & Export Generation
python backend/tests/test_api.py
```

---

## 📱 Building the Android APK

The project includes an Android Studio / Gradle project in `android_app/`.
To rebuild the debug APK:
```powershell
cd android_app
./gradlew.bat assembleDebug
```
The compiled APK will be output to:
`android_app/app/build/outputs/apk/debug/app-debug.apk`

---

## 📂 Project Architecture

```
resilient-oppenheimer/
├── run_backend.py                  # Main entry point for production server
├── backend/
│   ├── app/
│   │   ├── config.py               # Global settings, paths, AES keys
│   │   ├── database.py             # SQLAlchemy engine & session factory
│   │   ├── models.py               # Relational ORM models (Accounts, Orders, Items, Attachments, Logs)
│   │   ├── schemas.py              # Pydantic v2 validation models
│   │   ├── services/
│   │   │   ├── crypto.py           # AES encryption for Yahoo credentials
│   │   │   ├── imap_client.py      # Yahoo IMAP SSL incremental fetcher
│   │   │   ├── extractor.py        # Multi-modal extraction & NLP pattern matcher
│   │   │   ├── attachment_service.py # PDF, Excel, Word, CSV parsers
│   │   │   ├── sync_service.py     # Sync orchestration & background scheduler
│   │   │   └── export_service.py   # Excel (.xlsx) & CSV generation
│   │   ├── routers/
│   │   │   ├── accounts.py         # Yahoo credential endpoints
│   │   │   ├── orders.py           # Orders CRUD, search, and KPI metrics
│   │   │   ├── sync.py             # Sync trigger & log history
│   │   │   └── export.py           # File downloads & export endpoints
│   │   └── main.py                 # FastAPI application
│   ├── static/
│   │   ├── index.html              # Bilingual responsive Web Dashboard (EN & BN)
│   │   └── YahooOrderManager.apk   # Ready-to-install Android APK
│   └── tests/
│       ├── test_extraction.py      # Unit tests for subject & body extraction
│       └── test_api.py             # Integration tests for API & encryption
└── android_app/                    # Android Project (Jetpack Compose & Kotlin)
    ├── app/
    │   ├── build.gradle.kts
    │   └── src/main/
    │       ├── AndroidManifest.xml
    │       └── kotlin/com/example/yahooordermanager/
    │           ├── MainActivity.kt
    │           ├── data/OrderModels.kt & DataRepository.kt
    │           └── ui/main/MainScreen.kt & MainScreenViewModel.kt
    └── gradlew.bat
```
