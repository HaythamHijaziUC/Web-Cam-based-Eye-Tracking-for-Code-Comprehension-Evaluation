"""9-point calibration system with validation"""

import cv2
import numpy as np
import mediapipe as mp
from typing import Optional, Dict, List, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class CalibrationTarget:
    """Single calibration target"""
    def __init__(self, x_pct: float, y_pct: float, screen_w: int, screen_h: int):
        self.x_pct = x_pct  # 0.0 to 1.0
        self.y_pct = y_pct  # 0.0 to 1.0
        self.screen_x = int(x_pct * screen_w)
        self.screen_y = int(y_pct * screen_h)
    
    def get_coords(self) -> Tuple[int, int]:
        return (self.screen_x, self.screen_y)


class Calibrator:
    """9-point calibration system for eye tracking"""
    
    def __init__(self, screen_w: int, screen_h: int):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.mp_face_mesh = mp.solutions.face_mesh.FaceMesh(refine_landmarks=True)
        self.cap = cv2.VideoCapture(0)
        
        # 9 calibration targets (10%, 50%, 90%) x (10%, 50%, 90%)
        self.targets = self._create_targets()
        self.calibration_data = []
        
    def _create_targets(self) -> List[CalibrationTarget]:
        """Create 9-point calibration grid"""
        percentages = [0.1, 0.5, 0.9]
        targets = []
        for x_pct in percentages:
            for y_pct in percentages:
                targets.append(CalibrationTarget(x_pct, y_pct, self.screen_w, self.screen_h))
        return targets
    
    def run_calibration(self) -> Optional[Dict]:
        """
        Run full 9-point calibration.
        
        Returns:
            Dictionary with calibration_matrix, accuracy_score, and metadata
        """
        print("Starting 9-point calibration...")
        print("Follow the green dot on the screen")
        
        win = "Calibration"
        cv2.namedWindow(win, cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty(win, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        
        collected_samples = []
        
        for target_idx, target in enumerate(self.targets):
            print(f"Target {target_idx + 1}/9: Move to point ({target.x_pct*100:.0f}%, {target.y_pct*100:.0f}%)")
            
            target_x, target_y = target.get_coords()
            samples_for_target = []
            frame_count = 0
            
            # Display target for 2 seconds, collect samples from last 1 second
            while frame_count < 60:  # 2 seconds at 30fps
                ret, frame = self.cap.read()
                if not ret:
                    break
                
                h, w = frame.shape[:2]
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.mp_face_mesh.process(rgb)
                
                # Draw background
                canvas = np.zeros((self.screen_h, self.screen_w, 3), dtype=np.uint8)
                
                # Draw calibration target (green dot)
                cv2.circle(canvas, (target_x, target_y), 20, (0, 255, 0), -1)
                cv2.circle(canvas, (target_x, target_y), 25, (0, 255, 0), 2)
                
                # Draw progress
                progress_pct = (frame_count * 100) // 60
                cv2.putText(canvas, f"Calibration: {progress_pct}%", (50, 50),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                cv2.putText(canvas, f"Target {target_idx + 1}/9", (50, 100),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                
                cv2.imshow(win, canvas)
                cv2.waitKey(1)
                
                # Collect gaze samples from last 30 frames (1 second)
                if frame_count >= 30 and results.multi_face_landmarks:
                    mesh = results.multi_face_landmarks[0]
                    landmarks = np.array([(lm.x * w, lm.y * h) for lm in mesh.landmark])
                    
                    # Extract iris position (approximate)
                    iris_y = np.mean(landmarks[[470, 471, 472, 473, 474], 1])
                    iris_x = np.mean(landmarks[[470, 471, 472, 473, 474], 0])
                    
                    samples_for_target.append({
                        'iris_pos': (iris_x, iris_y),
                        'target_pos': (target_x, target_y),
                        'target_pct': (target.x_pct, target.y_pct)
                    })
                
                frame_count += 1
            
            if samples_for_target:
                collected_samples.append({
                    'target': target,
                    'samples': samples_for_target,
                    'mean_iris': np.mean([s['iris_pos'] for s in samples_for_target], axis=0)
                })
        
        cv2.destroyAllWindows()
        
        if not collected_samples:
            logger.error("Calibration failed: No gaze data collected")
            return None
        
        # Compute calibration matrix (simple linear regression)
        X = np.array([c['mean_iris'] for c in collected_samples])  # iris positions
        y = np.array([c['target']['get_coords']() for c in collected_samples])  # target positions
        
        # Simple linear calibration: gaze_screen = A @ iris_raw + b
        # Add bias term
        X_augmented = np.column_stack([X, np.ones(len(X))])
        try:
            calibration_matrix, _, _, _ = np.linalg.lstsq(X_augmented, y, rcond=None)
        except Exception as e:
            logger.error(f"Calibration matrix computation failed: {e}")
            return None
        
        # Compute validation error on calibration set
        predicted = X_augmented @ calibration_matrix
        errors = np.sqrt(np.sum((predicted - y) ** 2, axis=1))
        mean_error = np.mean(errors)
        
        calibration_data = {
            'user_id': None,  # Will be set by caller
            'calibration_matrix': calibration_matrix.tolist(),
            'mean_error_px': float(mean_error),
            'max_error_px': float(np.max(errors)),
            'accuracy_score': max(0, 100 - mean_error),  # Higher is better
            'timestamp': datetime.now().isoformat(),
            'screen_resolution': (self.screen_w, self.screen_h),
            'num_targets': len(collected_samples),
            'samples_per_target': len(collected_samples[0]['samples']) if collected_samples else 0
        }
        
        logger.info(f"Calibration complete: mean_error={mean_error:.1f}px, accuracy={calibration_data['accuracy_score']:.1f}%")
        
        self.cap.release()
        return calibration_data
    
    def validate_calibration(self, calib_data: Dict) -> Tuple[bool, str]:
        """
        Validate calibration with 4 extra points.
        
        Returns:
            (is_valid, message)
        """
        print("Running calibration validation...")
        
        # Use 4 corners for validation
        validation_targets = [
            CalibrationTarget(0.25, 0.25, self.screen_w, self.screen_h),
            CalibrationTarget(0.75, 0.25, self.screen_w, self.screen_h),
            CalibrationTarget(0.25, 0.75, self.screen_w, self.screen_h),
            CalibrationTarget(0.75, 0.75, self.screen_w, self.screen_h),
        ]
        
        validation_errors = []
        
        try:
            calib_matrix = np.array(calib_data['calibration_matrix'])
        except Exception as e:
            return False, f"Invalid calibration matrix: {e}"
        
        for target in validation_targets:
            # Collect samples
            target_x, target_y = target.get_coords()
            samples = []
            frame_count = 0
            
            win = "Validation"
            cv2.namedWindow(win, cv2.WND_PROP_FULLSCREEN)
            cv2.setWindowProperty(win, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            
            while frame_count < 30:  # 1 second
                ret, frame = self.cap.read()
                if not ret:
                    break
                
                canvas = np.zeros((self.screen_h, self.screen_w, 3), dtype=np.uint8)
                cv2.circle(canvas, (target_x, target_y), 15, (0, 255, 0), -1)
                cv2.imshow(win, canvas)
                cv2.waitKey(1)
                
                h, w = frame.shape[:2]
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.mp_face_mesh.process(rgb)
                
                if results.multi_face_landmarks:
                    mesh = results.multi_face_landmarks[0]
                    landmarks = np.array([(lm.x * w, lm.y * h) for lm in mesh.landmark])
                    iris_pos = np.mean(landmarks[[470, 471, 472, 473, 474]], axis=0)
                    samples.append(iris_pos)
                
                frame_count += 1
            
            cv2.destroyAllWindows()
            
            if samples:
                mean_iris = np.mean(samples, axis=0)
                iris_augmented = np.append(mean_iris, 1)
                predicted = iris_augmented @ calib_matrix
                error = np.sqrt(np.sum((predicted - (target_x, target_y)) ** 2))
                validation_errors.append(error)
        
        mean_validation_error = np.mean(validation_errors) if validation_errors else 0
        
        is_valid = mean_validation_error < 150  # 150px threshold
        message = f"Validation error: {mean_validation_error:.1f}px - {'PASS' if is_valid else 'FAIL'}"
        
        logger.info(message)
        return is_valid, message
