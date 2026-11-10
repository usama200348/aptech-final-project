import os
import sys
import json
import joblib
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report, confusion_matrix

# Ensure app package is accessible for data_loader
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
app_dir = os.path.join(project_root, 'app')
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

try:
    from app.data_loader import load_and_merge_data, get_data_paths
except ImportError:
    # Fallback direct loader if run independently
    def get_data_paths():
        models_dir = current_dir
        data_dir = os.path.join(project_root, 'data')
        csv_path = os.path.join(data_dir, 'student_academic_records.csv')
        if not os.path.exists(csv_path):
            csv_path = os.path.join(data_dir, 'EduPredict_Student_Dataset.csv')
        json_path = os.path.join(data_dir, 'lms_attendance_logs.json')
        return {
            'csv_path': csv_path,
            'json_path': json_path,
            'models_dir': models_dir,
            'model_pkl': os.path.join(models_dir, 'dropout_predict_model.pkl'),
            'metrics_json': os.path.join(models_dir, 'model_metrics.json')
        }

    def load_and_merge_data():
        paths = get_data_paths()
        df_academic = pd.read_csv(paths['csv_path'])
        with open(paths['json_path'], 'r', encoding='utf-8') as f:
            df_lms = pd.DataFrame(json.load(f))
        overlap_cols = [c for c in df_lms.columns if c in df_academic.columns and c != 'student_id']
        df_merged = pd.merge(df_academic, df_lms, on='student_id', how='left', suffixes=('', '_lms'))
        for col in overlap_cols:
            if f"{col}_lms" in df_merged.columns:
                df_merged[col] = df_merged[f"{col}_lms"].combine_first(df_merged[col])
                df_merged = df_merged.drop(columns=[f"{col}_lms"])
        return df_merged

def train_dropout_model():
    """
    Trains the Predictive Dropout Model using Random Forest Classification,
    evaluates its performance, and serializes the model and metrics.
    """
    print("[INFO] Starting EduPredict Model Training Pipeline...")
    paths = get_data_paths()
    df = load_and_merge_data()
    print(f"[INFO] Loaded {len(df)} student records for training.")

    # Features: Academic performance & LMS behavioral indicators
    feature_cols = ['gpa', 'attendance_pct', 'lms_clicks', 'assignments_submitted']
    X = df[feature_cols].copy()
    y = df['dropout_risk_flag'].astype(int)

    # Train / Test split
    test_size = 0.25 if len(df) >= 20 else 0.5
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=y if len(np.unique(y)) > 1 else None
    )

    # Train Random Forest Classifier with balanced class weights
    clf = RandomForestClassifier(
        n_estimators=100, 
        max_depth=5,
        min_samples_split=2,
        class_weight='balanced',
        random_state=42
    )
    clf.fit(X_train, y_train)

    # Model Evaluation
    y_pred = clf.predict(X_test)

    accuracy = round(float(accuracy_score(y_test, y_pred)), 4)
    precision = round(float(precision_score(y_test, y_pred, zero_division=0)), 4)
    recall = round(float(recall_score(y_test, y_pred, zero_division=0)), 4)
    f1 = round(float(f1_score(y_test, y_pred, zero_division=0)), 4)
    cm = confusion_matrix(y_test, y_pred).tolist()

    # Feature Importance analysis
    importances = {col: round(float(imp), 4) for col, imp in zip(feature_cols, clf.feature_importances_)}

    print(f"[INFO] Training Completed Successfully!")
    print(f" - Model Accuracy:  {accuracy * 100:.2f}%")
    print(f" - Precision:       {precision * 100:.2f}%")
    print(f" - Recall:          {recall * 100:.2f}%")
    print(f" - F1 Score:        {f1 * 100:.2f}%")
    print(f" - Feature Importances: {importances}")
    print("\nClassification Report:\n", classification_report(y_test, y_pred, zero_division=0))

    # Persist the trained model
    os.makedirs(paths['models_dir'], exist_ok=True)
    joblib.dump(clf, paths['model_pkl'])
    print(f"[INFO] Model binary serialized to: {paths['model_pkl']}")

    # Also save a copy directly in models dir if needed
    local_pkl = os.path.join(current_dir, 'dropout_predict_model.pkl')
    if local_pkl != paths['model_pkl']:
        joblib.dump(clf, local_pkl)

    # Persist model metrics and metadata
    metrics_data = {
        'model_name': 'Random Forest Classifier',
        'training_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'total_samples': len(df),
        'train_samples': len(X_train),
        'test_samples': len(X_test),
        'features': feature_cols,
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1_score': f1,
        'confusion_matrix': cm,
        'feature_importances': importances
    }

    with open(paths['metrics_json'], 'w', encoding='utf-8') as f:
        json.dump(metrics_data, f, indent=2)
    print(f"[INFO] Metrics saved to: {paths['metrics_json']}")

    return clf, metrics_data

if __name__ == '__main__':
    train_dropout_model()
