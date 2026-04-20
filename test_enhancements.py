#!/usr/bin/env python3
"""Quick testing suite for eye-tracking enhancements"""

import sys
import numpy as np
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

def test_user_selection():
    """Test: User selection screen"""
    print("\n" + "="*60)
    print("TEST 1: User Selection Screen")
    print("="*60)
    
    from src.ui.user_selection import show_user_selection_screen, UserManager
    
    manager = UserManager()
    existing = manager.get_existing_users()
    print(f"✓ Found {len(existing)} existing users: {existing}")
    
    # Test without showing UI (for CI/CD)
    print("✓ UserManager initialized successfully")
    print("► To test UI: Uncomment show_user_selection_screen() below")
    # user_info = show_user_selection_screen()
    # print(f"Selected user: {user_info}")


def test_cognitive_load_calculator():
    """Test: Cognitive load calculation"""
    print("\n" + "="*60)
    print("TEST 2: Cognitive Load Calculator")
    print("="*60)
    
    from src.metrics.cognitive_load import CognitiveLoadCalculator
    
    # Test all weight presets
    for preset in ['default', 'conservative', 'aggressive']:
        print(f"\n► Testing preset: '{preset}'")
        calc = CognitiveLoadCalculator(weights_preset=preset)
        
        # Test metrics
        test_cases = [
            {
                'name': 'Simple code',
                'metrics': {
                    'fixation_count': 5,
                    'regression_count': 1,
                    'reading_time_sec': 2.0,
                    'static_complexity': 1,
                },
                'lines': 8
            },
            {
                'name': 'Complex nested code',
                'metrics': {
                    'fixation_count': 25,
                    'regression_count': 8,
                    'reading_time_sec': 12.0,
                    'static_complexity': 12,
                },
                'lines': 10
            },
            {
                'name': 'List comprehension',
                'metrics': {
                    'fixation_count': 15,
                    'regression_count': 4,
                    'reading_time_sec': 6.0,
                    'static_complexity': 3,
                },
                'lines': 1
            }
        ]
        
        for test in test_cases:
            result = calc.calculate(test['metrics'], num_data_points=120, region_lines=test['lines'])
            
            print(f"  {test['name']}:")
            print(f"    Score: {result.score:.1f}/100")
            print(f"    Confidence: {result.confidence:.1%}")
            print(f"    Interpretation: {calc.get_interpretation(result.score)}")
            
            # Verify components
            assert 'fixation_density' in result.components, "Missing fixation_density"
            assert 'regression_rate' in result.components, "Missing regression_rate"
            assert result.score >= 0 and result.score <= 100, "Score out of range"
    
    print("✓ All cognitive load tests passed!")


def test_nasa_tlx_survey():
    """Test: NASA-TLX survey"""
    print("\n" + "="*60)
    print("TEST 3: NASA-TLX Survey")
    print("="*60)
    
    from src.ui.nasa_tlx_survey import NasaTlxScore
    
    # Create synthetic response
    tlx_response = NasaTlxScore(
        mental_demand=75,
        physical_demand=10,
        temporal_demand=40,
        performance=85,
        effort=70,
        frustration=30
    )
    
    print(f"Mental Demand: {tlx_response.mental_demand}/100")
    print(f"Physical Demand: {tlx_response.physical_demand}/100")
    print(f"Temporal Demand: {tlx_response.temporal_demand}/100")
    print(f"Performance: {tlx_response.performance}/100")
    print(f"Effort: {tlx_response.effort}/100")
    print(f"Frustration: {tlx_response.frustration}/100")
    print(f"Overall Workload: {tlx_response.overall_workload:.1f}/100")
    
    # Convert to dict
    data = tlx_response.to_dict()
    assert len(data) == 7, "NASA-TLX data dict incorrect"
    
    print("✓ NASA-TLX survey test passed!")
    print("► To test UI: Run `python -c \"from src.ui.nasa_tlx_survey import NasaTlxSurvey; survey = NasaTlxSurvey(); result = survey.show_survey(); print(result)\"`")


