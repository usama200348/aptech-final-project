import os
import sys
import json
import joblib
import pandas as pd
import numpy as np
from flask import Flask, render_template, request, jsonify, Response

# Add current and project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from app.data_loader import (
        load_and_merge_data, 
        save_student_data, 
        delete_student, 
        get_analytics, 
        get_data_paths
    )
except ImportError:
    from data_loader import (
        load_and_merge_data, 
        save_student_data, 
        delete_student, 
        get_analytics, 
        get_data_paths
    )

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Global model cache
ml_model = None
ml_metrics = None

def load_ml_model():
    """
    Loads or reloads the trained Random Forest model and metadata.
    """
    global ml_model, ml_metrics
    paths = get_data_paths()
    model_path = paths['model_pkl']
    metrics_path = paths['metrics_json']

    # Also check local models directory
    if not os.path.exists(model_path):
        alt_path = os.path.join(current_dir, '..', 'models', 'dropout_predict_model.pkl')
        if os.path.exists(alt_path):
            model_path = alt_path

    if os.path.exists(model_path):
        try:
            ml_model = joblib.load(model_path)
            app.logger.info(f"Loaded ML model from {model_path}")
        except Exception as e:
            app.logger.error(f"Failed to load ML model: {e}")
            ml_model = None
    else:
        ml_model = None

    if os.path.exists(metrics_path):
        try:
            with open(metrics_path, 'r', encoding='utf-8') as f:
                ml_metrics = json.load(f)
        except Exception as e:
            app.logger.error(f"Failed to load metrics: {e}")
            ml_metrics = None
    else:
        ml_metrics = None

    return ml_model, ml_metrics

# Load model on startup
load_ml_model()

def generate_interventions(gpa, attendance, clicks, assignments, assignments_total=8, fee_status='Paid'):
    """
    Generates intelligent, actionable educational interventions based on individual metrics.
    """
    interventions = []
    
    # GPA Evaluation
    if gpa < 2.0:
        interventions.append({
            'category': 'Academic Probation',
            'severity': 'Critical',
            'icon': 'exclamation-triangle',
            'action': 'Schedule mandatory 1-on-1 academic counseling with Course Coordinator and assign a peer tutor.'
        })
    elif gpa < 2.5:
        interventions.append({
            'category': 'Academic Advisory',
            'severity': 'Warning',
            'icon': 'book',
            'action': 'Recommend remedial workshop sessions and weekly faculty office hours.'
        })

    # Attendance Evaluation
    if attendance < 60.0:
        interventions.append({
            'category': 'Attendance Shortfall',
            'severity': 'Critical',
            'icon': 'clock-history',
            'action': 'Issue official Attendance Warning Letter. Student attendance has breached university minimum eligibility threshold.'
        })
    elif attendance < 75.0:
        interventions.append({
            'category': 'Attendance Advisory',
            'severity': 'Warning',
            'icon': 'calendar-check',
            'action': 'Automated SMS / Email alert to student. Follow up on recurring absence reasons.'
        })

    # LMS Digital Activity
    if clicks < 100:
        interventions.append({
            'category': 'Digital Disengagement',
            'severity': 'Warning',
            'icon': 'laptop',
            'action': 'Extremely low LMS interaction. Provide LMS technical onboarding and assign mandatory online quizzes.'
        })

    # Assignment Submissions
    rate = assignments / max(assignments_total, 1)
    if rate < 0.5:
        interventions.append({
            'category': 'Coursework Deficit',
            'severity': 'Critical',
            'icon': 'journal-x',
            'action': f'Missing {assignments_total - assignments} out of {assignments_total} coursework assignments. Grant 7-day grace extension under lab supervisor guidance.'
        })

    # Financial Standing
    if fee_status == 'Overdue':
        interventions.append({
            'category': 'Financial Distress',
            'severity': 'Warning',
            'icon': 'cash-coin',
            'action': 'Fee overdue. Refer to Student Financial Aid Committee for installment schedule or scholarship consideration.'
        })

    if not interventions:
        interventions.append({
            'category': 'Commendation',
            'severity': 'Success',
            'icon': 'check-circle',
            'action': 'Student is meeting all academic and attendance milestones. Eligible for honors recognition.'
        })

    return interventions

