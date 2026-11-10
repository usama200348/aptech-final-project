import os
import sys
import json
import pytest

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_dashboard_route(client):
    response = client.get('/')
    assert response.status_code == 200
    html = response.data.decode('utf-8')
    assert "EduPredict" in html
    assert "Total Enrolled" in html
    assert "High Dropout Risk" in html

def test_api_analytics(client):
    response = client.get('/api/analytics')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert data['data']['total'] > 0
    assert 'dept_stats' in data['data']

def test_api_students_list(client):
    response = client.get('/api/students')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert len(data['students']) > 0

def test_api_students_filter_department(client):
    response = client.get('/api/students?department=Computer Science')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    for s in data['students']:
        assert s['department'].lower() == 'computer science'

def test_api_students_filter_risk(client):
    response = client.get('/api/students?risk=high')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    for s in data['students']:
        assert s['dropout_risk_flag'] == 1

def test_api_student_detail(client):
    response = client.get('/api/students/STU1001')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert data['student']['student_id'] == 'STU1001'
    assert 'interventions' in data['student']

def test_api_predict_valid(client):
    payload = {
        'gpa': 1.6,
        'attendance': 45.0,
        'clicks': 60,
        'assignments': 2,
        'fee_status': 'Overdue'
    }
    response = client.post('/api/predict', json=payload)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert data['risk_flag'] == 1
    assert data['probability'] >= 60.0
    assert len(data['interventions']) > 0

def test_api_predict_invalid_bounds(client):
    # GPA > 4.0 should fail validation
    payload = {'gpa': 5.5, 'attendance': 80.0, 'clicks': 100, 'assignments': 5}
    response = client.post('/api/predict', json=payload)
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['success'] is False
    assert "GPA must be between" in data['error']

def test_api_predict_invalid_types(client):
    payload = {'gpa': 'invalid_string', 'attendance': 80.0}
    response = client.post('/api/predict', json=payload)
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['success'] is False

def test_api_crud_flow(client):
    test_id = "STU_API_TEST_101"
    
    # 1. Create
    new_student = {
        'student_id': test_id,
        'name': 'API Flow Test',
        'gender': 'F',
        'department': 'Data Science',
        'gpa': 3.75,
        'previous_qualification': 'A-Levels',
        'fee_status': 'Paid',
        'attendance_pct': 92.0,
        'lms_clicks': 310,
        'assignments_submitted': 8,
        'course_code': 'DS-501'
    }
    res_create = client.post('/api/students', json=new_student)
    assert res_create.status_code == 201
    
    # 2. Get Detail
    res_get = client.get(f'/api/students/{test_id}')
    assert res_get.status_code == 200
    assert json.loads(res_get.data)['student']['name'] == 'API Flow Test'

    # 3. Update
    res_update = client.put(f'/api/students/{test_id}', json={'gpa': 3.95, 'attendance_pct': 95.0})
    assert res_update.status_code == 200

    # 4. Delete
    res_del = client.delete(f'/api/students/{test_id}')
    assert res_del.status_code == 200

    # 5. Confirm deletion
    res_confirm = client.get(f'/api/students/{test_id}')
    assert res_confirm.status_code == 404

def test_api_export_csv(client):
    response = client.get('/api/export/csv')
    assert response.status_code == 200
    assert "text/csv" in response.headers.get('Content-Type', '')
    content = response.data.decode('utf-8')
    assert "student_id" in content
    assert "dropout_risk_flag" in content