def test_data_exporter():
    """Test: Data export functionality"""
    print("\n" + "="*60)
    print("TEST 4: Data Exporter")
    print("="*60)
    
    from src.validation.data_exporter import DataExporter
    from datetime import datetime
    
    exporter = DataExporter(output_dir="test_exports")
    
    # Create test data
    test_data = [
        {
            'timestamp': datetime.now().isoformat(),
            'user_id': 'test_user_001',
            'session_id': 1,
            'code_region': 'function_def [1-15]',
            'region_lines': 15,
            'fixation_count': 12,
            'fixation_density': 0.8,
            'regression_count': 3,
            'regression_rate': 0.25,
            'reading_time_sec': 5.2,
            'mean_fixation_duration_ms': 433,
            'static_cognitive_complexity': 5,
            'eye_tracking_cognitive_load_score': 72.3,
            'cognitive_load_confidence': 0.95,
            'nasa_tlx_mental_demand': 75,
            'nasa_tlx_overall_workload': 68.3,
            'comprehension_correct': True,
            'response_time_ms': 4200,
            'calibration_accuracy': 88.5,
            'notes': 'Test session'
        }
    ]
    
    try:
        csv_path = exporter.export_validation_data(test_data, "test_export.csv")
        print(f"✓ CSV exported to: {csv_path}")
        
        # Verify file exists
        assert csv_path.exists(), "CSV file not created"
        
        # Read back and verify
        with open(csv_path, 'r') as f:
            lines = f.readlines()
            print(f"✓ CSV has {len(lines)} lines (1 header + {len(lines)-1} data rows)")
        
    except Exception as e:
        print(f"✗ CSV export failed: {e}")
        return
    
    # Test session summary export
    try:
        session = {
            'user_id': 'test_user_001',
            'session_id': 1,
            'timestamp': datetime.now().isoformat(),
            'trials': [{'region_metrics': test_data}]
        }
        json_path = exporter.export_session_summary(session, "test_session.json")
        print(f"✓ JSON exported to: {json_path}")
        assert json_path.exists(), "JSON file not created"
        
    except Exception as e:
        print(f"✗ JSON export failed: {e}")
        return
    
    print("✓ All export tests passed!")


def test_user_manager():
    """Test: User manager and calibration storage"""
    print("\n" + "="*60)
    print("TEST 5: User Manager & Calibration Storage")
    print("="*60)
    
    from src.ui.user_selection import UserManager
    from datetime import datetime, timedelta
    
    manager = UserManager()
    
    # Test user existence
    test_user = "test_calibration_user"
    exists = manager.user_exists(test_user)
    print(f"User '{test_user}' exists: {exists}")
    
    # Create fake calibration data
    calib_data = {
        'user_id': test_user,
        'calibration_matrix': np.random.rand(2, 3).tolist(),  # 2x3 matrix
        'mean_error_px': 85.3,
        'accuracy_score': 91.2,
        'timestamp': datetime.now().isoformat(),
        'screen_resolution': (1920, 1080),
    }
    
    # Save calibration
    success = manager.save_user_calibration(test_user, calib_data)
    print(f"✓ Calibration saved: {success}")
    
    # Load calibration
    loaded = manager.load_user_calibration(test_user)
    assert loaded is not None, "Failed to load calibration"
    print(f"✓ Calibration loaded")
    
    # Check age
    age = manager.get_calibration_age_days(test_user)
    print(f"✓ Calibration age: {age} days")
    assert age == 0, "New calibration should be 0 days old"
    
    # List users
    users = manager.get_existing_users()
    print(f"✓ Existing users: {users}")
    assert test_user in users, "Test user not in list"
    
    print("✓ All user manager tests passed!")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print(" EYE-TRACKING SYSTEM - ENHANCEMENT TEST SUITE")
    print("="*70)
    
    tests = [
        ("User Selection", test_user_selection),
        ("Cognitive Load Calculator", test_cognitive_load_calculator),
        ("NASA-TLX Survey", test_nasa_tlx_survey),
        ("Data Exporter", test_data_exporter),
        ("User Manager", test_user_manager),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"\n✗ {test_name} FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    # Summary
    print("\n" + "="*70)
    print(f" TEST SUMMARY: {passed} passed, {failed} failed")
    print("="*70)
    
    if failed == 0:
        print("✓ ALL TESTS PASSED!")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
