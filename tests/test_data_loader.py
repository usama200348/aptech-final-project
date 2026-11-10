import os
import sys
import pytest

# Ensure project root is in sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.data_loader import (
    load_and_merge_data, 
    get_data_paths, 
    get_analytics, 
    save_student_data, 
    delete_student
)

def test_data_paths():
    paths = get_data_paths()
    assert os.path.exists(paths['csv_path'])
    assert os.path.exists(paths['json_path'])

def test_load_and_merge_data_no_collisions():
    df = load_and_merge_data()
    assert len(df) > 0
    
    # Verify no _x or _y collision columns exist
    for col in df.columns:
        assert not col.endswith('_x'), f"Found collision column: {col}"
        assert not col.endswith('_y'), f"Found collision column: {col}"
        assert not col.endswith('_lms'), f"Found collision column: {col}"

    # Verify essential columns are present
    required_cols = [
        'student_id', 'name', 'department', 'gpa', 
        'attendance_pct', 'lms_clicks', 'assignments_submitted', 
        'assignments_total', 'fee_status', 'dropout_risk_flag'
    ]
    for col in required_cols:
        assert col in df.columns, f"Missing required column: {col}"

def test_get_analytics():
    analytics = get_analytics()
    assert analytics['total'] > 0
    assert analytics['at_risk'] >= 0
    assert analytics['safe'] >= 0
    assert analytics['total'] == analytics['at_risk'] + analytics['safe']
    assert 0.0 <= analytics['avg_attendance'] <= 100.0
    assert 0.0 <= analytics['avg_gpa'] <= 4.0
    assert isinstance(analytics['dept_stats'], dict)

def test_crud_lifecycle():
    test_id = "STU9999_TEST"
    
    # 1. Create
    test_student = {
        'student_id': test_id,
        'name': 'Unit Test Student',
        'gender': 'M',
        'department': 'Computer Science',
        'gpa': 3.5,
        'previous_qualification': 'A-Levels',
        'fee_status': 'Paid',
        'attendance_pct': 88.0,
        'lms_clicks': 250,
        'assignments_submitted': 7,
        'assignments_total': 8,
        'course_code': 'CS-401'
    }
    saved = save_student_data(test_student, is_new=True)
    assert saved['student_id'] == test_id

    # Verify presence
    df = load_and_merge_data()
    assert test_id in df['student_id'].values

    # 2. Update
    test_student['gpa'] = 3.9
    updated = save_student_data(test_student, is_new=False)
    assert updated['gpa'] == 3.9

    # 3. Delete
    deleted = delete_student(test_id)
    assert deleted is True

    # Verify removal
    df_after = load_and_merge_data()
    assert test_id not in df_after['student_id'].values
