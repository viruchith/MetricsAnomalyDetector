import os
import pandas as pd
import joblib
import logging
from datetime import datetime
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

# Setup logging for predictions
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('predictions.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI()

MODEL_PATH = "failure_predictor.pkl"
ENCODER_PATH = "label_encoder.pkl"
FEATURES_PATH = "features.pkl"

def preprocess(df):
    # Fill missing hardware_failure_type with 'none'
    df['hardware_failure_type'] = df['hardware_failure_type'].fillna('none')
    # Encode categorical features
    categorical_cols = ['hard_disk_status', 'power_supply_status', 'network_card_status', 'motherboard_status']
    df = pd.get_dummies(df, columns=categorical_cols)
    # Return processed df
    return df

def extract_features(df, features=None):
    if features is None:
        return df
    missing = [f for f in features if f not in df.columns]
    for m in missing:
        df[m] = 0
    return df[features]

@app.post("/train")
async def train_model(file: UploadFile = File(...)):
    logger.info(f"=== MODEL TRAINING REQUEST ===")
    logger.info(f"Training file received: {file.filename}")
    
    df = pd.read_csv(file.file)
    logger.info(f"Training data loaded: {len(df)} records from {df['machine_id'].nunique()} machines")
    
    df = preprocess(df)
    le = LabelEncoder()
    df['failure_type_encoded'] = le.fit_transform(df['hardware_failure_type'])
    
    # Log training data distribution
    failure_dist = df['hardware_failure_type'].value_counts()
    logger.info(f"Training data distribution:")
    for failure_type, count in failure_dist.items():
        logger.info(f"  - {failure_type}: {count} instances")
    
    # Select features
    drop_cols = ['timestamp', 'machine_id', 'hardware_failure_type', 'hardware_failure_type', 'failure', 'failure_type_encoded']
    features = [c for c in df.columns if c not in drop_cols]
    X = df[features]
    y = df['failure_type_encoded']
    
    logger.info(f"Training with {len(features)} features: {features}")
    
    # Train model
    clf = RandomForestClassifier(class_weight='balanced', random_state=42)
    clf.fit(X, y)
    
    # Save model, encoder, and feature list
    joblib.dump(clf, MODEL_PATH)
    joblib.dump(le, ENCODER_PATH)
    joblib.dump(features, FEATURES_PATH)
    
    logger.info("Model training completed successfully")
    logger.info(f"Model saved to: {MODEL_PATH}")
    logger.info(f"Label encoder saved to: {ENCODER_PATH}")
    logger.info(f"Features saved to: {FEATURES_PATH}")
    logger.info(f"Classes learned: {list(le.classes_)}")
    logger.info(f"=== END TRAINING REQUEST ===\n")
    
    return {"message": "Model trained and saved successfully.", "classes": list(le.classes_)}

@app.post("/predict")
async def predict_failure(file: UploadFile = File(...)):
    # Log the incoming prediction request
    logger.info(f"=== NEW PREDICTION REQUEST ===")
    logger.info(f"File received: {file.filename}")
    logger.info(f"Content type: {file.content_type}")
    
    # Check if model exists
    if not os.path.exists(MODEL_PATH) or not os.path.exists(ENCODER_PATH) or not os.path.exists(FEATURES_PATH):
        logger.error("Model files not found - training required")
        return JSONResponse(status_code=400, content={"error": "Model not trained yet. Please train first."})
    
    # Load model and process data
    logger.info("Loading trained model and preprocessing data...")
    clf = joblib.load(MODEL_PATH)
    le = joblib.load(ENCODER_PATH)
    features = joblib.load(FEATURES_PATH)
    
    df = pd.read_csv(file.file)
    logger.info(f"Data loaded: {len(df)} records from {df['machine_id'].nunique()} machines")
    
    df = preprocess(df)
    X = extract_features(df, features)
    
    # Make predictions
    logger.info("Generating predictions...")
    y_pred = clf.predict(X)
    predictions = le.inverse_transform(y_pred)
    df['predicted_failure_type'] = predictions
    
    # Log prediction summary
    failure_counts = pd.Series(predictions).value_counts()
    logger.info(f"Prediction summary:")
    for failure_type, count in failure_counts.items():
        logger.info(f"  - {failure_type}: {count} instances")
    
    # Log individual predictions for failures (non-"none" predictions)
    failure_predictions = df[df['predicted_failure_type'] != 'none']
    if not failure_predictions.empty:
        logger.warning(f"CRITICAL: {len(failure_predictions)} potential failures detected!")
        for _, row in failure_predictions.iterrows():
            logger.warning(f"  FAILURE ALERT - Machine {row['machine_id']} at {row['timestamp']}: {row['predicted_failure_type']} failure predicted")
    else:
        logger.info("No failures predicted - all systems operating normally")
    
    result = df[['timestamp', 'machine_id', 'predicted_failure_type']].to_dict(orient='records')
    
    logger.info(f"Prediction request completed successfully - {len(result)} predictions returned")
    logger.info(f"=== END PREDICTION REQUEST ===\n")
    
    return {"predictions": result}