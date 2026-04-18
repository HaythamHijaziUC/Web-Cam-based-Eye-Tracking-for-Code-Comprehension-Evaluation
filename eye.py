import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import os
import json
import glob

from code_viewer import load_code_lines, render_code
from gaze_logger import GazeLogger
from heatmap import generate_heatmap

CALIB_FILE = "vertical_calib.npy"

# ---------------------------------------------------------
# Helper: session numbering
# ---------------------------------------------------------
def get_next_session_number():
    files = glob.glob("reading_report_session_*.json")
    if not files:
        return 1
    nums = []
    for f in files:
        try:
            n = int(f.split("_")[-1].split(".")[0])
            nums.append(n)
        except:
            pass
    return max(nums) + 1

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
# Load or run calibration
# ---------------------------------------------------------
screen_w, screen_h = pyautogui.size()

if os.path.exists(CALIB_FILE):
    calib_vals = np.load(CALIB_FILE)
    calib_top, calib_bottom = float(calib_vals[0]), float(calib_vals[1])
else:
    calib_top, calib_bottom = run_vertical_calibration(screen_w, screen_h)

# ---------------------------------------------------------
# Load code and render
# ---------------------------------------------------------
code_path = "example_code.py"
if not os.path.exists(code_path):
    with open(code_path, "w", encoding="utf-8") as f:
        f.write("print('example code')\n")

lines = load_code_lines(code_path)
code_img, line_regions = render_code(lines)
code_img = cv2.resize(code_img, (screen_w, screen_h))

region_height = screen_h // 3
semantic_pixel_regions = [
    ("Region 1", 0, region_height),
    ("Region 2", region_height, region_height * 2),
    ("Region 3", region_height * 2, screen_h)
]

# ---------------------------------------------------------
# Fullscreen code viewer
# ---------------------------------------------------------
win = "Code"
cv2.namedWindow(win, cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty(win, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
cv2.imshow(win, code_img)

# ---------------------------------------------------------
# Main gaze loop
# ---------------------------------------------------------
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)
cap = cv2.VideoCapture(0)

prev_nx, prev_ny = None, None
alpha_smooth = 0.25

logger = GazeLogger()
gaze_points = []

while True:
    ret, frame = cap.read()
    if not ret:
        break

    h, w = frame.shape[:2]
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)

    if results.multi_face_landmarks:
        mesh = results.multi_face_landmarks[0]
        landmarks = np.array([(lm.x * w, lm.y * h) for lm in mesh.landmark])

        nx_raw, ny_raw = compute_raw_gaze(landmarks, w, h)

        # Invert X to match screen orientation
        nx_raw = 1.0 - nx_raw

        # Vertical calibration
        ny_cal = (ny_raw - calib_top) / (calib_bottom - calib_top)
        ny_cal = float(np.clip(ny_cal, 0, 1))
        nx_raw = float(np.clip(nx_raw, 0, 1))

        # Temporal smoothing
        if prev_nx is None:
            prev_nx, prev_ny = nx_raw, ny_cal
        else:
            nx = alpha_smooth * nx_raw + (1 - alpha_smooth) * prev_nx
            ny = alpha_smooth * ny_cal + (1 - alpha_smooth) * prev_ny
            prev_nx, prev_ny = nx, ny
            nx_raw, ny_cal = nx, ny

        sx = int(nx_raw * (screen_w - 1))
        sy = int(ny_cal * (screen_h - 1))

        gaze_points.append((sx, sy))

        for name, y1, y2 in semantic_pixel_regions:
            if y1 <= sy <= y2:
                logger.log_region(name)
                break

        overlay = code_img.copy()
        cv2.circle(overlay, (sx, sy), 15, (0, 0, 255), -1)
        cv2.imshow(win, overlay)

    if cv2.waitKey(1) & 0xFF in (27, ord('q')):
        break

cap.release()
cv2.destroyAllWindows()

# ---------------------------------------------------------
# Summary + JSON + Wide Dashboard
# ---------------------------------------------------------
region_seconds, region_fixations, regressions = logger.summarize()

if region_seconds:
    most_fixated_region = max(region_seconds, key=region_seconds.get)
else:
    most_fixated_region = None

session_num = get_next_session_number()
report_filename = f"reading_report_session_{session_num}.json"

