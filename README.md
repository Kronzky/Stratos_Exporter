[README.md](https://github.com/user-attachments/files/33994718/README.md)
# Stratos Flight Telemetry Exporter

A standalone, zero-dependency Python tool to inspect and export high-resolution flight telemetry and landing reports directly from the local Stratos database.

**Script:** [export_stratos.py](export_stratos.py)  
**Output Directory:** [stratos_logs/](stratos_logs/)  
**Requirements:** Standard Python 3.8+ (uses only built-in standard library modules: `sqlite3`, `json`, `os`, `sys`, `pathlib`). No external packages or internet connection required.

---

## 1. Features

- **100% Standalone & Portable:** Directly reads the local Stratos SQLite database in read-only mode (`%APPDATA%\Stratos\plugins-data\landing-analyser\landing-analyser.db`). Runs on any machine with Stratos installed without requiring external files or network access.
- **True Geometric Descent Rate:** Implements Stratos's exact 500 ms rolling linear regression algorithm (`Tn`) to calculate real-time geometric descent rate from AGL changes, alongside the simulator's raw instrument readout (`Sim VS`).
- **Exact Touchdown Alignment:** Identifies the precise touchdown frame at the initial `onGround = true` transition, recording the official landing rate.
- **Consistent Decimal Precision:** Enforces formatted float precision across all rows:
  - `AGL ft`, `Pitch °`, and `Bank °`: Formatted to 1 decimal place (including trailing `.0`).
  - `G-Force`: Formatted to 2 decimal places.
  - `Time`: High-resolution 3-decimal millisecond timestamps (e.g. `T−0.046s`).
- **Collision-Proof Filenames:** Exports files using UTC timestamp prefixes (`YYYY-MM-DD_HHMM DEP-ARR CALLSIGN.tsv`), ensuring unique filenames even when multiple flights share the same date, route, and callsign.
- **Companion Metadata:** Exports a comprehensive `.json` file alongside every `.tsv` containing complete landing metadata (runway, approach stability, flap settings, and coordinates).

---

## 2. Command-Line Usage

The exporter accepts three simple arguments:

### A. List All Flights in the Database (`?`)
Displays a formatted overview table of all flights recorded in Stratos:
```bash
python export_stratos.py ?
```
**Example Output:**
```text
Available Stratos Flight Logs (44 total):
Idx  Date & Time (UTC)    Callsign   Route          Aircraft Frames 
-----------------------------------------------------------------
1    2026-10-03 20:37:06  WAT494     PANC->PAEN     DHC6     490    
2    2026-10-03 22:08:12  WAT3931    PAEN->PAKL     DHC6     491    
...
44   2026-10-24 22:27:01  WAT7003    ENSA->ENAS     DHC6     494    
```

### B. Export All Flights (`*`)
Batch exports every flight in the database into the `stratos_logs/` subfolder:
```bash
python export_stratos.py "*"
```

### C. Export a Specific Flight by Callsign
Filters and exports only flights matching the specified callsign (case-insensitive):
```bash
python export_stratos.py WAT7789
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
- Summary wind data is preserved in the companion `.json` metadata file rather than duplicated across the telemetry table.
