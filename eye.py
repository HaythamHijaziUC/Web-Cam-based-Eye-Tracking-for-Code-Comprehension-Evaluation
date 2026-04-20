import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import os
import json
import glob
import time
import tkinter as tk
from tkinter import filedialog
from datetime import datetime
from pathlib import Path

from code_viewer import load_code_lines, render_code
from gaze_logger import GazeLogger
from heatmap import generate_heatmap, draw_fixation_clusters
from semantic_parser import parse_semantic_regions
from cognitive_complexity import extract_full_file_complexity, compute_region_complexity
import analyzer

# Import new modules
from src.ui.user_selection import show_user_selection_screen, UserManager
from src.calibration.calibrator import Calibrator
from src.metrics.cognitive_load import CognitiveLoadCalculator
from src.ui.nasa_tlx_survey import NasaTlxSurvey
from src.validation.data_exporter import DataExporter

CALIB_FILE = "vertical_calib.npy"

# ---------------------------------------------------------
# Helper: session numbering
# ---------------------------------------------------------
def get_next_session_number():
    os.makedirs("session_data", exist_ok=True)
    files = glob.glob("session_data/reading_report_session_*.json")
    if not files:
        return 1
    nums = []
    for f in files:
        try:
            # Use basename to avoid path issues
            basename = os.path.basename(f)
            # Extract session number from "reading_report_session_X_user_Y.json"
            parts = basename.split("_")
            session_part = None
            for i, part in enumerate(parts):
                if part == "session" and i + 1 < len(parts):
                    session_part = parts[i + 1]
                    break
            if session_part:
                n = int(session_part)
                nums.append(n)
        except:
            pass
    return max(nums) + 1 if nums else 1

# ---------------------------------------------------------
# Gaze computation (raw) with amplified iris + reduced head
# ---------------------------------------------------------
LEFT_EYE = [33, 133, 159, 145, 160, 144]
RIGHT_EYE = [362, 263, 386, 374, 387, 373]

def eye_center(landmarks, idxs):
    return landmarks[idxs].mean(axis=0)

def compute_raw_gaze(landmarks, w, h):
    # Face center (head pose proxy)
    face_center = landmarks.mean(axis=0)
    fx = face_center[0] / w
    fy = face_center[1] / h

    # Eye center (iris / eye proxy)
    left_c = eye_center(landmarks, LEFT_EYE)
    right_c = eye_center(landmarks, RIGHT_EYE)
    eyes_c = (left_c + right_c) / 2.0
    ex = eyes_c[0] / w
    ey = eyes_c[1] / h

    # Head mapping
    head_x = np.clip(0.5 + (fx - 0.5) * 2.2, 0, 1)
    head_y = np.clip(0.5 + (fy - 0.5) * 2.2, 0, 1)

    # --- Improved hybrid gaze ---

    # 1. Raw eye + head
    nx_eye = ex
    ny_eye = ey
    nx_head = head_x
    ny_head = head_y

    # 2. Amplify iris movement
    iris_gain = 2.8  # you can tune 2.0–4.0
    nx_eye_amp = (nx_eye - 0.5) * iris_gain + 0.5
    ny_eye_amp = (ny_eye - 0.5) * iris_gain + 0.5

    # 3. Reduce head influence
    nx_mix = 0.85 * nx_eye_amp + 0.15 * nx_head
    ny_mix = 0.85 * ny_eye_amp + 0.15 * ny_head

    # 4. Nonlinear expansion (more control near center)
    def expand(v, strength=1.35):
        return (v - 0.5) * strength + 0.5

    nx_final = expand(nx_mix, 1.35)
    ny_final = expand(ny_mix, 1.35)

    # 5. Clamp
    nx_final = float(np.clip(nx_final, 0, 1))
    ny_final = float(np.clip(ny_final, 0, 1))

    return nx_final, ny_final