@app.route('/')
def dashboard():
    """
    Renders the primary EduPredict analytics dashboard.
    """
    df = load_and_merge_data()
    analytics = get_analytics()
    model, metrics = load_ml_model()

    students = df.to_dict(orient='records')
    departments = sorted(list(df['department'].dropna().unique()))

    return render_template(
        'index.html',
        students=students,
        total=analytics['total'],
        at_risk=analytics['at_risk'],
        safe=analytics['safe'],
        at_risk_pct=analytics['at_risk_pct'],
        avg_att=analytics['avg_attendance'],
        avg_gpa=analytics['avg_gpa'],
        departments=departments,
        dept_stats=analytics['dept_stats'],
        fee_stats=analytics['fee_stats'],
        metrics=metrics
    )

@app.route('/api/students', methods=['GET'])
def get_students():
    """
    REST API: Retrieves filtered student list with search, department, and risk filters.
    """
    try:
        df = load_and_merge_data()
        
        # Filtering parameters
        dept = request.args.get('department', '').strip()
        risk = request.args.get('risk', '').strip()
        fee = request.args.get('fee', '').strip()
        search = request.args.get('search', '').strip().lower()

        if dept:
            df = df[df['department'].str.lower() == dept.lower()]
        if risk == 'high':
            df = df[df['dropout_risk_flag'] == 1]
        elif risk == 'safe':
            df = df[df['dropout_risk_flag'] == 0]
        if fee:
            df = df[df['fee_status'].str.lower() == fee.lower()]
        if search:
            mask = (
                df['student_id'].str.lower().str.contains(search, na=False) |
                df['name'].str.lower().str.contains(search, na=False) |
                df['department'].str.lower().str.contains(search, na=False)
            )
            df = df[mask]

        students = df.to_dict(orient='records')
        return jsonify({
            'success': True,
            'total': len(students),
            'students': students
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/students/<student_id>', methods=['GET'])
def get_student_detail(student_id):
    """
    REST API: Retrieves single student details with risk analysis and recommendations.
    """
    try:
        df = load_and_merge_data()
        stu = df[df['student_id'].str.upper() == student_id.strip().upper()]
        if stu.empty:
            return jsonify({'success': False, 'error': f"Student '{student_id}' not found"}), 404

        record = stu.iloc[0].to_dict()
        interventions = generate_interventions(
            gpa=float(record.get('gpa', 0)),
            attendance=float(record.get('attendance_pct', 0)),
            clicks=int(record.get('lms_clicks', 0)),
            assignments=int(record.get('assignments_submitted', 0)),
            assignments_total=int(record.get('assignments_total', 8)),
            fee_status=str(record.get('fee_status', 'Paid'))
        )
        record['interventions'] = interventions

        return jsonify({'success': True, 'student': record})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/students', methods=['POST'])
def create_student():
    """
    REST API: Creates a new student record and persists it to datasets.
    """
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({'success': False, 'error': 'Invalid JSON body'}), 400

        # Validate required fields
        stu_id = str(data.get('student_id', '')).strip().upper()
        name = str(data.get('name', '')).strip()
        dept = str(data.get('department', '')).strip()

        if not stu_id or not name or not dept:
            return jsonify({'success': False, 'error': 'student_id, name, and department are required'}), 400

        try:
            gpa = float(data.get('gpa', 0.0))
            att = float(data.get('attendance_pct', 0.0))
            clicks = int(data.get('lms_clicks', 0))
            submitted = int(data.get('assignments_submitted', 0))
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': 'gpa, attendance_pct, lms_clicks, and assignments_submitted must be valid numbers'}), 400

        if not (0.0 <= gpa <= 4.0):
            return jsonify({'success': False, 'error': 'GPA must be between 0.00 and 4.00'}), 400
        if not (0.0 <= att <= 100.0):
            return jsonify({'success': False, 'error': 'Attendance must be between 0.0% and 100.0%'}), 400

        # Predict risk using ML model or fallback
        model, _ = load_ml_model()
        if model is not None:
            features = pd.DataFrame([[gpa, att, clicks, submitted]], columns=['gpa', 'attendance_pct', 'lms_clicks', 'assignments_submitted'])
            risk_flag = int(model.predict(features)[0])
        else:
            risk_flag = 1 if (gpa < 2.2 or att < 60.0 or submitted < 4) else 0

        data['dropout_risk_flag'] = risk_flag
        saved_record = save_student_data(data, is_new=True)

        return jsonify({
            'success': True,
            'message': f"Student {stu_id} created successfully.",
            'student': saved_record
        }), 201
    except ValueError as ve:
        return jsonify({'success': False, 'error': str(ve)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/students/<student_id>', methods=['PUT'])
def update_student(student_id):
    """
    REST API: Updates an existing student record.
    """
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({'success': False, 'error': 'Invalid JSON body'}), 400

        data['student_id'] = student_id.strip().upper()
        
        # If numeric values updated, recalculate risk
        if 'gpa' in data or 'attendance_pct' in data:
            gpa = float(data.get('gpa', 2.5))
            att = float(data.get('attendance_pct', 75.0))
            clicks = int(data.get('lms_clicks', 100))
            submitted = int(data.get('assignments_submitted', 5))
            model, _ = load_ml_model()
            if model is not None:
                features = pd.DataFrame([[gpa, att, clicks, submitted]], columns=['gpa', 'attendance_pct', 'lms_clicks', 'assignments_submitted'])
                data['dropout_risk_flag'] = int(model.predict(features)[0])
            else:
                data['dropout_risk_flag'] = 1 if (gpa < 2.2 or att < 60.0 or submitted < 4) else 0

        saved_record = save_student_data(data, is_new=False)
        return jsonify({
            'success': True,
            'message': f"Student {student_id} updated successfully.",
            'student': saved_record
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/students/<student_id>', methods=['DELETE'])
def delete_student_api(student_id):
    """
    REST API: Deletes a student record.
    """
    try:
        success = delete_student(student_id)
        if not success:
            return jsonify({'success': False, 'error': f"Student '{student_id}' not found"}), 404
        return jsonify({
            'success': True,
            'message': f"Student {student_id} deleted successfully."
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/predict', methods=['POST'])
def predict():
    """
    REST API: Real-time ML Inference for Student Dropout Risk.
    Evaluates academic & LMS behavioral features using Random Forest with full probability and intervention report.
    """
    try:
        req_data = request.get_json(force=True, silent=True) or {}
        
        # Support flexible payload keys
        gpa_raw = req_data.get('gpa', 0.0)
        att_raw = req_data.get('attendance', req_data.get('attendance_pct', 0.0))
        clicks_raw = req_data.get('clicks', req_data.get('lms_clicks', 0))
        assignments_raw = req_data.get('assignments', req_data.get('assignments_submitted', 0))
        total_assignments_raw = req_data.get('assignments_total', 8)
        fee_status = str(req_data.get('fee_status', 'Paid')).strip()

        try:
            gpa = float(gpa_raw)
            attendance = float(att_raw)
            clicks = int(clicks_raw)
            assignments = int(assignments_raw)
            total_assignments = int(total_assignments_raw)
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'error': 'Inputs for gpa, attendance, clicks, and assignments must be valid numbers.'
            }), 400

        # Boundary checks
        if not (0.0 <= gpa <= 4.0):
            return jsonify({'success': False, 'error': 'GPA must be between 0.00 and 4.00'}), 400
        if not (0.0 <= attendance <= 100.0):
            return jsonify({'success': False, 'error': 'Attendance must be between 0.0% and 100.0%'}), 400
        if clicks < 0 or assignments < 0:
            return jsonify({'success': False, 'error': 'Clicks and assignments must be non-negative'}), 400

        # Perform ML Model inference
        model, metrics = load_ml_model()
        model_name = "Rule-Based Heuristic (Fallback)"
        prob_percent = None

        if model is not None:
            model_name = "Random Forest Classifier (Trained Model)"
            features = pd.DataFrame(
                [[gpa, attendance, clicks, assignments]], 
                columns=['gpa', 'attendance_pct', 'lms_clicks', 'assignments_submitted']
            )
            prediction = int(model.predict(features)[0])
            if hasattr(model, "predict_proba"):
                proba = model.predict_proba(features)[0]
                # Index 1 is probability of class 1 (at risk)
                prob_risk = proba[1] if len(proba) > 1 else proba[0]
                prob_percent = round(float(prob_risk) * 100, 1)
            else:
                prob_percent = 100.0 if prediction == 1 else 0.0
            risk = prediction
        else:
            # Rule-based fallback
            risk = 1 if (gpa < 2.2 or attendance < 60.0 or assignments < 4) else 0
            prob_percent = 90.0 if risk == 1 else 15.0

        if risk == 1:
            risk_level = "High Risk"
            recommendation = "HIGH RISK of Academic Failure / Dropout"
            badge_class = "danger"
        elif prob_percent and prob_percent >= 35.0:
            risk_level = "Moderate Advisory"
            recommendation = "MODERATE RISK - Early intervention recommended"
            badge_class = "warning"
        else:
            risk_level = "On Track"
            recommendation = "LOW RISK - Performing Normally and On Track"
            badge_class = "success"

        interventions = generate_interventions(
            gpa=gpa,
            attendance=attendance,
            clicks=clicks,
            assignments=assignments,
            assignments_total=total_assignments,
            fee_status=fee_status
        )

        return jsonify({
            'success': True,
            'risk_flag': risk,
            'risk_level': risk_level,
            'badge_class': badge_class,
            'probability': prob_percent,
            'recommendation': recommendation,
            'model_used': model_name,
            'interventions': interventions,
            'features_analyzed': {
                'gpa': gpa,
                'attendance_pct': attendance,
                'lms_clicks': clicks,
                'assignments_submitted': assignments,
                'assignments_total': total_assignments,
                'fee_status': fee_status
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/analytics', methods=['GET'])
def analytics_api():
    """
    REST API: Comprehensive analytics payload for dashboards and charts.
    """
    try:
        analytics = get_analytics()
        _, metrics = load_ml_model()
        analytics['model_metrics'] = metrics
        return jsonify({'success': True, 'data': analytics})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/retrain', methods=['POST'])
def retrain_model_api():
    """
    REST API: Retrains the Random Forest Model on current dataset and refreshes in-memory cache.
    """
    try:
        from models.train_predictive_models import train_dropout_model
        clf, metrics = train_dropout_model()
        load_ml_model()
        return jsonify({
            'success': True,
            'message': 'Predictive model retrained successfully.',
            'metrics': metrics
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/export/csv', methods=['GET'])
def export_csv():
    """
    Exports the current student dataset as a downloadable CSV.
    """
    try:
        df = load_and_merge_data()
        csv_data = df.to_csv(index=False)
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=EduPredict_Students_Export.csv"}
        )
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found(e):
    if request.path.startswith('/api/'):
        return jsonify({'success': False, 'error': 'Endpoint not found'}), 404
    return render_template('index.html', error="Page not found"), 404

@app.errorhandler(500)
def server_error(e):
    if request.path.startswith('/api/'):
        return jsonify({'success': False, 'error': 'Internal server error'}), 500
    return render_template('index.html', error="Internal server error"), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"[INFO] EduPredict Server launching on http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)
