import os
import sys
import json
import sqlite3
from pathlib import Path

DB_PATH = os.path.expandvars(r"%APPDATA%\Stratos\plugins-data\landing-analyser\landing-analyser.db")
OUTPUT_DIR = Path(__file__).resolve().parent / "stratos_logs"


def get_all_reports():
    """Fetches all reports from Stratos DB in read-only mode."""
    if not os.path.exists(DB_PATH):
        print(f"Error: Stratos database not found at '{DB_PATH}'")
        sys.exit(1)

    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    cur = conn.cursor()
    cur.execute("""
        SELECT id, flight_id, created_at, departure_icao, arrival_icao, aircraft_type, report_json, landing_rate_fpm
        FROM landing_reports
        ORDER BY created_at ASC
    """)
    rows = cur.fetchall()
    conn.close()
    return rows


def compute_geometric_descent_fpm(frames, idx, td_index=None, landing_rate_fpm=None, window_ms=500):
    """
    Computes the geometric descent rate (fpm) from gear-AGL changes using a
    500ms rolling linear regression matching Stratos's Tn algorithm.
    """
    if td_index is not None and idx == td_index and landing_rate_fpm is not None:
        val = round(landing_rate_fpm)
        return f"+{val}" if val > 0 else f"{val}"

    cur_t = frames[idx]["t"]
    cur_gnd = frames[idx].get("onGround", False)
    min_t = cur_t - window_ms

    window = []
    p = idx
    while p >= 0:
        f = frames[p]
        if f["t"] < min_t or f.get("onGround", False) != cur_gnd:
            break
        window.insert(0, f)
        p -= 1

    if len(window) < 5:
        return "—"
    u = window[0]["t"]
    if window[-1]["t"] - u < 100:
        return "—"

    n = len(window)
    avg_t = sum(f["t"] - u for f in window) / n
    avg_agl = sum(f["agl"] for f in window) / n

    numerator = 0.0
    denominator = 0.0
    for f in window:
        dt = (f["t"] - u) - avg_t
        d_agl = f["agl"] - avg_agl
        numerator += dt * d_agl
        denominator += dt * dt

    if denominator == 0:
        return "—"

    slope_fpm = (numerator / denominator) * 60000.0
    val = round(slope_fpm)
    return f"+{val}" if val > 0 else f"{val}"


def list_reports(rows):
    """Displays a formatted list of all available flights in the database."""
    print(f"\nAvailable Stratos Flight Logs ({len(rows)} total):")
    print(f"{'Idx':<4} {'Date & Time (UTC)':<20} {'Callsign':<10} {'Route':<14} {'Aircraft':<8} {'Frames':<7}")
    print("-" * 65)

    for idx, row in enumerate(rows, start=1):
        db_id, flight_id, created_at, dep, arr, aircraft, raw_json = row
        try:
            data = json.loads(raw_json)
            flight = data.get("flight", {})
            callsign = flight.get("callsign", "UNKNOWN")
            dep_icao = (flight.get("departureIcao") or dep or "DEP").upper()
            arr_icao = (flight.get("arrivalIcao") or arr or "ARR").upper()
            ac_icao = flight.get("aircraftIcao") or "N/A"
            frames = len(data.get("frameSamples", []))
            date_display = created_at[:19].replace("T", " ") if created_at else "UNKNOWN"

            print(f"{idx:<4} {date_display:<20} {callsign:<10} {dep_icao}->{arr_icao:<9} {ac_icao:<8} {frames:<7}")
        except Exception:
            continue
    print()


def fmt_float(val, decimals=1):
    if val == "" or val is None:
        return ""
    try:
        return f"{float(val):.{decimals}f}"
    except Exception:
        return str(val)


