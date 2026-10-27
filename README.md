[README.md](https://github.com/user-attachments/files/33996029/README.md)
# Stratos Flight Telemetry Exporter

A standalone tool to inspect and export high-resolution flight telemetry and landing reports directly from the local Stratos database.

Available both as a **standalone Windows executable** (`export_stratos.exe`) and as an open-source **Python script** ([export_stratos.py](export_stratos.py)).

- **Output Directory:** [stratos_logs/](stratos_logs/) (created automatically next to the executable/script)
- **Requirements:** 
  - **Executable:** Windows 10/11 (zero dependencies, Python not required).
  - **Python Script:** Python 3.8+ (uses only built-in standard library modules: `sqlite3`, `json`, `os`, `sys`, `pathlib`).

---

## 1. Features

- **100% Standalone & Portable:** Directly reads the local Stratos SQLite database in read-only mode (`%APPDATA%\Stratos\plugins-data\landing-analyser\landing-analyser.db`). Runs on any machine with Stratos installed without requiring external files or network access.
- **Interactive or CLI:** Can be double-clicked in Windows Explorer to open an interactive menu, or scripted via command-line arguments.
- **True Geometric Descent Rate:** Implements Stratos's exact 500 ms rolling linear regression algorithm (`Tn`) to calculate real-time geometric descent rate from AGL changes, alongside the simulator's raw instrument readout (`Sim VS`).
- **Exact Touchdown Alignment:** Identifies the precise touchdown frame at the initial `onGround = true` transition, recording the official landing rate.
- **Consistent Decimal Precision:** Enforces formatted float precision across all rows:
  - `AGL ft`, `Pitch °`, and `Bank °`: Formatted to 1 decimal place (including trailing `.0`).
  - `G-Force`: Formatted to 2 decimal places.
  - `Time`: High-resolution 3-decimal millisecond timestamps (e.g. `T−0.046s`).
- **Collision-Proof Filenames:** Exports files using UTC timestamp prefixes (`YYYY-MM-DD_HHMM DEP-ARR CALLSIGN.tsv`), ensuring unique filenames even when multiple flights share the same date, route, and callsign.
- **Companion Metadata:** Exports a comprehensive `.json` file alongside every `.tsv` containing complete landing metadata (runway, approach stability, flap settings, and coordinates).

---

## 2. Usage

### A. Interactive Mode (Double-Click)
When you double-click `export_stratos.exe` (or run it without arguments), an interactive prompt launches:

```text
============================================================
           Stratos Flight Log Exporter
============================================================
Loaded 44 flight reports from Stratos database.
------------------------------------------------------------
Options:
  ?          - List all flights
  *          - Export all flights
  <callsign> - Export by callsign (e.g. WAT7789)
  <number>   - Export by list index # (e.g. 44)
  q          - Quit
------------------------------------------------------------
Enter choice: 
```

Type `?` to view all flights, enter a callsign or index number to export, and type `q` when finished. The window remains open until you exit.

### B. Command-Line Arguments
For terminal users or automated batch scripts, you can pass arguments directly:

- **List All Flights:**
  ```cmd
  export_stratos.exe ?
  ```
  *(or `python export_stratos.py ?`)*

- **Export All Flights:**
  ```cmd
  export_stratos.exe *
  ```
  *(or `python export_stratos.py "*"`)*

- **Export by Flight Number or Callsign:**
  ```cmd
  export_stratos.exe 44
  export_stratos.exe WAT7789
  ```

---

## 3. Output Format

All exports are saved into the `stratos_logs/` subfolder directly beneath the script.

### Filename Structure
- **TSV Telemetry Table:** `stratos_logs/{YYYY-MM-DD}_{HHMM} {DEP}-{ARR} {CALLSIGN}.tsv`
- **JSON Metadata:** `stratos_logs/{YYYY-MM-DD}_{HHMM} {DEP}-{ARR} {CALLSIGN}.json`

### 11-Column TSV Layout
Each TSV contains tab-separated columns matching standard FDR layout:

| Column Header | Description | Example |
| :--- | :--- | :---: |
| **Time** | Timestamp relative to touchdown in milliseconds | `T−0.046s` |
| **Phase** | Flight phase (`Approach`, `Flare`, `Touchdown`, `Rollout`) | `Touchdown` |
| **AGL ft** | Altitude Above Ground Level (calibrated gear height) | `1.2` |
| **Descent fpm** | Geometric descent rate from rolling AGL regression | `-212` |
| **Sim VS** | Raw flight simulator instrument vertical speed | `-171` |
| **IAS kt** | Indicated Airspeed in knots | `66` |
| **GS kt** | Groundspeed in knots | `66` |
| **Pitch °** | Aircraft pitch attitude in degrees | `-2.6` |
| **Bank °** | Aircraft bank angle in degrees | `0.7` |
| **G-Force** | Normal acceleration (G load) | `1.11` |
| **On Ground** | Weight-on-wheels sensor flag (`true` or `false`) | `true` |

---

### Note on Derived Column (`Descent fpm`)

The **`Descent fpm`** column is **not stored as per-frame data in the Stratos database**:
- Inside `landing-analyser.db`, each recorded sample frame only contains the simulator's raw instrument vertical speed (`vs`). Stratos never stores pre-calculated `Descent fpm` values in the database; it computes them dynamically on the fly in its desktop UI.
- The export script reproduces this by calculating the geometric descent rate dynamically using the rolling 500 ms AGL linear regression algorithm, applying the official landing rate at the touchdown frame. (See the file `Descent_FPM.md` for more detail.)
