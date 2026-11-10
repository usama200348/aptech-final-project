#!/bin/bash
# EduPredict HDFS Data Ingestion Script
# Compatible with Apache Hadoop 2.x/3.x HDFS clusters

echo "=================================================="
echo " Starting HDFS EduPredict Ingestion Pipeline "
echo "=================================================="

# 1. Create HDFS directories
echo "[INFO] Creating HDFS Directory Hierarchy..."
hdfs dfs -mkdir -p /edupredict/raw/academic_records
hdfs dfs -mkdir -p /edupredict/raw/lms_logs
hdfs dfs -mkdir -p /edupredict/processed

# 2. Upload Academic Records CSV (Check both naming variants)
if [ -f "./data/student_academic_records.csv" ]; then
    echo "[INFO] Uploading student_academic_records.csv to HDFS..."
    hdfs dfs -put -f ./data/student_academic_records.csv /edupredict/raw/academic_records/
elif [ -f "./data/EduPredict_Student_Dataset.csv" ]; then
    echo "[INFO] Uploading EduPredict_Student_Dataset.csv to HDFS..."
    hdfs dfs -put -f ./data/EduPredict_Student_Dataset.csv /edupredict/raw/academic_records/student_academic_records.csv
fi

# 3. Upload LMS Logs JSON
if [ -f "./data/lms_attendance_logs.json" ]; then
    echo "[INFO] Uploading lms_attendance_logs.json to HDFS..."
    hdfs dfs -put -f ./data/lms_attendance_logs.json /edupredict/raw/lms_logs/
fi

# 4. Verify upload
echo "[INFO] Contents of HDFS /edupredict/raw/academic_records:"
hdfs dfs -ls /edupredict/raw/academic_records

echo "[INFO] Contents of HDFS /edupredict/raw/lms_logs:"
hdfs dfs -ls /edupredict/raw/lms_logs

echo "=================================================="
echo " HDFS Data Ingestion Completed Successfully! "
echo "=================================================="
