# Centralized Multi-Device Deployment & Administration Guide
## BSR Rate Hub – Sri Lanka Multi-Sector BOQ Engineering System

---

## 1. System Architecture Overview

The system is engineered for **multi-device synchronization**. Any rate item added, document uploaded, or review approved from one PC is immediately available across all connected PCs, laptops, tablets, and smartphones.

```
                  ┌─────────────────────────────────────────┐
                  │          Connected Devices              │
                  │  (PC 1, Laptop 2, iPad, Android Phone)  │
                  └────────────────────┬────────────────────┘
                                       │ HTTPS / LAN
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │       Frontend Single Page App          │
                  │     (React + TypeScript + Tailwind)     │
                  │   Desktop, Tablet & Mobile Viewports    │
                  └────────────────────┬────────────────────┘
                                       │ JWT Authenticated API
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │             FastAPI Backend             │
                  │     RBAC Security • Audit Logging       │
                  └─────────────┬───────────────────────────┘
                                │
        ┌───────────────────────┴───────────────────────┐
        ▼                                               ▼
┌──────────────────────────────┐        ┌──────────────────────────────┐
│  Centralized PostgreSQL DB   │        │ Centralized Document Storage │
│ (Supabase Cloud / Shared DB) │        │ (Supabase Storage / S3 / LAN)│
│  5,178+ Multi-Sector Rates   │        │ PDF, Excel, Word, Images, ZIP│
└──────────────────────────────┘        └──────────────────────────────┘
```

---

## 2. Default User Accounts (Role-Based Access Control)

The system comes pre-seeded with 4 test and operational accounts:

| Role | Email / Username | Password | Permissions |
| :--- | :--- | :--- | :--- |
| **ADMIN** | `admin@bsrhub.lk` / `admin` | `Admin@123456` | Full system control, user creation/editing, role management, document deletion, security audit trail. |
| **MANAGER** | `manager@bsrhub.lk` / `manager` | `Manager@123456` | Document upload, rate extraction, review queue approve/reject, rate editing. |
| **USER** | `qs@bsrhub.lk` / `qs_engineer` | `User@123456` | Rate search, cross-provincial compare, Excel export, document upload. |
| **VIEWER** | `viewer@bsrhub.lk` / `viewer` | `Viewer@123456` | Read-only access to rate search and comparison matrix. Modification and upload actions are disabled. |

> **Security Note**: Administrators can create new accounts and change passwords directly in the **Users & Audit** dashboard.

---

## 3. Option A: Cloud Deployment (Global Access Anywhere)

### Step 1: Set Up Centralized Cloud Database (Supabase)
1. Sign up at [https://supabase.com](https://supabase.com) and create a free or pro project.
2. Go to the **SQL Editor** in your Supabase dashboard.
3. Open `data/migrations/supabase_schema.sql` from this repository, copy the contents, paste into the Supabase SQL editor, and click **Run**.
4. In Supabase **Settings -> Database**, copy the **Connection string (URI)** (e.g. `postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres`).

### Step 2: Set Up Centralized Cloud Document Storage (Supabase Storage)
1. In Supabase, go to **Storage -> New Bucket**.
2. Name the bucket: `bsr-documents` (Private bucket).
3. In Supabase **Settings -> API**, copy:
   - **Project URL** (e.g. `https://xyzcompany.supabase.co`)
   - **service_role secret key** (needed for backend authenticated uploads).

### Step 3: Deploy Backend API (Render or Railway)
#### Deploy on Render:
1. Connect your repository to [Render.com](https://render.com).
2. Create a new **Web Service** using `backend/Dockerfile`.
3. Set the following Environment Variables in the Render dashboard:
   - `DATABASE_URL`: `postgresql://postgres:[password]@db.[ref].supabase.co:5432/postgres`
   - `STORAGE_BACKEND`: `supabase`
   - `SUPABASE_URL`: `https://[ref].supabase.co`
   - `SUPABASE_SERVICE_ROLE_KEY`: `[your-service-role-key]`
   - `SUPABASE_STORAGE_BUCKET`: `bsr-documents`
   - `JWT_SECRET`: `[generate a secure random 64-character string]`
   - `CORS_ORIGINS`: `*`
4. Deploy the service. Render will provide a public URL: `https://bsr-rate-hub-api.onrender.com`.

### Step 4: Deploy Frontend (Vercel or Netlify)
#### Deploy on Vercel:
1. Import your repository into [Vercel.com](https://vercel.com).
2. Root Directory: `frontend`
3. Build Command: `npm run build`
4. Output Directory: `dist`
5. Set Environment Variable:
   - `VITE_API_BASE_URL`: `https://bsr-rate-hub-api.onrender.com/api`
6. Click **Deploy**.
7. In `vercel.json`, requests to `/api/*` will route directly to your backend.

---

## 4. Option B: Local Office Network (LAN Server Deployment)

If you prefer to keep all data within your physical office local network without cloud subscriptions:

### Step 1: Designate One Host PC
1. Run `INSTALL_SETUP.bat` on the host PC (e.g., the office QS server or a desktop that stays on).
2. Run `allow_firewall_lan.bat` as Administrator on the host PC to open Ports `8080` (Frontend) and `8000` (API) on the local Windows Firewall.
3. Check the host PC's local IP address:
   ```cmd
   ipconfig
   ```
   (e.g. `192.168.1.105`).

### Step 2: Access from Any Laptop or PC in the Office
Open any web browser on any office laptop or desktop connected to the same Wi-Fi / LAN:
```
http://192.168.1.105:8080
```
Log in using any of the authorized credentials.

---

## 5. Smartphone & Tablet Access (PWA Setup)

The frontend is fully optimized for iPhone, iPad, and Android screens (down to 320px width) with touch-friendly navigation, mobile drawers, and bottom action bars:

### iPhone & iPad (iOS Safari)
1. Connect to the office Wi-Fi or visit your cloud URL (e.g. `http://192.168.1.105:8080` or your Vercel URL).
2. Tap the **Share** icon (square with arrow pointing up) in Safari.
3. Tap **Add to Home Screen**.
4. The **BSR Hub** app icon will appear on your home screen. Tapping it opens the app in fullscreen standalone mode without browser URL bars.

### Android (Google Chrome)
1. Open Chrome and navigate to the application URL.
2. Tap the three dots menu (**⋮**) in the top right.
3. Tap **Install app** or **Add to Home screen**.
4. The system installs as a native-like Web App.

---

## 6. Verification Checklist

- [x] **Centralized Database**: Multi-sector rate hierarchy (BSR, HSR, Water Supply, Sewerage) with 5,178 active items.
- [x] **Centralized Storage**: Automatic upload streaming to Supabase Storage with local cache fallback.
- [x] **Role-Based Access Control**: Strict route protection on `/api/users`, `/api/documents/{id}`, `/api/review/{id}`, and `/api/master-items`.
- [x] **Audit Trail**: Every login, upload, rate update, document deletion, and user creation is logged with timestamps and IP addresses.
- [x] **Mobile Responsiveness**: Responsive mobile hamburger drawer, mobile bottom navigation, touch targets, and horizontal scroll tables for all device sizes.
