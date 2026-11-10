import os
import sys

# Ensure project root is in sys.path
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app.app import app, load_ml_model
from app.data_loader import get_data_paths

def main():
    print("=" * 65)
    print("🎓 EduPredict - Big Data Analytics Portal & Dropout Predictor")
    print("   Aptech Final Semester eProject")
    print("=" * 65)

    paths = get_data_paths()

    # If model is not yet trained, train it automatically on startup
    if not os.path.exists(paths['model_pkl']):
        print("[INFO] Trained ML model not found. Automatically training Random Forest...")
        from models.train_predictive_models import train_dropout_model
        train_dropout_model()

    load_ml_model()

    port = int(os.environ.get('PORT', 5000))
    print(f"\n[SUCCESS] EduPredict Portal is active!")
    print(f"👉 Access Web Application at: http://127.0.0.1:{port}")
    print(f"👉 REST API Predict Endpoint: http://127.0.0.1:{port}/api/predict")
    print(f"👉 REST API Analytics:        http://127.0.0.1:{port}/api/analytics")
    print("=" * 65 + "\n")

    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    main()
