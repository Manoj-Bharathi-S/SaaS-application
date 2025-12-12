from fastapi import FastAPI, HTTPException
print("Loading ML Service modules...")
from pydantic import BaseModel
import pandas as pd
import joblib
from sklearn.ensemble import IsolationForest
import os

app = FastAPI(title="ML Service")

MODEL_PATH = "model.joblib"
DATA_PATH = "data/activity_logs.csv"

# Global model
model = None

def load_model():
    global model
    if os.path.exists(MODEL_PATH):
        try:
            model = joblib.load(MODEL_PATH)
            print("Model loaded successfully.")
        except:
            print("Failed to load model.")
            model = None

@app.on_event("startup")
def startup():
    load_model()

@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": model is not None}

class TrainRequest(BaseModel):
    contamination: float = 0.05

@app.post("/train")
def train(req: TrainRequest):
    global model
    if not os.path.exists(DATA_PATH):
        raise HTTPException(status_code=404, detail="Training data not found. Run generator script.")
    
    df = pd.read_csv(DATA_PATH)
    features = df[['hour', 'download_mb', 'failed_logins', 'role_mismatch']]
    
    clf = IsolationForest(contamination=req.contamination, random_state=42)
    clf.fit(features)
    
    joblib.dump(clf, MODEL_PATH)
    model = clf
    
    return {"status": "trained", "n_samples": len(df)}

class ScoreRequest(BaseModel):
    features: dict 
    # expected keys: hour, download_mb, failed_logins, role_mismatch

@app.post("/score")
def score(req: ScoreRequest):
    if model is None:
        raise HTTPException(status_code=503, detail="Model not trained yet.")
    
    # Extract features in correct order
    try:
        f = req.features
        # Ensure order matches training
        X = pd.DataFrame([{
            'hour': f.get('hour', 12),
            'download_mb': f.get('download_mb', 10),
            'failed_logins': f.get('failed_logins', 0),
            'role_mismatch': f.get('role_mismatch', 0)
        }])
        
        # Predict: 1 for inlier, -1 for outlier
        pred = model.predict(X)[0]
        score_val = model.decision_function(X)[0]
        
        is_anomaly = True if pred == -1 else False
        
        return {
            "score": float(score_val),
            "is_anomaly": is_anomaly
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("Starting ML Service on port 8007")
    uvicorn.run(app, host="0.0.0.0", port=8007)
