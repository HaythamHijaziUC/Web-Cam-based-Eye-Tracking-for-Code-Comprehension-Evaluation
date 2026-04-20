"""Configurable cognitive load calculator with scientific validation"""

import json
import numpy as np
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

WEIGHTS_FILE = Path(__file__).parent / "weights.json"


@dataclass
class CognitiveLoadResult:
    """Result of cognitive load calculation"""
    score: float  # 0-100 scale
    components: Dict[str, float]  # Individual component scores
    confidence: float  # 0-1, based on data quality
    warnings: List[str]


class CognitiveLoadCalculator:
    """
    Calculate cognitive load from eye-tracking metrics.
    
    Combines:
    - Fixation density (fixations per line)
    - Regression rate (backward eye movements)
    - Mean fixation duration
    - Static code complexity
    """
    
    def __init__(self, weights_preset: str = "default"):
        """
        Initialize calculator with weight preset.
        
        Args:
            weights_preset: 'default', 'conservative', or 'aggressive'
        """
        self.weights = self._load_weights(weights_preset)
        self.weights_preset = weights_preset
        logger.info(f"Initialized CognitiveLoadCalculator with '{weights_preset}' weights")
    
    def _load_weights(self, preset: str = "default") -> Dict[str, float]:
        """Load weights from JSON file"""
        try:
            with open(WEIGHTS_FILE, 'r') as f:
                data = json.load(f)
            
            if preset == "default":
                weights = data["weights"]
            elif preset in data["alternatives"]:
                weights = data["alternatives"][preset]
            else:
                logger.warning(f"Unknown preset '{preset}', using default")
                weights = data["weights"]
            
            logger.info(f"Loaded weights: {weights}")
            return weights
            
        except FileNotFoundError:
            logger.warning(f"Weights file not found, using hardcoded defaults")
            return {
                'fixation_density': 1.0,
                'regression_rate': 1.5,
                'mean_fixation_duration': 0.8,
                'cognitive_complexity': 0.5
            }
    
    def calculate(self, 
                 metrics: Dict[str, float],
                 num_data_points: int = 100,
                 region_lines: int = 10) -> CognitiveLoadResult:
        """
        Calculate cognitive load from eye-tracking metrics.
        
        Args:
            metrics: Dictionary with keys:
                - 'fixation_count': int
                - 'regression_count': int
                - 'reading_time_sec': float
                - 'static_complexity': int (0-20 scale)
            num_data_points: Number of gaze samples collected
            region_lines: Number of lines in code region
        
        Returns:
            CognitiveLoadResult with score and component breakdown
        """
        warnings = []
        components = {}
        
        # Extract metrics
        fixation_count = metrics.get('fixation_count', 0)
        regression_count = metrics.get('regression_count', 0)
        reading_time = metrics.get('reading_time_sec', 0.001)
        static_complexity = metrics.get('static_complexity', 1)
        
        # Quality checks
        if num_data_points < 50:
            warnings.append(f"Low data quality: only {num_data_points} samples")
        if region_lines < 1:
            region_lines = 1
            warnings.append("Invalid region lines, set to 1")
        
        # ========== COMPONENT 1: Fixation Density ==========
        fixation_density = fixation_count / region_lines
        components['fixation_density'] = fixation_density * self.weights['fixation_density']
        
        # ========== COMPONENT 2: Regression Rate ==========
        regression_rate = regression_count / max(1, fixation_count)
        components['regression_rate'] = regression_rate * self.weights['regression_rate']
        
        # ========== COMPONENT 3: Mean Fixation Duration ==========
        mean_fixation_duration = reading_time / max(1, fixation_count)  # seconds
        # Normalize: typical fixation is 200-300ms, longer indicates struggle
        normalized_duration = min(mean_fixation_duration / 0.3, 2.0)  # Cap at 2.0
        components['mean_fixation_duration'] = normalized_duration * self.weights['mean_fixation_duration']
        
        # ========== COMPONENT 4: Static Cognitive Complexity ==========
        # Normalize complexity (SonarSource: typically 0-20)
        normalized_complexity = min(static_complexity / 10, 2.0)
        components['cognitive_complexity'] = normalized_complexity * self.weights['cognitive_complexity']
        
        # ========== Z-SCORE NORMALIZATION ==========
        # Normalize components to 0-100 scale
        component_scores = list(components.values())
        if sum(component_scores) > 0:
            max_score = max(component_scores)
            normalized = {k: (v / max_score * 100) if max_score > 0 else 0 
                         for k, v in components.items()}
        else:
            normalized = {k: 0 for k in components.keys()}
        
        # Final composite score (average of normalized components)
        final_score = np.mean(list(normalized.values())) if normalized else 0
        
        # ========== CONFIDENCE CALCULATION ==========
        # Based on data quality
        confidence = min(num_data_points / 100, 1.0)  # Max 1.0 at 100+ samples
        if regression_count > fixation_count / 2:
            confidence *= 0.9  # Reduce confidence if too many regressions
        
        result = CognitiveLoadResult(
            score=float(np.clip(final_score, 0, 100)),
            components=normalized,
            confidence=float(confidence),
            warnings=warnings
        )
        
        return result
    
    def calculate_batch(self, 
                       metrics_list: List[Dict[str, float]]) -> List[CognitiveLoadResult]:
        """Calculate cognitive load for multiple regions"""
        return [self.calculate(m) for m in metrics_list]
    
    def get_interpretation(self, score: float) -> str:
        """Get text interpretation of cognitive load score"""
        if score < 20:
            return "Very Low - Trivial code"
        elif score < 40:
            return "Low - Straightforward code"
        elif score < 60:
            return "Medium - Moderate complexity"
        elif score < 80:
            return "High - Complex code"
        else:
            return "Very High - Highly complex, needs refactoring"
    
    def export_configuration(self) -> Dict:
        """Export current configuration for reproducibility"""
        return {
            'weights_preset': self.weights_preset,
            'weights': self.weights,
            'version': '1.0'
        }
