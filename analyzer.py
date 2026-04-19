import json
import glob
import re
import csv
import os

def calculate_zscores(data_list, key):
    values = [d[key] for d in data_list]
    if not values: return
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    std = variance ** 0.5
    for d in data_list:
        if std > 0:
            d[f"{key}_zscore"] = (d[key] - mean) / std
        else:
            d[f"{key}_zscore"] = 0.0

def analyze():
    print("Scanning for reading_report_session_*.json files...")
    files = glob.glob("reading_report_session_*.json")
    if not files:
        print("No JSON session reports found!")
        return

    all_region_data = []

    for fpath in files:
        print(f"Processing {fpath}...")
        with open(fpath, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: Could not parse {fpath}")
                continue

        exp_info = data.get("experiment_info", {})
        session_id = exp_info.get("session_id", "Unknown")
        user_id = exp_info.get("user_id", "Unknown")

        for trial in data.get("trials", []):
            code_id = trial.get("code_id", "Unknown")
            
            for rm in trial.get("region_metrics", []):
                region_name = rm.get("code_region", "")
                
                # Extract line length from: "Function_Def [12-25]"
                lines = 1
                match = re.search(r'\[(\d+)-(\d+)\]', region_name)
                if match:
                    start = int(match.group(1))
                    end = int(match.group(2))
                    lines = max(1, end - start + 1)
                
                fixations = rm.get("fixation_count", 0)
                reading_time = rm.get("reading_time_sec", 0.0)
                regressions = rm.get("regression_count", 0)
                
                # Normalization
                fix_density = fixations / lines
                time_density = reading_time / lines

                all_region_data.append({
                    "session_id": session_id,
                    "user_id": user_id,
                    "code_id": code_id,
                    "code_region": region_name,
                    "region_lines": lines,
                    "raw_reading_time_sec": reading_time,
                    "raw_fixations": fixations,
                    "raw_regressions": regressions,
                    "fixation_density": round(fix_density, 3),
                    "normalized_time": round(time_density, 3),
                })
                
    if not all_region_data:
        print("No valid region data found in files!")
        return
        
    # Calculate global Z-scores across the dataset for the complexity heuristic
    calculate_zscores(all_region_data, "fixation_density")
    calculate_zscores(all_region_data, "raw_regressions")
    
    # Calculate Composite Complexity Score: Z_FixationDensity + (Z_Regressions * 1.5)
    for d in all_region_data:
        # Standard code comprehension heuristic weight for regressions
        comp = d["fixation_density_zscore"] + (d["raw_regressions_zscore"] * 1.5)
        d["complexity_score"] = round(comp, 3)
        
    # Write to CSV
    csv_file = "master_analysis.csv"
    headers = [
        "session_id", "user_id", "code_id", "code_region", "region_lines",
        "raw_reading_time_sec", "raw_fixations", "raw_regressions",
        "fixation_density", "normalized_time", "complexity_score"
    ]
    
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(all_region_data)
        
    print(f"\nSUCCESS: Data aggregated! Wrote {len(all_region_data)} region records to {csv_file}.")

if __name__ == "__main__":
    analyze()
