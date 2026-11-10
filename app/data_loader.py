import os
import json
import pandas as pd

def get_project_root():
    """
    Returns the absolute path to the EduPredict root directory.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # If this file is in app/ or models/, root is parent
    parent_dir = os.path.dirname(current_dir)
    if os.path.exists(os.path.join(parent_dir, 'data')):
        return parent_dir
    if os.path.exists(os.path.join(current_dir, 'data')):
        return current_dir
    return os.getcwd()

def get_data_paths():
    """
    Resolves data file paths.
    """
    root = get_project_root()
    data_dir = os.path.join(root, 'data')
    
    csv_academic = os.path.join(data_dir, 'student_academic_records.csv')
    csv_primary = os.path.join(data_dir, 'EduPredict_Student_Dataset.csv')
    
    # Check which CSV exists, prefer student_academic_records if both exist
    csv_path = csv_academic if os.path.exists(csv_academic) else csv_primary
    json_path = os.path.join(data_dir, 'lms_attendance_logs.json')
    
    models_dir = os.path.join(root, 'models')
    model_pkl = os.path.join(models_dir, 'dropout_predict_model.pkl')
    metrics_json = os.path.join(models_dir, 'model_metrics.json')
    
    return {
        'root': root,
        'data_dir': data_dir,
        'csv_path': csv_path,
        'csv_academic': csv_academic,
        'csv_primary': csv_primary,
        'json_path': json_path,
        'models_dir': models_dir,
        'model_pkl': model_pkl,
        'metrics_json': metrics_json
    }

def load_and_merge_data():
    """
    Loads academic records and LMS logs, performs clean merge on student_id,
    and eliminates duplicate suffix columns.
    """
    paths = get_data_paths()
    
    if not os.path.exists(paths['csv_path']):
        raise FileNotFoundError(f"Academic records CSV not found at {paths['csv_path']}")
    
    df_academic = pd.read_csv(paths['csv_path'])
    
    if os.path.exists(paths['json_path']):
        with open(paths['json_path'], 'r', encoding='utf-8') as f:
            lms_data = json.load(f)
        df_lms = pd.DataFrame(lms_data)
    else:
        df_lms = pd.DataFrame()
        
    if df_lms.empty:
        return df_academic

    # Identify overlapping columns to avoid _x / _y collisions
    overlap_cols = [c for c in df_lms.columns if c in df_academic.columns and c != 'student_id']
    
    # Merge with suffixes
    df_merged = pd.merge(df_academic, df_lms, on='student_id', how='left', suffixes=('', '_lms'))
    
    # If overlapping columns exist, prioritize LMS log data for behavioral stats, then drop _lms column
    for col in overlap_cols:
        lms_col = f"{col}_lms"
        if lms_col in df_merged.columns:
            df_merged[col] = df_merged[lms_col].combine_first(df_merged[col])
            df_merged = df_merged.drop(columns=[lms_col])
            
    # Clean data types
    if 'dropout_risk_flag' in df_merged.columns:
        df_merged['dropout_risk_flag'] = df_merged['dropout_risk_flag'].fillna(0).astype(int)
    if 'gpa' in df_merged.columns:
        df_merged['gpa'] = df_merged['gpa'].astype(float).round(2)
    if 'attendance_pct' in df_merged.columns:
        df_merged['attendance_pct'] = df_merged['attendance_pct'].astype(float).round(1)
    if 'lms_clicks' in df_merged.columns:
        df_merged['lms_clicks'] = df_merged['lms_clicks'].fillna(0).astype(int)
    if 'assignments_submitted' in df_merged.columns:
        df_merged['assignments_submitted'] = df_merged['assignments_submitted'].fillna(0).astype(int)
    if 'assignments_total' in df_merged.columns:
        df_merged['assignments_total'] = df_merged['assignments_total'].fillna(8).astype(int)

    return df_merged

def save_student_data(student_dict, is_new=True):
    """
    Saves or updates a student in both CSV files and LMS JSON file.
    """
    paths = get_data_paths()
    df_current = load_and_merge_data()
    
    stu_id = str(student_dict.get('student_id', '')).strip().upper()
    if not stu_id:
        raise ValueError("Student ID is required.")

    # Calculate risk flag if not provided
    gpa = float(student_dict.get('gpa', 0.0))
    att = float(student_dict.get('attendance_pct', 0.0))
    submitted = int(student_dict.get('assignments_submitted', 0))
    risk = int(student_dict.get('dropout_risk_flag', 1 if (gpa < 2.2 or att < 60.0 or submitted < 4) else 0))

    record = {
        'student_id': stu_id,
        'name': str(student_dict.get('name', 'Anonymous Student')).strip(),
        'gender': str(student_dict.get('gender', 'M')).strip().upper(),
        'department': str(student_dict.get('department', 'Computer Science')).strip(),
        'gpa': round(gpa, 2),
        'previous_qualification': str(student_dict.get('previous_qualification', 'A-Levels')).strip(),
        'fee_status': str(student_dict.get('fee_status', 'Paid')).strip(),
        'attendance_pct': round(att, 1),
        'lms_clicks': int(student_dict.get('lms_clicks', 0)),
        'assignments_submitted': submitted,
        'assignments_total': int(student_dict.get('assignments_total', 8)),
        'dropout_risk_flag': risk,
        'course_code': str(student_dict.get('course_code', 'CS-401')).strip()
    }

    exists = stu_id in df_current['student_id'].values

    if is_new and exists:
        raise ValueError(f"Student ID '{stu_id}' already exists.")

    if exists:
        # Update existing record
        idx = df_current[df_current['student_id'] == stu_id].index[0]
        for k, v in record.items():
            df_current.at[idx, k] = v
    else:
        # Append new record
        new_row = pd.DataFrame([record])
        df_current = pd.concat([df_current, new_row], ignore_index=True)

    # Persist CSVs
    csv_cols = ["student_id", "name", "gender", "department", "gpa", "previous_qualification", 
                "fee_status", "attendance_pct", "lms_clicks", "assignments_submitted", 
                "assignments_total", "dropout_risk_flag"]
    df_csv = df_current[csv_cols]
    df_csv.to_csv(paths['csv_academic'], index=False)
    df_csv.to_csv(paths['csv_primary'], index=False)

    # Persist JSON
    json_cols = ["student_id", "course_code", "attendance_pct", "lms_clicks", 
                 "assignments_submitted", "assignments_total"]
    lms_records = df_current[json_cols].to_dict(orient="records")
    with open(paths['json_path'], 'w', encoding='utf-8') as f:
        json.dump(lms_records, f, indent=2)

    return record

def delete_student(student_id):
    """
    Deletes a student record by student_id from CSVs and JSON.
    """
    paths = get_data_paths()
    df_current = load_and_merge_data()
    stu_id = str(student_id).strip().upper()
    
    if stu_id not in df_current['student_id'].values:
        return False

    df_filtered = df_current[df_current['student_id'] != stu_id]

    csv_cols = ["student_id", "name", "gender", "department", "gpa", "previous_qualification", 
                "fee_status", "attendance_pct", "lms_clicks", "assignments_submitted", 
                "assignments_total", "dropout_risk_flag"]
    df_csv = df_filtered[csv_cols]
    df_csv.to_csv(paths['csv_academic'], index=False)
    df_csv.to_csv(paths['csv_primary'], index=False)

    json_cols = ["student_id", "course_code", "attendance_pct", "lms_clicks", 
                 "assignments_submitted", "assignments_total"]
    lms_records = df_filtered[json_cols].to_dict(orient="records")
    with open(paths['json_path'], 'w', encoding='utf-8') as f:
        json.dump(lms_records, f, indent=2)

    return True

def get_analytics():
    """
    Computes summary analytics for the web portal.
    """
    df = load_and_merge_data()
    total = len(df)
    if total == 0:
        return {
            'total': 0, 'at_risk': 0, 'at_risk_pct': 0, 'safe': 0, 
            'avg_attendance': 0, 'avg_gpa': 0, 'dept_stats': {}, 
            'risk_distribution': {}
        }

    at_risk = int(df['dropout_risk_flag'].sum())
    safe = total - at_risk
    at_risk_pct = round((at_risk / total) * 100, 1)
    avg_attendance = round(float(df['attendance_pct'].mean()), 1)
    avg_gpa = round(float(df['gpa'].mean()), 2)

    # Department breakdown
    dept_stats = {}
    for dept, group in df.groupby('department'):
        dept_stats[dept] = {
            'total': len(group),
            'at_risk': int(group['dropout_risk_flag'].sum()),
            'avg_gpa': round(float(group['gpa'].mean()), 2),
            'avg_att': round(float(group['attendance_pct'].mean()), 1)
        }

    # Fee status risk correlation
    fee_stats = {}
    for fee, group in df.groupby('fee_status'):
        fee_stats[fee] = {
            'total': len(group),
            'at_risk': int(group['dropout_risk_flag'].sum())
        }

    return {
        'total': total,
        'at_risk': at_risk,
        'safe': safe,
        'at_risk_pct': at_risk_pct,
        'avg_attendance': avg_attendance,
        'avg_gpa': avg_gpa,
        'dept_stats': dept_stats,
        'fee_stats': fee_stats
    }
