# Layer 5 — AI/ML → Login Page → Dashboard → Alert
## Machine Learning Pipeline, 60-Second Prediction Horizon & Role-Based Auth

### 1. Objective
Implement an end-to-end Machine Learning pipeline that forecasts production bottlenecks 60 seconds into the future without data leakage, compares against a rule-based baseline, performs real-time inference, and secures the dashboard with role-based authentication.

### 2. Implemented Components
- **Synthetic Dataset Generator:** `ml/generate_dataset.py`
  - Generates 15 independent manufacturing runs.
  - Constructs ground truth target strictly in the future window $[t+10s, t+60s]$.
- **Training Pipeline:** `ml/train.py`
  - Random Forest Classifier (100 estimators, depth 8, balanced class weights).
  - Evaluates against Rule-Based Baseline heuristic.
  - Computes Accuracy, Precision, Recall, F1, ROC-AUC, and Confusion Matrix.
  - Serializes artifact to `ml/models/bottleneck_rf_model.joblib`.
- **Standalone Evaluator:** `ml/evaluate.py`
- **Real-Time Predictor Daemon:** `src/prediction/predictor.py`
  - Maintains 10-second rolling feature buffer, executes inference, and publishes to `factory/predictions`.
- **Authentication & RBAC:** `src/common/auth.py`
  - Salted PBKDF2-HMAC-SHA256 password hashing.
  - Administrator (`admin`) and Operator (`operator`) roles.

### 3. How to Run & Verify
```bash
# Execute Layer 5 acceptance test
bash scripts/run_layer5.sh
```

### 4. Acceptance Criteria Checklist
- [x] Machine Learning pipeline implemented with scikit-learn.
- [x] Strict 60-second future target without data leakage.
- [x] Evaluation metrics (Accuracy, Precision, Recall, F1, ROC-AUC, Confusion Matrix) verified.
- [x] Real-time inference daemon active and logging predictions.
- [x] Salted password hashing and role-based login system operational.

