import json
import glob
import re
import csv
import os
from collections import defaultdict

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
    print("\n" + "="*80)
    print("EYE TRACKING ANALYSIS SYSTEM")
    print("="*80)
    
    print("\nScanning for reading_report_session_*.json files in session_data/ directory...")
    files = glob.glob("session_data/reading_report_session_*.json")
    if not files:
        print("No JSON session reports found!")
        return

    all_region_data = []
    session_summaries = defaultdict(lambda: {"total_time": 0, "total_fixations": 0, "total_regressions": 0, "regions": 0, "gaze_points": 0})
    user_summaries = defaultdict(lambda: {"total_time": 0, "total_fixations": 0, "sessions": 0, "files": set()})
    file_summaries = defaultdict(lambda: {"total_time": 0, "total_fixations": 0, "regions": 0, "high_load_regions": []})

    for fpath in files:
        print(f"\nProcessing {fpath}...")
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
            gaze_points = trial.get("gaze_points", [])
            most_fixated = trial.get("most_fixated_region", "N/A")
            
            # Track session statistics
            session_summaries[session_id]["files"] = session_id
            user_summaries[user_id]["files"].add(code_id)
            user_summaries[user_id]["sessions"] += 1
            
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
                cc = rm.get("static_cognitive_complexity", 1)  # SonarSource Rules
                
                # Normalization
                fix_density = fixations / lines
                time_density = reading_time / lines

                all_region_data.append({
                    "session_id": session_id,
                    "user_id": user_id,
                    "code_id": code_id,
                    "code_region": region_name,
                    "region_lines": lines,
                    "static_cognitive_complexity": cc,
                    "raw_reading_time_sec": reading_time,
                    "raw_fixations": fixations,
                    "raw_regressions": regressions,
                    "fixation_density": round(fix_density, 3),
                    "normalized_time": round(time_density, 3),
                })
                
                # Update summaries
                session_summaries[session_id]["total_time"] += reading_time
                session_summaries[session_id]["total_fixations"] += fixations
                session_summaries[session_id]["total_regressions"] += regressions
                session_summaries[session_id]["regions"] += 1
                session_summaries[session_id]["gaze_points"] = len(gaze_points)
                
                user_summaries[user_id]["total_time"] += reading_time
                user_summaries[user_id]["total_fixations"] += fixations
                
                file_summaries[code_id]["total_time"] += reading_time
                file_summaries[code_id]["total_fixations"] += fixations
                file_summaries[code_id]["regions"] += 1
                
    if not all_region_data:
        print("No valid region data found in files!")
        return
        
    # Calculate global Z-scores across the dataset for the complexity heuristic
    calculate_zscores(all_region_data, "fixation_density")
    calculate_zscores(all_region_data, "raw_regressions")
    
    # Calculate Composite Complexity Score: Z_FixationDensity + (Z_Regressions * weight)
    # Weight can be empirically derived via factor analysis or set based on theoretical rationale
    regression_weight = 1.5  # TODO: Empirically validate this weight

    raw_scores = []
    for d in all_region_data:
        comp = d["fixation_density_zscore"] + (d["raw_regressions_zscore"] * regression_weight)
        raw_scores.append(comp)
        
    if raw_scores:
        min_comp = min(raw_scores)
        max_comp = max(raw_scores)
        range_comp = max_comp - min_comp
        
        for i, d in enumerate(all_region_data):
            if range_comp > 0:
                scaled = ((raw_scores[i] - min_comp) / range_comp) * 100
            else:
                scaled = 50.0 # Default if everything is identical
            d["eye_tracking_cognitive_load"] = round(scaled, 1)
        
    # Write to CSV
    csv_file = "master_analysis.csv"
    headers = [
        "session_id", "user_id", "code_id", "code_region", "region_lines",
        "static_cognitive_complexity", "raw_reading_time_sec", "raw_fixations", "raw_regressions",
        "fixation_density", "normalized_time", "eye_tracking_cognitive_load"
    ]
    
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(all_region_data)
        
    print(f"\n✓ Data aggregated! Wrote {len(all_region_data)} region records to {csv_file}.")
    
    # ========== COMPREHENSIVE ANALYSIS REPORT ==========
    print("\n" + "="*80)
    print("COMPREHENSIVE ANALYSIS REPORT")
    print("="*80)
    
    # Session-level analysis
    print("\n📊 SESSION-LEVEL SUMMARY:")
    print("-" * 80)
    for sid, summary in sorted(session_summaries.items()):
        print(f"  Session {sid}:")
        print(f"    - Total Reading Time: {summary['total_time']:.2f}s")
        print(f"    - Total Fixations: {summary['total_fixations']}")
        print(f"    - Total Regressions: {summary['total_regressions']}")
        print(f"    - Regions Analyzed: {summary['regions']}")
        if summary['gaze_points'] > 0:
            print(f"    - Gaze Points Collected: {summary['gaze_points']}")
    
    # User-level analysis
    print("\n👤 USER-LEVEL SUMMARY:")
    print("-" * 80)
    for uid, summary in sorted(user_summaries.items()):
        print(f"  User {uid}:")
        print(f"    - Sessions Completed: {summary['sessions']}")
        print(f"    - Files Analyzed: {len(summary['files'])}")
        print(f"    - Total Reading Time: {summary['total_time']:.2f}s")
        print(f"    - Total Fixations: {summary['total_fixations']}")
    
    # Code file analysis
    print("\n📁 CODE FILE ANALYSIS:")
    print("-" * 80)
    for code_id, summary in sorted(file_summaries.items()):
        print(f"  {code_id}:")
        print(f"    - Regions: {summary['regions']}")
        print(f"    - Total Reading Time: {summary['total_time']:.2f}s")
        print(f"    - Total Fixations: {summary['total_fixations']}")
        print(f"    - Avg Time per Region: {summary['total_time'] / summary['regions']:.2f}s")
    
    # Top and bottom difficulty regions
    print("\n🔥 COGNITIVE LOAD ANALYSIS:")
    print("-" * 80)
    sorted_by_load = sorted(all_region_data, key=lambda x: x["eye_tracking_cognitive_load"], reverse=True)
    
    print("  ⚠️  TOP 5 MOST COGNITIVELY DEMANDING REGIONS:")
    for i, region in enumerate(sorted_by_load[:5], 1):
        print(f"    {i}. {region['code_region']} (Load: {region['eye_tracking_cognitive_load']:.1f})")
        print(f"       - Fixations: {region['raw_fixations']}, Regressions: {region['raw_regressions']}")
        print(f"       - Reading Time: {region['raw_reading_time_sec']:.2f}s, Static CC: {region['static_cognitive_complexity']}")
    
    print("\n  ✅ TOP 5 LEAST COGNITIVELY DEMANDING REGIONS:")
    for i, region in enumerate(sorted_by_load[-5:], 1):
        print(f"    {i}. {region['code_region']} (Load: {region['eye_tracking_cognitive_load']:.1f})")
    
    # Regression analysis
    print("\n⏮️  REGRESSION ANALYSIS:")
    print("-" * 80)
    total_regressions = sum(r["raw_regressions"] for r in all_region_data)
    regions_with_regressions = len([r for r in all_region_data if r["raw_regressions"] > 0])
    print(f"  Total Regressions: {total_regressions}")
    print(f"  Regions with Regressions: {regions_with_regressions} out of {len(all_region_data)}")
    if total_regressions > 0:
        avg_regression_per_region = total_regressions / regions_with_regressions if regions_with_regressions > 0 else 0
        print(f"  Average Regressions per Region (where regressions occur): {avg_regression_per_region:.2f}")
    
    # Fixation density analysis
    print("\n👁️  FIXATION DENSITY ANALYSIS:")
    print("-" * 80)
    avg_fixation_density = sum(r["fixation_density"] for r in all_region_data) / len(all_region_data)
    avg_time_density = sum(r["normalized_time"] for r in all_region_data) / len(all_region_data)
    print(f"  Average Fixation Density (fixations/line): {avg_fixation_density:.3f}")
    print(f"  Average Time Density (seconds/line): {avg_time_density:.3f}")
    
    print("\n" + "="*80)
    print("Analysis complete! Results saved to master_analysis.csv")
    print("="*80 + "\n")

if __name__ == "__main__":
    analyze()
