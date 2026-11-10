import os
import sys
import joblib
import pandas as pd
import pytest

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from models.train_predictive_models import train_dropout_model, get_data_paths

def test_model_training_and_serialization():
    clf, metrics = train_dropout_model()
    assert clf is not None
    assert metrics['accuracy'] >= 0.85
    assert metrics['f1_score'] >= 0.85
    assert 'gpa' in metrics['feature_importances']
    assert 'attendance_pct' in metrics['feature_importances']

    paths = get_data_paths()
    assert os.path.exists(paths['model_pkl'])
    assert os.path.exists(paths['metrics_json'])

def test_model_inference():
    paths = get_data_paths()
    model = joblib.load(paths['model_pkl'])

    feature_cols = ['gpa', 'attendance_pct', 'lms_clicks', 'assignments_submitted']

    # Case A: Severe Risk Student (GPA 1.2, Attendance 38%, 40 Clicks, 1 Assignment)
    risk_df = pd.DataFrame([[1.2, 38.0, 40, 1]], columns=feature_cols)
    pred_risk = model.predict(risk_df)[0]
    proba_risk = model.predict_proba(risk_df)[0][1]
    assert pred_risk == 1
    assert proba_risk >= 0.70

    # Case B: High Performer Student (GPA 3.8, Attendance 95%, 400 Clicks, 8 Assignments)
    safe_df = pd.DataFrame([[3.8, 95.0, 400, 8]], columns=feature_cols)
    pred_safe = model.predict(safe_df)[0]
    proba_safe = model.predict_proba(safe_df)[0][1]
    assert pred_safe == 0
    assert proba_safe <= 0.30