# ---------------------------------------------------------
# One-time vertical calibration
# ---------------------------------------------------------
def run_vertical_calibration(screen_w, screen_h):
    print("Starting vertical calibration...")

    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)
    cap = cv2.VideoCapture(0)

    win = "Calibration"
    cv2.namedWindow(win, cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty(win, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    phase = "top"
    calib_top = None
    calib_bottom = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)

        ny_raw = None
        if results.multi_face_landmarks:
            mesh = results.multi_face_landmarks[0]
            landmarks = np.array([(lm.x * w, lm.y * h) for lm in mesh.landmark])
            _, ny_raw = compute_raw_gaze(landmarks, w, h)

        black = np.zeros((screen_h, screen_w, 3), dtype=np.uint8)
        if phase == "top":
            text = "Calibration: Look at TOP, press SPACE"
        else:
            text = "Calibration: Look at BOTTOM, press SPACE"

        cv2.putText(black, text, (50, screen_h // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255,255,255), 2)
        cv2.imshow(win, black)

        key = cv2.waitKey(1) & 0xFF
        if key == 27:
            break
        if key == 32 and ny_raw is not None:
            if phase == "top":
                calib_top = ny_raw
                print("Captured TOP:", calib_top)
                phase = "bottom"
            else:
                calib_bottom = ny_raw
                print("Captured BOTTOM:", calib_bottom)
                break

    cap.release()
    cv2.destroyWindow(win)

    if calib_top is None or calib_bottom is None:
        print("Calibration failed. Using defaults.")
        return 0.0, 1.0

    if calib_bottom <= calib_top:
        calib_top, calib_bottom = calib_bottom, calib_top

    np.save(CALIB_FILE, np.array([calib_top, calib_bottom], dtype=np.float32))
    print("Calibration saved.")
    return calib_top, calib_bottom

# ---------------------------------------------------------
# NEW: User Selection and Calibration System
# ---------------------------------------------------------
screen_w, screen_h = pyautogui.size()
print(f"Screen resolution: {screen_w}x{screen_h}")

# Show user selection screen
print("\n" + "="*70)
print("LAUNCHING USER SELECTION SCREEN")
print("="*70)

user_info = show_user_selection_screen()
if user_info is None:
    print("User selection cancelled. Exiting.")
    exit(0)

user_id = user_info['user_id']
is_new_user = user_info['is_new_user']
recalibrate = user_info.get('recalibrate', False)

print(f"\n✓ User selected: {user_id}")
print(f"  New user: {is_new_user}")
print(f"  Recalibrate: {recalibrate}")

# Initialize user manager for calibration storage
user_manager = UserManager()

# Determine if we need to calibrate
need_calibration = is_new_user or recalibrate
preloaded_calibration = user_info.get('calibration_data', None)

if need_calibration:
    print("\n" + "="*70)
    print("STARTING 9-POINT CALIBRATION")
    print("="*70)
    
    calibrator = Calibrator(screen_w=screen_w, screen_h=screen_h)
    calib_data = calibrator.run_calibration()
    
    if calib_data is not None:
        # Validate calibration
        is_valid, val_message = calibrator.validate_calibration(calib_data)
        print(f"\nCalibration validation: {val_message}")
        
        if is_valid:
            # Save calibration
            user_manager.save_user_calibration(user_id, calib_data)
            print(f"✓ Calibration saved for user {user_id}")
            print(f"  Mean error: {calib_data['mean_error_px']:.1f}px")
            print(f"  Accuracy: {calib_data['accuracy_score']:.1f}%")
            calibration_matrix = np.array(calib_data['calibration_matrix'])
            calib_accuracy = calib_data['accuracy_score']
        else:
            print("✗ Calibration validation failed. Using identity matrix.")
            calibration_matrix = np.eye(2, 3)
            calib_accuracy = 0.0
    else:
        print("Calibration cancelled.")
        calibration_matrix = np.eye(2, 3)
        calib_accuracy = 0.0
else:
    print("\n" + "="*70)
    print("USING STORED CALIBRATION")
    print("="*70)
    
    # Use preloaded calibration from user selection
    if preloaded_calibration:
        calib_data = preloaded_calibration
        print(f"✓ Calibration preloaded for user {user_id}")
    else:
        calib_data = user_manager.load_user_calibration(user_id)
        print(f"✓ Calibration loaded for user {user_id}")
    
    if calib_data:
        calibration_matrix = np.array(calib_data['calibration_matrix'])
        calib_accuracy = calib_data['accuracy_score']
        print(f"  Accuracy: {calib_accuracy:.1f}%")
        age = user_manager.get_calibration_age_days(user_id)
        if age:
            print(f"  Age: {age} days old")
    else:
        print("⚠️ Could not load calibration. Using identity matrix.")
        calibration_matrix = np.eye(2, 3)
        calib_accuracy = 0.0

# Keep old vertical calibration values for backward compatibility
calib_top = 0.0
calib_bottom = 1.0

# Keep old vertical calibration values for backward compatibility
calib_top = 0.0
calib_bottom = 1.0

# Create a hidden Tkinter root window
root = tk.Tk()
root.withdraw()
root.wm_attributes('-topmost', 1)

# Open Native File Dialog
selected_code_path = filedialog.askopenfilename(
    title="Select Code File for Experiment",
    filetypes=[("Source Code", "*.py *.java *.cpp *.c *.ts *.js *.txt"), ("All Files", "*.*")]
)

root.destroy()

if not selected_code_path:
    print("No file selected! Exiting.")
    exit(0)

stimuli_files = [selected_code_path]
print(f"Selected file: {selected_code_path}")

# Screen init
win = "Code"
cv2.namedWindow(win, cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty(win, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FPS, 30)

prev_nx, prev_ny = None, None
alpha_smooth = 0.25
offset_x, offset_y = 0.0, 0.0

abort_session = False

for code_path in stimuli_files:
    # Each file gets its own session
    session_num = get_next_session_number()
    session_report = {
        "experiment_info": {
            "session_id": session_num,
            "user_id": user_id
        },
        "trials": []
    }
    
    print(f"Loading {code_path}...")
    lines = load_code_lines(code_path)
    code_img, line_regions = render_code(lines)
    code_img = cv2.resize(code_img, (screen_w, screen_h))

    with open(code_path, "r", encoding="utf-8") as f:
        code_content = f.read()

    ast_regions = parse_semantic_regions(code_content)
    cc_line_scores = extract_full_file_complexity(code_content)

    semantic_pixel_regions = []
    for region in ast_regions:
        raw_h = line_regions[-1][1] if line_regions else 1
        scale_y = screen_h / raw_h
        y_start = int(line_regions[region["start"]][0] * scale_y)
        y_end = int(line_regions[region["end"]][1] * scale_y)
        
        # Calculate strict Cognitive Complexity (SonarSource) inherited for this segment
        cc = compute_region_complexity(cc_line_scores, region["start"], region["end"])
        
        semantic_pixel_regions.append({
            "name": region["name"], "start": region["start"],
            "y1": max(0, y_start), "y2": min(screen_h, y_end),
            "cc": cc
        })

    logger = GazeLogger()
    gaze_points = []
    
    t0 = time.time()
    frame_count = 0
    fps_display = 0.0
    tracking_started = False
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)

        overlay = code_img.copy()
        for reg in semantic_pixel_regions:
            cv2.line(overlay, (0, reg["y1"]), (screen_w, reg["y1"]), (100, 100, 100), 1)

        face_detected = False

        if results.multi_face_landmarks:
            face_detected = True
            mesh = results.multi_face_landmarks[0]
            landmarks = np.array([(lm.x * w, lm.y * h) for lm in mesh.landmark])

            nx_raw, ny_raw = compute_raw_gaze(landmarks, w, h)
            nx_raw = 1.0 - nx_raw

            ny_cal = float(np.clip((ny_raw - calib_top) / (calib_bottom - calib_top), 0, 1))
            nx_raw = float(np.clip(nx_raw + offset_x, 0, 1))
            ny_cal = float(np.clip(ny_cal + offset_y, 0, 1))

            if prev_nx is None:
                prev_nx, prev_ny = nx_raw, ny_cal
            else:
                nx = alpha_smooth * nx_raw + (1 - alpha_smooth) * prev_nx
                ny = alpha_smooth * ny_cal + (1 - alpha_smooth) * prev_ny
                prev_nx, prev_ny = nx, ny
                nx_raw, ny_cal = nx, ny

            sx = int(nx_raw * (screen_w - 1))
            sy = int(ny_cal * (screen_h - 1))

            cv2.circle(overlay, (sx, sy), 15, (0, 0, 255), -1)

            if tracking_started:
                gaze_points.append((sx, sy))
                active_region = None
                for region in semantic_pixel_regions:
                    if region["y1"] <= sy <= region["y2"]:
                        active_region = region
                        break
                
                logger.log_region(active_region)

                frame_count += 1
                elapsed = time.time() - t0
                if elapsed >= 1.0:
                    fps_display = frame_count / elapsed
                    t0 = time.time()
                    frame_count = 0
                
                cv2.putText(overlay, f"FPS: {fps_display:.1f}", (screen_w - 150, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(overlay, "Press 'N' for next trial", (screen_w - 250, 80),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)

        if not face_detected:
            cv2.putText(overlay, "FACE NOT DETECTED", (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)

        if not tracking_started:
            cv2.putText(overlay, "STANDBY: Fixate on code and press SPACE.", 
                        (screen_w // 2 - 350, 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)

        cv2.imshow(win, overlay)

        key = cv2.waitKey(1) & 0xFF
        if key in (27, ord('q')):
            abort_session = True
            break
        elif key == ord(' '):
            if not tracking_started:
                tracking_started = True
                print("Tracking started!")
                logger = GazeLogger()
                t0 = time.time()
                frame_count = 0
                fps_display = 0.0
        elif key == ord('n'):
            if tracking_started:
                print(f"Finished trial: {code_path}")
                break
        elif key == ord('c'):
            print("Calibrating center point...")
            if prev_nx is not None:
                offset_x += (0.5 - prev_nx)
                offset_y += (0.5 - prev_ny)
                print(f"Drift corrected. New Offsets: X={offset_x:.2f}, Y={offset_y:.2f}")

    # Proceed to summary even if aborted to show final dashboard

    # Summarize this trial
    region_seconds, region_fixations, regressions, transitions = logger.summarize()
    most_fix = max(region_seconds, key=region_seconds.get) if region_seconds else None
    
    trial_data = {
        "code_id": os.path.basename(code_path),
        "most_fixated_region": most_fix,
        "transitions": transitions,
        "gaze_points": gaze_points,
        "region_metrics": []
    }
    
    # Flat format for statistical analysis (Pandas/SPSS) mapping over regions
    for r in region_seconds:
        cc_val = 1
        for reg in semantic_pixel_regions:
            if reg["name"] == r:
                cc_val = reg.get("cc", 1)
                break
                
        trial_data["region_metrics"].append({
            "code_region": r,
            "static_cognitive_complexity": cc_val,
            "fixation_count": int(region_fixations.get(r, 0)),
            "regression_count": int(regressions.get(r, 0)),
            "reading_time_sec": float(f"{region_seconds.get(r, 0):.3f}")
        })
        
    session_report["trials"].append(trial_data)

    # ---------------------------------------------------------
    # Draw Heatmap Dashboard for this Trial
    # ---------------------------------------------------------
    if gaze_points:
        heat = generate_heatmap(code_img, gaze_points)
        # Add fixation clustering overlay
        try:
            heat, cluster_stats = draw_fixation_clusters(heat, gaze_points, eps=50, min_samples=3)
            print(f"Fixation clusters detected: {len(cluster_stats)} regions")
        except Exception as e:
            print(f"Clustering visualization skipped: {e}")
    else:
        # If no gaze points, create a blank heatmap
        heat = code_img.copy()
        cv2.putText(heat, "NO GAZE DATA RECORDED", (screen_w // 2 - 200, screen_h // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)

    for reg in semantic_pixel_regions:
        cv2.line(heat, (0, reg["y1"]), (screen_w, reg["y1"]), (255,255,255), 2)

        panel_width = 600
        panel = np.zeros((heat.shape[0], panel_width, 3), dtype=np.uint8)
        H, W = panel.shape[0], panel.shape[1]

        bar_top, bar_bottom = 0, H // 3
        line_top, line_bottom = bar_bottom, 2 * H // 3
        text_top, text_bottom = line_bottom, H

        # BAR CHART
        bar_area = panel[bar_top:bar_bottom, :]
        max_sec = max(region_seconds.values()) if region_seconds else 0.0
        base_y = bar_bottom - bar_top - 40
        start_x, bar_w, gap = 60, 60, 80

        cv2.putText(bar_area, "Fixation Time (s)", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)

        if max_sec > 0:
            for i, reg in enumerate(semantic_pixel_regions):
                if i >= 5: break
                name = reg["name"]
                sec = region_seconds.get(name, 0.0)
                h_pix = int((sec / max_sec) * (base_y - 40))
                x1 = start_x + i * (bar_w + gap)
                x2, y1, y2 = x1 + bar_w, base_y, base_y - h_pix
                cv2.rectangle(bar_area, (x1, y1), (x2, y2), (100+i*30, 200-i*20, 255-i*40), -1)
                cv2.putText(bar_area, f"{sec:.1f}", (x1, y2 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)
                cv2.putText(bar_area, name.split(":")[-1].strip()[:10], (x1, base_y+20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200,200,200), 1)

        # LINE CHART
        line_area = panel[line_top:line_bottom, :]
        cv2.putText(line_area, "Fixation Sequence", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)
        seq = getattr(logger, "fixation_sequence", [])
        region_order = {reg["name"]: i+1 for i, reg in enumerate(semantic_pixel_regions)}
        num_regs = len(semantic_pixel_regions)

        if len(seq) >= 2 and num_regs > 0:
            h_line = line_bottom - line_top
            x_step = W / max(1, len(seq) - 1)
            pts = []
            for i, meta in enumerate(seq):
                level = region_order.get(meta["name"], 1)
                y = int(h_line - (level - 1) * (h_line / (num_regs+1)) - h_line / (num_regs+1))
                pts.append((int(i * x_step), y))
            for i in range(len(pts) - 1):
                cv2.line(line_area, pts[i], pts[i+1], (0,255,255), 2)
            for name, level in region_order.items():
                if level > 5: break
                y = int(h_line - (level - 1) * (h_line / (num_regs+1)) - h_line / (num_regs+1))
                cv2.putText(line_area, name.split(":")[-1].strip()[:5], (5, y), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200,200,200), 1)

        # TEXT SUMMARY
        text_area = panel[text_top:text_bottom, :]
        y, line_h = 40, 35
        cv2.putText(text_area, f"File: {os.path.basename(code_path)[:15]}", (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 2)
        y += int(line_h * 1.5)
        cv2.putText(text_area, "Regressions:", (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)
        y += line_h
        for reg in semantic_pixel_regions[:4]:
            text = f"{reg['name'].split(':')[-1][:10]}: {regressions.get(reg['name'], 0)}"
            cv2.putText(text_area, text, (40, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200,200,200), 2)
            y += line_h

        y += int(line_h * 0.5)
        cv2.putText(text_area, f"Most fixated: {most_fix or 'None'}", (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,0), 2)

        combined = np.hstack([heat, panel])

        # Save heatmap visual to disk
        base_name = os.path.basename(code_path)
        os.makedirs("session_data", exist_ok=True)
        img_name = f"session_data/heatmap_session_{session_num}_user_{user_id}_{base_name}.png"
        cv2.imwrite(img_name, combined)
        print(f"Heatmap saved to {img_name}")

        cv2.destroyAllWindows()
        cv2.namedWindow("Heatmap + Dashboard", cv2.WINDOW_NORMAL)
        cv2.moveWindow("Heatmap + Dashboard", 100, 100)
        cv2.imshow("Heatmap + Dashboard", combined)
        
        print("Displaying dashboard. Press any key or close the window to continue to the next file...")
        while True:
            key = cv2.waitKey(100) & 0xFF
            # Check if window is still open
            if cv2.getWindowProperty("Heatmap + Dashboard", cv2.WND_PROP_VISIBLE) < 1:
                break
            # Check for keyboard press
            if key != 255:
                break
        try:
            cv2.destroyWindow("Heatmap + Dashboard")
        except:
            pass
        
        # Re-initialize fullscreen for the next file
        cv2.namedWindow(win, cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty(win, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    # Save this session's JSON
    os.makedirs("session_data", exist_ok=True)
    report_filename = f"session_data/reading_report_session_{session_num}_user_{user_id}.json"
    with open(report_filename, "w", encoding="utf-8") as f:
        json.dump(session_report, f, indent=2)

    print(f"Session {session_num} complete! Data saved to {report_filename}")

    # ---------------------------------------------------------
    # NEW: NASA-TLX Workload Assessment
    # ---------------------------------------------------------
    print("\n" + "="*60)
    print("NASA-TLX Workload Assessment")
    print("="*60)
    
    try:
        tlx_survey = NasaTlxSurvey()
        tlx_response = tlx_survey.show_survey()
        
        if tlx_response:
            print("\nNASA-TLX Responses:")
            print(f"  Mental Demand: {tlx_response.mental_demand}/100")
            print(f"  Physical Demand: {tlx_response.physical_demand}/100")
            print(f"  Temporal Demand: {tlx_response.temporal_demand}/100")
            print(f"  Performance: {tlx_response.performance}/100")
            print(f"  Effort: {tlx_response.effort}/100")
            print(f"  Frustration: {tlx_response.frustration}/100")
            print(f"  Overall Workload: {tlx_response.overall_workload:.1f}/100")
        else:
            tlx_response = None
            print("NASA-TLX survey cancelled.")
    except Exception as e:
        print(f"Error running NASA-TLX survey: {e}")
        tlx_response = None

    # ---------------------------------------------------------
    # NEW: Cognitive Load Analysis with Validation Data Export
    # ---------------------------------------------------------
    print("\n" + "="*60)
    print("Cognitive Load Analysis")
    print("="*60)
    
    try:
        # Initialize cognitive load calculator
        calc = CognitiveLoadCalculator(weights_preset='default')
        
        # Prepare validation data for export
        exporter = DataExporter(output_dir="exports")
        validation_records = []
        
        # Process each region's metrics
        for region_metric in trial_data.get("region_metrics", []):
            # Get psychological metrics from region
            metrics = {
                'fixation_count': region_metric.get('fixation_count', 0),
                'regression_count': region_metric.get('regression_count', 0),
                'reading_time_sec': region_metric.get('reading_time_sec', 0.0),
                'static_complexity': region_metric.get('static_cognitive_complexity', 1),
            }
            
            # Calculate cognitive load
            num_gaze_samples = len(gaze_points)
            region_lines = 1  # Approximate for this code region
            
            result = calc.calculate(
                metrics, 
                num_data_points=max(30, num_gaze_samples),  # Min 30 data points for stability
                region_lines=region_lines
            )
            
            # Build validation record
            record = {
                'timestamp': datetime.now().isoformat(),
                'user_id': user_id,
                'session_id': session_num,
                'code_region': region_metric.get('code_region', 'unknown'),
                'region_lines': region_lines,
                'fixation_count': region_metric.get('fixation_count', 0),
                'fixation_density': region_metric.get('fixation_count', 0) / max(1, region_metric.get('reading_time_sec', 1)),
                'regression_count': region_metric.get('regression_count', 0),
                'regression_rate': region_metric.get('regression_count', 0) / max(1, region_metric.get('fixation_count', 1)),
                'reading_time_sec': region_metric.get('reading_time_sec', 0.0),
                'mean_fixation_duration_ms': 0 if metrics['fixation_count'] == 0 else (metrics['reading_time_sec'] * 1000) / metrics['fixation_count'],
                'static_cognitive_complexity': region_metric.get('static_cognitive_complexity', 1),
                'eye_tracking_cognitive_load_score': result.score,
                'cognitive_load_confidence': result.confidence,
                'nasa_tlx_mental_demand': tlx_response.mental_demand if tlx_response else 0,
                'nasa_tlx_physical_demand': tlx_response.physical_demand if tlx_response else 0,
                'nasa_tlx_temporal_demand': tlx_response.temporal_demand if tlx_response else 0,
                'nasa_tlx_performance': tlx_response.performance if tlx_response else 0,
                'nasa_tlx_effort': tlx_response.effort if tlx_response else 0,
                'nasa_tlx_frustration': tlx_response.frustration if tlx_response else 0,
                'nasa_tlx_overall_workload': tlx_response.overall_workload if tlx_response else 0,
                'comprehension_correct': True,  # Would need actual comprehension test
                'response_time_ms': int(region_metric.get('reading_time_sec', 0) * 1000),
                'calibration_accuracy': calib_accuracy,
                'notes': f"Session {session_num}, Task: {os.path.basename(code_path)}"
            }
            
            validation_records.append(record)
            
            # Print cognitive load result
            print(f"\nRegion: {region_metric.get('code_region', 'unknown')}")
            print(f"  Cognitive Load Score: {result.score:.1f}/100")
            print(f"  Confidence: {result.confidence:.1%}")
            print(f"  Interpretation: {calc.get_interpretation(result.score)}")
            if result.warnings:
                print(f"  Warnings: {', '.join(result.warnings)}")
        
        # Export validation data
        if validation_records:
            csv_path = exporter.export_validation_data(
                validation_records, 
                f"validation_export_session_{session_num}_user_{user_id}.csv"
            )
            print(f"\n✓ Validation data exported to: {csv_path}")
        
    except Exception as e:
        print(f"Error in cognitive load analysis: {e}")
        import traceback
        traceback.print_exc()

    if abort_session:
        break

cap.release()
cv2.destroyAllWindows()

# ---------------------------------------------------------
# Save Session JSON & Sync CSV
# ---------------------------------------------------------
print("\n--- Synchronizing Master CSV Dataset ---")
try:
    analyzer.analyze()
except Exception as e:
    print(f"Error updating CSV: {e}")