def export_single_report(row):
    """Exports one report row to TSV and JSON."""
    db_id, flight_id, created_at, dep, arr, aircraft, raw_json, landing_rate_fpm = row
    data = json.loads(raw_json)

    flight = data.get("flight", {})
    callsign = flight.get("callsign", "UNKNOWN")
    dep_icao = (flight.get("departureIcao") or dep or "DEP").upper()
    arr_icao = (flight.get("arrivalIcao") or arr or "ARR").upper()

    if created_at and len(created_at) >= 16:
        dt_prefix = f"{created_at[:10]}_{created_at[11:13]}{created_at[14:16]}"
    elif created_at:
        dt_prefix = created_at[:10]
    else:
        dt_prefix = "UNKNOWN"

    base_name = f"{dt_prefix} {dep_icao}-{arr_icao} {callsign}"

    flare_ms = (data.get("flareDurationSeconds", 4.0) or 4.0) * 1000.0

    frames = data.get("frameSamples", [])
    if not frames:
        print(f"Skipping {base_name}: No frame samples.")
        return False

    td_index = next((i for i, f in enumerate(frames) if f.get("onGround")), None)
    if td_index is None:
        td_index = frames.index(min(frames, key=lambda f: abs(f.get("t", 999999))))

    tsv_lines = ["Time\tPhase\tAGL ft\tDescent fpm\tSim VS\tIAS kt\tGS kt\tPitch °\tBank °\tG-Force\tOn Ground"]
    for idx, fr in enumerate(frames):
        t_ms = fr.get("t", 0)
        t_sec = t_ms / 1000.0
        t_str = f"T−{abs(t_sec):.3f}s" if t_ms < 0 else f"T+{t_sec:.3f}s"

        if idx == td_index:
            phase = "Touchdown"
        elif idx > td_index:
            phase = "Rollout"
        elif t_ms >= -flare_ms:
            phase = "Flare"
        else:
            phase = "Approach"

        agl = fmt_float(fr.get("agl"), 1)
        descent_fpm = compute_geometric_descent_fpm(frames, idx, td_index=td_index, landing_rate_fpm=landing_rate_fpm)
        vs = fr.get("vs", "")
        ias = fr.get("ias", "")
        gs = fr.get("gs", "")
        pitch = fmt_float(fr.get("pitch"), 1)
        bank = fmt_float(fr.get("bank"), 1)
        gforce = fmt_float(fr.get("gForce"), 2)
        on_gnd = fr.get("onGround", False)
        gnd_str = "true" if on_gnd else "false"

        tsv_lines.append(f"{t_str}\t{phase}\t{agl}\t{descent_fpm}\t{vs}\t{ias}\t{gs}\t{pitch}\t{bank}\t{gforce}\t{gnd_str}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    tsv_file = OUTPUT_DIR / f"{base_name}.tsv"
    tsv_file.write_text("\n".join(tsv_lines) + "\n", encoding="utf-8")

    json_file = OUTPUT_DIR / f"{base_name}.json"
    json_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    print(f"Exported: {base_name}.tsv ({len(frames)} frames)")
    return True


def main():
    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  python export_stratos.py ?          - List all available flight logs in database")
        print("  python export_stratos.py *          - Export all flight logs to 'stratos_logs/'")
        print("  python export_stratos.py <CALLSIGN> - Export matching callsign (e.g. WAT1234)")
        print()
        return

    arg = sys.argv[1].strip()
    rows = get_all_reports()

    if arg == "?":
        list_reports(rows)
        return

    if arg == "*":
        print(f"Exporting all {len(rows)} flights to '{OUTPUT_DIR.resolve()}'...\n")
        count = 0
        for row in rows:
            if export_single_report(row):
                count += 1
        print(f"\nDone! Exported {count} flights.")
        return

    # Filter by callsign
    target_callsign = arg.upper()
    matching_rows = []
    for r in rows:
        try:
            callsign = json.loads(r[6]).get("flight", {}).get("callsign", "").upper()
            if callsign == target_callsign:
                matching_rows.append(r)
        except Exception:
            continue

    if not matching_rows:
        print(f"\nNo flights found matching callsign '{target_callsign}'.")
        print("Run 'python export_stratos.py ?' to view all available callsigns.\n")
        return

    print(f"Found {len(matching_rows)} flight(s) matching '{target_callsign}':\n")
    for r in matching_rows:
        export_single_report(r)
    print(f"\nOutput saved in '{OUTPUT_DIR.resolve()}'.\n")


if __name__ == "__main__":
    main()
