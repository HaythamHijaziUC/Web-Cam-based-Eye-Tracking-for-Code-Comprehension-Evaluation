# Web-Cam based Eye-Tracking for Code Comprehension Evaluation

Webcam-based eye tracking for code comprehension experiments, combining:
- gaze and fixation logging,
- semantic code-region parsing,
- static cognitive complexity, and
- workload estimation/export for analysis workflows.

## Overview

The current pipeline in `main` is:
1. User selection (`new` vs `returning`) and calibration loading.
2. 9-point gaze calibration (for new users or recalibration).
3. Fullscreen code-reading session with gaze tracking.
4. Trial heatmap + fixation cluster dashboard generation.
5. Session JSON save (`session_data/`).
6. NASA-TLX survey capture.
7. Validation CSV export (`exports/`).
8. Global aggregation to `master_analysis.csv`.

## Current Features

### Eye Tracking and Session Flow
- MediaPipe + OpenCV webcam tracking (no dedicated hardware).
- Fullscreen code display with live gaze cursor.
- Smoothing and drift correction (`c` key during tracking).
- Automatic session numbering via `session_data/reading_report_session_*.json`.
- Start tracking with `SPACE`, finish trial with `n`, quit with `q`/`ESC`.

### User and Calibration System
- Simple user flow in `src/ui/user_selection.py`.
- User calibration persistence in `calibrations/<user_id>.pkl`.
- 9-point calibrator with validation checks in `src/calibration/calibrator.py`.
- Legacy calibration compatibility path is supported in `eye.py`.

### Code and Cognitive Analysis
- Semantic region extraction (`semantic_parser.py`).
- Static cognitive complexity scoring (`cognitive_complexity.py`).
- Region-level metrics: fixation count, regression count, reading time.
- Dataset-level cognitive load aggregation in `analyzer.py`:
  `Z(fixation_density) + 1.5 * Z(raw_regressions)`, scaled to 0-100.

### Workload and Export
- NASA-TLX survey UI (`src/ui/nasa_tlx_survey.py`).
- Configurable cognitive-load calculator (`src/metrics/cognitive_load.py`) with presets from `src/metrics/weights.json`.
- Validation CSV export (`src/validation/data_exporter.py`) to `exports/`.

## Project Structure

- `eye.py`: Main end-to-end experiment runner.
- `analyzer.py`: Aggregates all session JSON files into `master_analysis.csv` and prints summary.
- `gaze_logger.py`: Fixation and transition/regression logging.
- `heatmap.py`: Heatmap rendering and fixation cluster overlay.
- `code_viewer.py`: Code rendering and line-region mapping.
- `semantic_parser.py`: Semantic region detection.
- `cognitive_complexity.py`: Static complexity scoring.
- `src/ui/user_selection.py`: User selection and calibration loading/saving helpers.
- `src/calibration/calibrator.py`: 9-point calibration and validation logic.
- `src/ui/nasa_tlx_survey.py`: Post-task NASA-TLX questionnaire UI.
- `src/metrics/cognitive_load.py`: Multi-component cognitive load model.
- `src/validation/data_exporter.py`: Validation-ready CSV/JSON export helpers.
- `run_eyetracker.bat`: Windows launcher (configured for a local Anaconda env path).

## Installation

```bash
git clone https://github.com/HaythamHijaziUC/Web-Cam-based-Eye-Tracking-for-Code-Comprehension-Evaluation.git
cd Web-Cam-based-Eye-Tracking-for-Code-Comprehension-Evaluation
pip install -r requirements.txt
```

Dependencies (`requirements.txt`):
- `opencv-python`
- `mediapipe`
- `numpy`
- `pyautogui`
- `scikit-learn`

## Usage

### Run Experiment

```bash
python eye.py
```

On launch:
1. Choose new or returning user.
2. If needed, complete 9-point calibration.
3. Select a source file (`.py`, `.java`, `.cpp`, `.c`, `.ts`, `.js`, `.txt`).
4. Press `SPACE` to begin tracking.

### Runtime Controls

- `SPACE`: Start tracking.
- `n`: End current trial and continue.
- `c`: Drift correction (recenter).
- `q` or `ESC`: Quit session.

### Run Standalone Aggregation

```bash
python analyzer.py
```

## Outputs

- Session report JSON:
  `session_data/reading_report_session_<session>_user_<user>.json`
- Trial heatmap dashboard image:
  `session_data/heatmap_session_<session>_user_<user>_<filename>.png`
- Validation export CSV:
  `exports/validation_export_session_<session>_user_<user>.csv`
- Aggregated master CSV:
  `master_analysis.csv`

## Notes and Known Behavior

- Returning-user flow currently auto-selects the first detected user in `calibrations/`.
- `run_eyetracker.bat` uses a machine-specific interpreter path:
  `C:\Users\hayth\anaconda3\envs\eyetracker\python.exe`.
  Update it if your local environment path is different.
- `analyzer.py` recomputes `master_analysis.csv` from all available `session_data` JSON files.

## Quick Checks

```bash
python test_user_selection.py
python test_enhancements.py
python test_clustering.py
```

## License

Private / Research Use
