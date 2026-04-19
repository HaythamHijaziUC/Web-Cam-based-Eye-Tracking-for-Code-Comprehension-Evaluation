# Web-Cam based Eye-Tracking for Code Comprehension Evaluation

A comprehensive eye-tracking system for analyzing code comprehension using webcam technology. Combines gaze tracking with static code analysis to quantify cognitive load and identify comprehension challenges.

## 🚀 Features

### Core Eye-Tracking
- **Webcam Gaze Tracking**: Hardware-free eye tracking using MediaPipe and OpenCV
- **Real-time Calibration**: Vertical calibration with drift correction (Hot-key 'C')
- **Fixation Detection**: I-DT algorithm filters noise and saccades
- **Regression Tracking**: Automatic detection of backward eye movements
- **Multi-session Support**: Unique session numbering prevents data overwriting

### Code Analysis
- **AST-Based Semantic Parsing**: Python code parsed into functions, loops, and logical blocks
- **Cognitive Complexity**: SonarSource-compliant static complexity analysis
- **Semantic Region Mapping**: Gaze points mapped to code regions for detailed analysis

### Cognitive Load Metrics
- **Eye-Tracking Cognitive Load**: Composite metric combining:
  - Fixation Density (fixations per line)
  - Reading Regressions (backward movements)
  - Static Code Complexity
- **Formula**: `Cognitive Load = Z(Fixation Density) + 1.5 × Z(Regressions)`
- **Scale**: 0-100 (higher = more mentally demanding)

### Advanced Analytics
- **Comprehensive Reporting**: Session, user, and file-level statistics
- **Heatmap Generation**: Visual gaze point distributions
- **CSV Export**: Statistical analysis ready data
- **Multi-language Fallback**: Keyword-based parsing for non-Python files

## 📊 Metrics & Calculations

### Eye-Tracking Cognitive Load
```
Cognitive Load Score = Z(Fixation Density) + (Z(Regression Count) × 1.5)
```
- **Fixation Density**: Visual attention per line of code
- **Regressions**: Backward eye movements indicating comprehension issues
- **Z-Score Normalization**: Cross-region comparability
- **Weighted Combination**: Empirically configurable regression weight

### Static Cognitive Complexity (SonarSource Rules)
- **+1** for each: if/while/for statements, comprehensions
- **+1 + nesting level** for nested control structures
- **+1** for each boolean operator (and/or)
- **+1** for exception handlers

### Session Analytics
- **Reading Time**: Total time spent on code regions
- **Fixation Count**: Number of meaningful gaze fixations
- **Regression Frequency**: Back-tracking between regions
- **Gaze Point Collection**: Raw eye-tracking data

## 🛠️ Scripts

- `eye.py`: Main eye-tracking application with calibration and data collection
- `analyzer.py`: Comprehensive analysis engine with cognitive load calculations
- `gaze_logger.py`: Fixation detection and region transition logging
- `heatmap.py`: Gaze point visualization and heatmap generation
- `code_viewer.py`: Code rendering with line numbering
- `calibration.py`: Camera calibration utilities
- `cognitive_complexity.py`: SonarSource cognitive complexity implementation
- `semantic_parser.py`: AST-based code region parsing

## 📦 Installation

1. **Clone Repository**:
   ```bash
   git clone https://github.com/HaythamHijaziUC/Web-Cam-based-Eye-Tracking-for-Code-Comprehension-Evaluation.git
   cd Web-Cam-based-Eye-Tracking-for-Code-Comprehension-Evaluation
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## 🎯 Usage

### Data Collection
1. **Run Eye Tracking**:
   ```bash
   python eye.py
   ```

2. **Calibration**:
   - Look at TOP/BOTTOM calibration points
   - Press SPACE to capture each position

3. **Code Reading**:
   - Select code file via file dialog
   - Press SPACE to start tracking
   - Read code naturally
   - Press 'N' for next file, 'Q' to quit

4. **Drift Correction**: Press 'C' during tracking to recalibrate center point

### Data Analysis
```bash
python analyzer.py
```

**Output**:
- **JSON Reports**: `session_data/reading_report_session_X_user_Y.json`
- **Heatmaps**: `session_data/heatmap_session_X_user_Y_filename.png`
- **CSV Analysis**: `master_analysis.csv` with cognitive load scores
- **Console Report**: Comprehensive session/user/file statistics

## 📈 Sample Output

```
================================================================================
COMPREHENSIVE ANALYSIS REPORT
================================================================================

📊 SESSION-LEVEL SUMMARY:
  Session 1: Total Reading Time: 10.60s, Fixations: 9, Regressions: 3

👤 USER-LEVEL SUMMARY:
  User 19: Sessions: 2, Files: 1, Total Time: 19.77s

🔥 COGNITIVE LOAD ANALYSIS:
  ⚠️ TOP 5 MOST DEMANDING REGIONS:
    1. Module [14-17]: Load 100.0 (High complexity + regressions)
    2. Module [1-12]: Load 82.9 (Nested control structures)

⏮️ REGRESSION ANALYSIS:
  Total Regressions: 6, Regions with issues: 4/6
```

## 🔬 Scientific Foundation

### Cognitive Load Theory
- **Intrinsic Load**: Code structure complexity (static analysis)
- **Extraneous Load**: Poor code organization
- **Germane Load**: Learning and comprehension effort

### Eye-Tracking Validation
- **Fixations**: 100-500ms indicate information processing
- **Saccades**: Rapid eye movements between fixations
- **Regressions**: Backward movements signal comprehension failure

### Metric Reliability
- **Z-Score Normalization**: Accounts for individual differences
- **Composite Scoring**: Balances multiple cognitive indicators
- **Configurable Weights**: Regression weight (1.5) empirically testable

## 📝 License

Private / Research Use

## 🤝 Contributing

For scientific improvements:
- Empirical validation of regression weights
- Additional eye-tracking metrics
- Cross-language semantic parsing
- Statistical analysis enhancements
