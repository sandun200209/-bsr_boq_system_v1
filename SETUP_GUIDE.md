# BSR Rate Hub – Complete Setup & Installation Guide
## How to Install and Run on Any Windows PC or Laptop

> **Designed for Sri Lankan Quantity Surveyors, Civil Engineers, Estimators, and Project Offices.**  
> Supports **BSR** (Building Works), **HSR** (Highway / Road Works), **Water Supply Rates** (NWSDB), and **Sewerage & Storm Water Drainage Works**.

---

## 📋 System Requirements

| Specification | Minimum | Recommended |
| :--- | :--- | :--- |
| **Operating System** | Windows 10 (64-bit, Build 19041+) or Windows 11 | Windows 11 (64-bit) |
| **Processor** | Intel Core i3 / AMD Ryzen 3 or higher | Intel Core i5 / AMD Ryzen 5 or higher |
| **Memory (RAM)** | 4 GB | 8 GB or 16 GB |
| **Free Disk Space** | 5 GB (for container engines, rates & documents) | 10 GB+ |
| **Virtualization** | Hardware Virtualization (VT-x / AMD-V) enabled in BIOS | Enabled |
| **Container Engine** | Docker Desktop for Windows (with WSL 2 backend) | Docker Desktop (latest) |

---

## 🚀 Choose Your Installation Method

Depending on your situation, choose one of the three easy methods below:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       CHOOSE YOUR SETUP PATH                            │
├──────────────────────┬──────────────────────────┬───────────────────────┤
│  Method 1: ONLINE    │   Method 2: OFFLINE USB  │   Method 3: OFFICE    │
│   (Laptop with Wi-Fi)│    (Remote Site / No Net)│      LAN ACCESS       │
│                      │                          │  (No install needed!) │
│  Double-click:       │   Double-click:          │                       │
│  INSTALL_ON_NEW_PC   │   install_offline.bat    │   Open Browser:       │
│                      │                          │   http://Host-IP:8080 │
└──────────────────────┴──────────────────────────┴───────────────────────┘
```

---

## 🌐 Method 1: 1-Click Online Setup (Recommended for Connected PCs)

Use this method if the laptop or PC has internet access.

### Step 1: Copy Folder to the Laptop
1. Copy the entire `bsr_boq_system_v1` folder onto the target PC or laptop (for example, save to `C:\BSR_Rate_Hub` or `Downloads`).

### Step 2: Run the Installer
1. Inside the folder, **double-click** on:
   ```
   INSTALL_ON_NEW_PC.bat
   ```
   *(or `setup_this_pc.bat` / `INSTALL_SETUP.bat`)*

2. The automated wizard will:
   - **Check for Docker Desktop**:
     - If Docker Desktop is already installed, it automatically starts the engine.
     - If Docker Desktop is not installed, it offers to download and run the official installer for you automatically!
   - **Configure Storage**: Sets up secure directories for documents (`data/uploads`) and backups (`data/backups`).
   - **Start the Application**: Launches the PostgreSQL database, FastAPI backend, and Nginx web server.
   - **Synchronize Database**: Applies all rate tables and loads all 3,754 rate items across Building, Highway, Water Supply, and Sewerage.
   - **Create Desktop Shortcut**: Automatically places an icon named **"BSR Rate Hub"** directly on your Windows Desktop.
   - **Configure Windows Firewall**: Prompts to allow office network access.
   - **Launch**: Automatically opens your web browser to `http://localhost:8080`.

---

## 💾 Method 2: 100% Offline USB Setup (No Internet on the New Laptop)

Use this method for remote construction sites, provincial offices, or laptops without fast internet.

### Phase A: On Your Current (Working) Computer
1. Connect a USB flash drive (at least 2 GB free).
2. Inside the working `bsr_boq_system_v1` folder, double-click:
   ```
   export_offline_package.bat
   ```
3. This creates a folder named `offline_bundle/` containing:
   - `docker_images.tar` (all pre-built engines)
   - `seed_database.sql` (all 3,754 rate items across all 4 sectors)
   - `uploads/` (all original PDF and Excel source documents)
