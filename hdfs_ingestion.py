import os
import sys
import shutil
import subprocess

def run_hdfs_ingestion():
    """
    Ingests EduPredict academic records and LMS logs into HDFS.
    If Hadoop CLI ('hdfs') is available, connects to Hadoop cluster.
    Otherwise, stages files into a local simulated HDFS storage structure (./hdfs_storage).
    """
    print("=" * 60)
    print(" EduPredict Big Data HDFS Ingestion Pipeline")
    print("=" * 60)

    project_root = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(project_root, 'data')
    csv_file = os.path.join(data_dir, 'student_academic_records.csv')
    if not os.path.exists(csv_file):
        csv_file = os.path.join(data_dir, 'EduPredict_Student_Dataset.csv')
    json_file = os.path.join(data_dir, 'lms_attendance_logs.json')

    hdfs_bin = shutil.which('hdfs')
    
    if hdfs_bin:
        print(f"[INFO] Detected Hadoop HDFS binary at: {hdfs_bin}")
        try:
            # 1. Create HDFS directories
            subprocess.run([hdfs_bin, 'dfs', '-mkdir', '-p', '/edupredict/raw/academic_records'], check=True)
            subprocess.run([hdfs_bin, 'dfs', '-mkdir', '-p', '/edupredict/raw/lms_logs'], check=True)
            subprocess.run([hdfs_bin, 'dfs', '-mkdir', '-p', '/edupredict/processed'], check=True)

            # 2. Upload datasets
            subprocess.run([hdfs_bin, 'dfs', '-put', '-f', csv_file, '/edupredict/raw/academic_records/'], check=True)
            subprocess.run([hdfs_bin, 'dfs', '-put', '-f', json_file, '/edupredict/raw/lms_logs/'], check=True)

            print("[INFO] Upload to HDFS Cluster completed successfully.")
            subprocess.run([hdfs_bin, 'dfs', '-ls', '/edupredict/raw/academic_records'])
            subprocess.run([hdfs_bin, 'dfs', '-ls', '/edupredict/raw/lms_logs'])
            return True
        except Exception as e:
            print(f"[WARNING] Hadoop HDFS command encountered an issue: {e}")
            print("[INFO] Falling back to staging environment simulation...")

    # Simulated / Staging mode for local development and Windows Aptech evaluation
    print("[INFO] Live Hadoop cluster not detected or unreachable. Using Staging / Simulation Mode.")
    simulated_hdfs = os.path.join(project_root, 'hdfs_storage')
    raw_academic = os.path.join(simulated_hdfs, 'edupredict', 'raw', 'academic_records')
    raw_lms = os.path.join(simulated_hdfs, 'edupredict', 'raw', 'lms_logs')
    processed_dir = os.path.join(simulated_hdfs, 'edupredict', 'processed')

    os.makedirs(raw_academic, exist_ok=True)
    os.makedirs(raw_lms, exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)

    dest_csv = os.path.join(raw_academic, 'student_academic_records.csv')
    dest_json = os.path.join(raw_lms, 'lms_attendance_logs.json')

    shutil.copy2(csv_file, dest_csv)
    shutil.copy2(json_file, dest_json)

    print(f"[SUCCESS] Staged academic records to: {dest_csv}")
    print(f"[SUCCESS] Staged LMS logs to:        {dest_json}")
    print("=" * 60)
    print(" HDFS Ingestion Pipeline Completed Successfully!")
    print("=" * 60)
    return True

if __name__ == '__main__':
    run_hdfs_ingestion()
