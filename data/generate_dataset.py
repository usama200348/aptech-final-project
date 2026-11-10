import os
import json
import random
import pandas as pd

def generate_full_dataset(num_additional=192):
    """
    Enriches the EduPredict student dataset while preserving all original STU1001-STU1008 records.
    Produces both CSV and JSON formats with synchronized data.
    """
    data_dir = os.path.dirname(os.path.abspath(__file__))
    csv_primary = os.path.join(data_dir, 'EduPredict_Student_Dataset.csv')
    csv_academic = os.path.join(data_dir, 'student_academic_records.csv')
    json_path = os.path.join(data_dir, 'lms_attendance_logs.json')

    # Seed for reproducibility
    random.seed(42)

    # Original records
    original_students = [
        {"student_id": "STU1001", "name": "Ahmad Khan", "gender": "M", "department": "Computer Science", "gpa": 3.65, "previous_qualification": "A-Levels", "fee_status": "Paid", "attendance_pct": 92.5, "lms_clicks": 340, "assignments_submitted": 8, "assignments_total": 8, "dropout_risk_flag": 0, "course_code": "CS-401"},
        {"student_id": "STU1002", "name": "Fatima Ali", "gender": "F", "department": "Software Engineering", "gpa": 2.10, "previous_qualification": "FSc Pre-Eng", "fee_status": "Pending", "attendance_pct": 58.0, "lms_clicks": 110, "assignments_submitted": 4, "assignments_total": 8, "dropout_risk_flag": 1, "course_code": "SE-302"},
        {"student_id": "STU1003", "name": "Zainab Hassan", "gender": "F", "department": "Data Science", "gpa": 3.88, "previous_qualification": "A-Levels", "fee_status": "Paid", "attendance_pct": 96.0, "lms_clicks": 480, "assignments_submitted": 8, "assignments_total": 8, "dropout_risk_flag": 0, "course_code": "DS-501"},
        {"student_id": "STU1004", "name": "Bilal Ahmed", "gender": "M", "department": "Information Technology", "gpa": 1.85, "previous_qualification": "FSc Pre-Eng", "fee_status": "Overdue", "attendance_pct": 45.0, "lms_clicks": 75, "assignments_submitted": 2, "assignments_total": 8, "dropout_risk_flag": 1, "course_code": "IT-201"},
        {"student_id": "STU1005", "name": "Hamza Sheikh", "gender": "M", "department": "Computer Science", "gpa": 2.95, "previous_qualification": "FSc Pre-Eng", "fee_status": "Paid", "attendance_pct": 81.0, "lms_clicks": 230, "assignments_submitted": 7, "assignments_total": 8, "dropout_risk_flag": 0, "course_code": "CS-401"},
        {"student_id": "STU1006", "name": "Sana Malik", "gender": "F", "department": "Cyber Security", "gpa": 3.40, "previous_qualification": "A-Levels", "fee_status": "Paid", "attendance_pct": 89.0, "lms_clicks": 310, "assignments_submitted": 8, "assignments_total": 8, "dropout_risk_flag": 0, "course_code": "CY-101"},
        {"student_id": "STU1007", "name": "Usman Tariq", "gender": "M", "department": "Software Engineering", "gpa": 1.60, "previous_qualification": "FSc Pre-Eng", "fee_status": "Overdue", "attendance_pct": 40.0, "lms_clicks": 50, "assignments_submitted": 1, "assignments_total": 8, "dropout_risk_flag": 1, "course_code": "SE-302"},
        {"student_id": "STU1008", "name": "Ayesha Siddiqui", "gender": "F", "department": "Data Science", "gpa": 3.15, "previous_qualification": "A-Levels", "fee_status": "Paid", "attendance_pct": 85.0, "lms_clicks": 290, "assignments_submitted": 7, "assignments_total": 8, "dropout_risk_flag": 0, "course_code": "DS-501"}
    ]

    first_names_m = ["Muhammad", "Ali", "Hassan", "Hussein", "Omer", "Abdullah", "Mustafa", "Zubair", "Haris", "Saad", "Farhan", "Danish", "Taha", "Waqas", "Nabeel", "Shahid", "Kashif", "Adeel", "Raza", "Imran"]
    first_names_f = ["Maryam", "Hiba", "Mahnoor", "Noor", "Hafsa", "Sadia", "Khadija", "Rimsha", "Anum", "Iqra", "Hira", "Mehak", "Bushra", "Laiba", "Aliza", "Sundas", "Kinza", "Sidra", "Farah", "Amna"]
    last_names = ["Khan", "Ahmed", "Malik", "Sheikh", "Qureshi", "Chaudhry", "Ansari", "Bhatti", "Raza", "Abbasi", "Mirza", "Gondal", "Javed", "Shah", "Siddiqui", "Rehman", "Akhtar", "Farooq", "Yousaf", "Mughal"]

    dept_courses = {
        "Computer Science": "CS-401",
        "Software Engineering": "SE-302",
        "Data Science": "DS-501",
        "Information Technology": "IT-201",
        "Cyber Security": "CY-101",
        "Artificial Intelligence": "AI-303"
    }

    qualifications = ["FSc Pre-Eng", "A-Levels", "ICS", "DAE"]
    fee_options = ["Paid", "Paid", "Paid", "Pending", "Overdue"]

    records = list(original_students)

    for i in range(1009, 1009 + num_additional):
        stu_id = f"STU{i}"
        gender = random.choice(["M", "F"])
        first_name = random.choice(first_names_m if gender == "M" else first_names_f)
        last_name = random.choice(last_names)
        name = f"{first_name} {last_name}"
        dept = random.choice(list(dept_courses.keys()))
        course = dept_courses[dept]
        qual = random.choice(qualifications)
        fee = random.choice(fee_options)

        # Generate realistic student profiles:
        # Profile type: High Performer (40%), Average (35%), Struggling/At Risk (25%)
        profile = random.choices(["high", "avg", "struggling"], weights=[0.40, 0.35, 0.25])[0]

        if profile == "high":
            gpa = round(random.uniform(3.2, 4.0), 2)
            att = round(random.uniform(80.0, 99.0), 1)
            clicks = random.randint(220, 520)
            submitted = random.choice([7, 8, 8, 8])
            risk = 0
            fee = random.choice(["Paid", "Paid", "Pending"])
        elif profile == "avg":
            gpa = round(random.uniform(2.4, 3.2), 2)
            att = round(random.uniform(65.0, 82.0), 1)
            clicks = random.randint(120, 260)
            submitted = random.choice([5, 6, 7])
            risk = 0
        else: # struggling
            gpa = round(random.uniform(1.2, 2.2), 2)
            att = round(random.uniform(35.0, 62.0), 1)
            clicks = random.randint(30, 130)
            submitted = random.choice([0, 1, 2, 3, 4])
            # Determine risk flag based on real educational risk factors
            risk = 1 if (gpa < 2.2 or att < 60.0 or submitted < 4) else 0
            if fee == "Paid" and random.random() < 0.6:
                fee = random.choice(["Pending", "Overdue"])

        records.append({
            "student_id": stu_id,
            "name": name,
            "gender": gender,
            "department": dept,
            "gpa": gpa,
            "previous_qualification": qual,
            "fee_status": fee,
            "attendance_pct": att,
            "lms_clicks": clicks,
            "assignments_submitted": submitted,
            "assignments_total": 8,
            "dropout_risk_flag": risk,
            "course_code": course
        })

    # Prepare Academic Records DataFrame (CSV)
    df_all = pd.DataFrame(records)
    csv_cols = ["student_id", "name", "gender", "department", "gpa", "previous_qualification", 
                "fee_status", "attendance_pct", "lms_clicks", "assignments_submitted", 
                "assignments_total", "dropout_risk_flag"]
    df_csv = df_all[csv_cols]

    # Save to both CSV filenames so no code ever breaks
    df_csv.to_csv(csv_primary, index=False)
    df_csv.to_csv(csv_academic, index=False)

    # Prepare LMS Attendance Logs (JSON)
    json_cols = ["student_id", "course_code", "attendance_pct", "lms_clicks", 
                 "assignments_submitted", "assignments_total"]
    lms_records = df_all[json_cols].to_dict(orient="records")

    with open(json_path, "w") as f:
        json.dump(lms_records, f, indent=2)

    print(f"[SUCCESS] Generated {len(records)} student records.")
    print(f" - CSV saved to: {csv_primary} and {csv_academic}")
    print(f" - JSON saved to: {json_path}")
    print(f" - Total At-Risk Students: {df_all['dropout_risk_flag'].sum()} ({round(df_all['dropout_risk_flag'].mean()*100, 1)}%)")

if __name__ == "__main__":
    generate_full_dataset()