4. Copy the entire `bsr_boq_system_v1` folder onto your USB flash drive.

### Phase B: On the Target Laptop
1. Plug the USB flash drive into the target laptop.
2. Copy `bsr_boq_system_v1` to `C:\BSR_Rate_Hub`.
3. Ensure Docker Desktop is installed on the laptop.
4. Double-click:
   ```
   install_offline.bat
   ```
5. In **under 30 seconds**, the system imports the images, restores all rates, creates the desktop shortcut, and opens the browser. **Zero internet required!**

---

## 🏢 Method 3: Office LAN Multi-PC Sharing (Zero-Install for Colleagues)

You **do not need to install Docker on every laptop in your office**!  
One PC or laptop acts as the host server, and all other engineers and quantity surveyors connect through their web browsers over the office Wi-Fi or Ethernet.

### On the Host PC (Where BSR Rate Hub is Running):
1. Double-click:
   ```
   allow_firewall_lan.bat
   ```
   This automatically adds a Windows Defender Firewall rule for port `8080` and displays your PC's network IP address (e.g., `http://192.168.1.15:8080`).

### On Other Laptops & Mobile Devices:
1. Open any web browser (Chrome, Edge, Firefox, Safari).
2. Type the host PC's IP address:
   ```
   http://192.168.1.15:8080
   ```
3. *(Optional shortcut)*: You can copy `connect_from_other_pc.bat` to their laptop. Running it will ask for the host IP and create a desktop shortcut that opens BSR Rate Hub immediately.

---

## 🖥 Daily Usage

Once installed, managing the application is effortless:

| Action | How to Do It |
| :--- | :--- |
| **Launch BSR Rate Hub** | Double-click the **"BSR Rate Hub"** shortcut on your Windows Desktop, or double-click `start_windows.bat`. |
| **Stop the App** | Double-click `stop_windows.bat`. (Your rates and files remain 100% safe). |
| **Restart the App** | Double-click `restart_windows.bat`. |
| **Find Office LAN IP** | Double-click `show_lan_address.bat`. |
| **Backup Everything** | Double-click `backup_database.bat` (creates a timestamped SQL dump + source files in `data/backups/`). |
| **Restore Database** | Open CMD and run: `restore_database.bat <path_to_database.sql>`. |

---

## 🛠 Troubleshooting & Common Questions

### 1. Docker Desktop shows "WSL 2 installation is incomplete"
- **Cause**: Windows Subsystem for Linux (WSL) needs a component update.
- **Fix**:
  1. Open Windows PowerShell or Command Prompt as Administrator.
  2. Type:
     ```cmd
     wsl --install
     ```
  3. Restart your PC when prompted, then open Docker Desktop again.

### 2. "Hardware virtualization is disabled in BIOS"
- **Cause**: Intel VT-x or AMD-V is disabled in your laptop's BIOS/UEFI settings.
- **Fix**:
  1. Restart your laptop and press `F2`, `F10`, `F12`, or `Del` to enter BIOS.
  2. Locate **Virtualization Technology** (or **SVM Mode**) and set to **Enabled**.
  3. Press `F10` to save and reboot.

### 3. Another app is using Port 8080
- **Fix**:
  1. Open `docker-compose.yml` in Notepad.
  2. Change line 42:
     `- "0.0.0.0:8080:80"` to `- "0.0.0.0:8085:80"`.
  3. Double-click `restart_windows.bat`.
  4. Access the system at `http://localhost:8085`.

### 4. Colleagues cannot connect over Wi-Fi
- **Fix**:
  1. Double-click `allow_firewall_lan.bat` on the host PC (run as Administrator).
  2. Verify that both the host PC and the colleague's laptop are connected to the same Wi-Fi router.
  3. Check that the Wi-Fi network profile in Windows is set to **Private Network**, not Public.

---

## 🛡️ Data Safety & Privacy
- **100% Local & Private**: All data is stored locally on your PC (`postgres_data` volume and `data/uploads/`). No data is sent to external clouds or third-party servers.
- **Automatic Backups**: Always run `backup_database.bat` before making major system changes or moving to a new laptop.
