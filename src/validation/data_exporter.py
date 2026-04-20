"""Data export functionality for validation and analysis"""

import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DataExporter:
    """Export eye-tracking data for validation and analysis"""
    
    def __init__(self, output_dir: str = "exports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def export_validation_data(self, 
                              data_list: List[Dict[str, Any]],
                              output_filename: Optional[str] = None) -> Path:
        """
        Export comprehensive validation dataset.
        
        CSV columns:
        - user_id
        - session_id
        - code_region
        - fixation_density (fixations/line)
        - regression_rate (regressions/fixations)
        - mean_fixation_duration (seconds)
        - cognitive_complexity (0-20 scale)
        - eye_tracking_cognitive_load (0-100)
        - nasa_tlx_mental_demand (0-100)
        - nasa_tlx_effort (0-100)
        - nasa_tlx_overall (0-100)
        - comprehension_score (optional)
        - response_time_ms (optional)
        
        Args:
            data_list: List of dictionaries with session data
            output_filename: Optional custom filename (default: timestamp-based)
        
        Returns:
            Path to created CSV file
        """
        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"validation_export_{timestamp}.csv"
        
        output_path = self.output_dir / output_filename
        
        # Define headers
        headers = [
            'timestamp',
            'user_id',
            'session_id',
            'code_region',
            'region_lines',
            'fixation_count',
            'fixation_density',
            'regression_count',
            'regression_rate',
            'reading_time_sec',
            'mean_fixation_duration_ms',
            'static_cognitive_complexity',
            'eye_tracking_cognitive_load_score',
            'cognitive_load_confidence',
            'nasa_tlx_mental_demand',
            'nasa_tlx_physical_demand',
            'nasa_tlx_temporal_demand',
            'nasa_tlx_performance',
            'nasa_tlx_effort',
            'nasa_tlx_frustration',
            'nasa_tlx_overall_workload',
            'comprehension_correct',
            'response_time_ms',
            'calibration_accuracy',
            'notes'
        ]
        
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=headers, extrasaction='ignore')
                writer.writeheader()
                
                for row in data_list:
                    # Ensure all fields are present
                    complete_row = {h: row.get(h, '') for h in headers}
                    writer.writerow(complete_row)
            
            logger.info(f"Validation data exported to {output_path} ({len(data_list)} rows)")
            return output_path
            
        except Exception as e:
            logger.error(f"Error exporting validation data: {e}")
            raise
    
    def export_session_summary(self,
                              session_data: Dict[str, Any],
                              output_filename: Optional[str] = None) -> Path:
        """
        Export session summary as JSON.
        
        Args:
            session_data: Dictionary with session information
            output_filename: Optional custom filename
        
        Returns:
            Path to created JSON file
        """
        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            user_id = session_data.get('user_id', 'unknown')
            output_filename = f"session_{user_id}_{timestamp}.json"
        
        output_path = self.output_dir / output_filename
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, default=str)
            
            logger.info(f"Session summary exported to {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error exporting session summary: {e}")
            raise
    
    def export_calibration_report(self,
                                 calibration_data: Dict[str, Any],
                                 validation_results: Dict[str, Any],
                                 output_filename: Optional[str] = None) -> Path:
        """
        Export calibration and validation report.
        
        Args:
            calibration_data: Calibration information
            validation_results: Validation test results
            output_filename: Optional custom filename
        
        Returns:
            Path to created JSON file
        """
        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            user_id = calibration_data.get('user_id', 'unknown')
            output_filename = f"calibration_{user_id}_{timestamp}.json"
        
        output_path = self.output_dir / output_filename
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'calibration': calibration_data,
            'validation': validation_results,
            'status': 'PASSED' if validation_results.get('is_valid', False) else 'FAILED'
        }
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Calibration report exported to {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error exporting calibration report: {e}")
            raise
    
    def batch_export(self,
                    sessions: List[Dict[str, Any]],
                    output_prefix: str = "batch_export") -> Dict[str, Path]:
        """
        Export multiple sessions in batch.
        
        Args:
            sessions: List of session dictionaries
            output_prefix: Prefix for output files
        
        Returns:
            Dictionary mapping export types to file paths
        """
        results = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Compile validation data
        validation_data = []
        for session in sessions:
            for trial in session.get('trials', []):
                for region in trial.get('region_metrics', []):
                    row = {
                        'timestamp': session.get('timestamp'),
                        'user_id': session.get('user_id'),
                        'session_id': session.get('session_id'),
                        'code_region': region.get('code_region'),
                        **region
                    }
                    validation_data.append(row)
        
        if validation_data:
            csv_path = self.export_validation_data(
                validation_data,
                f"{output_prefix}_{timestamp}.csv"
            )
            results['validation_csv'] = csv_path
        
        # Export individual session summaries
        for session in sessions:
            json_path = self.export_session_summary(
                session,
                f"{output_prefix}_session_{session.get('user_id')}_{timestamp}.json"
            )
            results[f"session_{session.get('session_id')}"] = json_path
        
        logger.info(f"Batch export complete: {len(results)} files created")
        return results