report = {
    "session": session_num,
    "regions": {
        region: {
            "fixation_time_sec": float(f"{region_seconds.get(region, 0):.3f}"),
            "fixations": int(region_fixations.get(region, 0)),
            "regressions": int(regressions.get(region, 0))
        }
        for region in ["Region 1", "Region 2", "Region 3"]
    },
    "most_fixated_region": most_fixated_region
}

with open(report_filename, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)

if gaze_points:
    heat = generate_heatmap(code_img, gaze_points)

    # region boundaries on heatmap
    cv2.line(heat, (0, region_height), (screen_w, region_height), (255,255,255), 2)
    cv2.line(heat, (0, region_height*2), (screen_w, region_height*2), (255,255,255), 2)

    panel_width = 600
    panel = np.zeros((heat.shape[0], panel_width, 3), dtype=np.uint8)

    H = panel.shape[0]
    W = panel.shape[1]

    bar_top = 0
    bar_bottom = H // 3
    line_top = bar_bottom
    line_bottom = 2 * H // 3
    text_top = line_bottom
    text_bottom = H

    # ---------------- BAR CHART ----------------
    bar_area = panel[bar_top:bar_bottom, :]
    max_sec = max(region_seconds.values()) if region_seconds else 0.0
    margin = 60
    base_y = bar_bottom - bar_top - 40
    bar_w = 60
    gap = 80
    start_x = margin

    cv2.putText(bar_area, "Fixation Time (s)", (20, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)

    if max_sec > 0:
        for i, region in enumerate(["Region 1", "Region 2", "Region 3"]):
            sec = region_seconds.get(region, 0.0)
            h_norm = sec / max_sec
            h_pix = int(h_norm * (base_y - 40))
            x1 = start_x + i * (bar_w + gap)
            x2 = x1 + bar_w
            y1 = base_y
            y2 = base_y - h_pix
            color = (100 + i*50, 200 - i*40, 255 - i*60)
            cv2.rectangle(bar_area, (x1, y1), (x2, y2), color, -1)
            cv2.putText(bar_area, f"{sec:.1f}", (x1, y2 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)
            cv2.putText(bar_area, region.split()[-1], (x1+10, base_y+20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,200,200), 1)

    # ---------------- LINE CHART ----------------
    line_area = panel[line_top:line_bottom, :]
    cv2.putText(line_area, "Fixation Sequence", (20, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)

    seq = getattr(logger, "fixation_sequence", [])
    region_order = {"Region 1": 1, "Region 2": 2, "Region 3": 3}

    if len(seq) >= 2:
        h_line = line_bottom - line_top
        w_line = W
        x_step = w_line / max(1, len(seq) - 1)
        pts = []
        for i, r in enumerate(seq):
            x = int(i * x_step)
            level = region_order.get(r, 1)
            y = int(h_line - (level - 1) * (h_line / 3) - h_line / 6)
            pts.append((x, y))
        for i in range(len(pts) - 1):
            cv2.line(line_area, pts[i], pts[i+1], (0,255,255), 2)
        for level, name in [(1,"R1"), (2,"R2"), (3,"R3")]:
            y = int(h_line - (level - 1) * (h_line / 3) - h_line / 6)
            cv2.putText(line_area, name, (10, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,200,200), 1)

    # ---------------- TEXT SUMMARY ----------------
    text_area = panel[text_top:text_bottom, :]
    y = 40
    line_h = 35

    cv2.putText(text_area, f"Session #{session_num}", (20, y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,255), 2)
    y += int(line_h * 1.5)

    cv2.putText(text_area, "Regressions:", (20, y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)
    y += line_h

    for region in ["Region 1", "Region 2", "Region 3"]:
        reg = regressions.get(region, 0)
        text = f"{region}: {reg}"
        cv2.putText(text_area, text, (40, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200,200,200), 2)
        y += line_h

    y += int(line_h * 0.5)
    if most_fixated_region:
        text = f"Most fixated: {most_fixated_region}"
    else:
        text = "Most fixated: None"

    cv2.putText(text_area, text, (20, y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,0), 2)

    combined = np.hstack([heat, panel])

    # Make sure dashboard window is visible and not fullscreen-hidden
    cv2.destroyAllWindows()
    cv2.namedWindow("Heatmap + Dashboard", cv2.WINDOW_NORMAL)
    cv2.moveWindow("Heatmap + Dashboard", 100, 100)

    cv2.imshow("Heatmap + Dashboard", combined)
    cv2.waitKey(0)
