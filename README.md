# Web-Cam based Eye-Tracking for Code Comprehension Evaluation

A lightweight, webcam-based eye-tracking system designed for research and evaluation of code comprehension. This tool uses MediaPipe and OpenCV to track gaze points and map them to semantic regions in a code viewer.

## Features

- **Webcam Gaze Tracking**: No specialized hardware required.
- **AST-Based Semantic Mapping**: Automatically parses Python code into logical blocks (Functions, Loops, Classes) for higher-level comprehension analysis.
- **Fixation Detection (I-DT)**: Implements a Dispersion-Threshold filter to remove gaze jitter and saccades, logging only meaningful fixations.
- **Drift Correction**: Real-time offset adjustment during sessions (Hot-key 'C').
- **Regression Tracking**: Automatically detects back-tracking between semantic regions based on execution flow.
- **Multi-Language Support**: AST parsing for Python with a keyword-based fallback for Java/C++.

## Scripts

- `eye.py`: Main entry point for the gaze tracking loop and calibration.
- `gaze_logger.py`: Handles logging of gaze points and semantic region transitions.
- `heatmap.py`: Utilities for generating gazepoint heatmaps.
- `code_viewer.py`: Renders code files with syntax highlighting for the tracking session.
- `calibration.py`: Calibration logic and model handling.
- `semantic_parser.py`: (Optional) Logic for parsing code into semantic regions.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/HaythamHijaziUC/Web-Cam-based-Eye-Tracking-for-Code-Comprehension-Evaluation.git
   cd Web-Cam-based-Eye-Tracking-for-Code-Comprehension-Evaluation
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the main script:
   ```bash
   python eye.py
   ```
2. Follow the on-screen instructions for vertical calibration (Look at top/bottom and press SPACE).
3. View the code and perform the reading task.
4. Press `q` or `ESC` to end the session and generate the report and heatmap.

## License

Private / Research Use
