# 🔁 Persistent Predictive Maintenance System
# Reuses saved models if available
# Trains only if models missing or forced
# Predicts future failure risk on latest data

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import joblib
import os
from io import StringIO
import warnings

warnings.filterwarnings('ignore')

# -----------------------------
# Configuration
# -----------------------------
DATA_FILE = 'machinedata copy.csv'         # Save data to file for persistence
MODELS_DIR = 'models'
ENCODERS_DIR = 'encoders'
FORCE_RETRAIN = False  # Set to True to retrain even if models exist

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(ENCODERS_DIR, exist_ok=True)

# -----------------------------
# Step 1: Load Data (from string or file)
# -----------------------------
print("🚀 Loading machine sensor data...\n")

# For demo: using inline data (replace with pd.read_csv(DATA_FILE) in production)

df = pd.read_csv(DATA_FILE)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.sort_values(['machine_id', 'timestamp']).reset_index(drop=True)

print(f"📊 Loaded {len(df)} readings from {df['machine_id'].nunique()} machines.")

# Failure types to model
failure_types = ['hard_disk', 'fan', 'power_supply', 'network_card', 'motherboard']
status_cols = [
    'hard_disk_status',
    'power_supply_status',
    'network_card_status',
    'motherboard_status'
]
features = [
    'machine_id_encoded', 'temperature', 'vibration', 'pressure', 'current',
    'hard_disk_status', 'fan_speed', 'power_supply_status',
    'network_card_status', 'motherboard_status',
    'hour', 'minute',
    'temperature_rolling_avg', 'vibration_rolling_avg', 'current_rolling_avg',
    'temp_fan_ratio', 'current_pressure_ratio', 'vibration_temp_interaction'
]

# -----------------------------
# Step 2: Feature Engineering
# -----------------------------
print("⚙️ Engineering features...")

df['hour'] = df['timestamp'].dt.hour
df['minute'] = df['timestamp'].dt.minute

for col in ['temperature', 'vibration', 'current']:
    df[f'{col}_rolling_avg'] = df.groupby('machine_id')[col].transform(lambda x: x.rolling(3, 1).mean())

df['temp_fan_ratio'] = df['temperature'] / (df['fan_speed'] / 100)
df['current_pressure_ratio'] = df['current'] / df['pressure']
df['vibration_temp_interaction'] = df['vibration'] * df['temperature']

df['hardware_failure_type'] = df['hardware_failure_type'].fillna('none')

# -----------------------------
# Step 3: Encode Categorical Features
# -----------------------------
print("🔐 Encoding categorical features...")

# Reload or create encoders
for col in status_cols:
    encoder_path = f'{ENCODERS_DIR}/{col}_encoder.pkl'
    if os.path.exists(encoder_path) and not FORCE_RETRAIN:
        le = joblib.load(encoder_path)
        df[col] = le.transform(df[col].astype(str))
        print(f"   🔄 Loaded encoder for '{col}'")
    else:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col].astype(str))
        joblib.dump(le, encoder_path)
        print(f"   ✅ Saved new encoder for '{col}'")

# Machine ID encoder
encoder_path = f'{ENCODERS_DIR}/machine_id_encoder.pkl'
if os.path.exists(encoder_path) and not FORCE_RETRAIN:
    le_machine = joblib.load(encoder_path)
    df['machine_id_encoded'] = le_machine.transform(df['machine_id'])
    print("   🔄 Loaded machine_id encoder")
else:
    le_machine = LabelEncoder()
    df['machine_id_encoded'] = le_machine.fit_transform(df['machine_id'])
    joblib.dump(le_machine, encoder_path)
    print("   ✅ Saved new machine_id encoder")

# -----------------------------
# Step 4: Train or Load Models
# -----------------------------
X = df[features].copy()

print("\n🔁 Checking for existing models...\n")
models_exist = all(os.path.exists(f'{MODELS_DIR}/{ft}_predictor.pkl') for ft in failure_types)

if models_exist and not FORCE_RETRAIN:
    print("🟢 Models found. Skipping training. Using saved models.")
else:
    print("🟡 Training models (first run or forced retrain)...")
    for failure in failure_types:
        print(f"\n🤖 Training model for '{failure}'...")

        # Label: will this failure occur in next 3 steps?
        y = pd.Series(0, index=df.index)
        for idx in df.index:
            end_idx = min(idx + 3, len(df))
            window = df.iloc[idx:end_idx]
            if (window['hardware_failure_type'] == failure).any():
                y.iloc[idx] = 1

        # Time-based split
        split_idx = int(0.7 * len(df))
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

        # Skip if only one class
        if y_train.nunique() < 2:
            print(f"   ⚠️  Not enough positive samples for '{failure}'. Skipping model.")
            continue

        clf = RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42)
        clf.fit(X_train, y_train)

        # Save model
        joblib.dump(clf, f'{MODELS_DIR}/{failure}_predictor.pkl')
        print(f"   💾 Model saved for '{failure}'")

# -----------------------------
# Step 5: Predict on Latest Data
# -----------------------------
print("\n🔮 Loading models and predicting future risks...\n")

# Load original data for string decoding
original_df = pd.read_csv(DATA_FILE)
original_df['timestamp'] = pd.to_datetime(original_df['timestamp'])
latest_full = original_df.groupby('machine_id').last().reset_index()

# Get latest encoded features
latest_encoded = df.groupby('machine_id').last().reset_index()
X_latest = latest_encoded[features].copy()

# Icons for output
icons = {
    'hard_disk': '🔧',
    'fan': '🌀',
    'power_supply': '⚡',
    'network_card': '📡',
    'motherboard': '🧠'
}

print("🚨 FAILURE RISK FORECAST (Reusing Saved Models)\n")
print(f"{'Machine':<10} {'Risk Type':<18} {'Level':<10} {'Confidence':<12} {'Indicators'}")
print("-" * 85)

for idx, row in X_latest.iterrows():
    machine_id = latest_full.iloc[idx]['machine_id']

    # Diagnose current state
    temp = latest_full.iloc[idx]['temperature']
    vib = latest_full.iloc[idx]['vibration']
    fan = latest_full.iloc[idx]['fan_speed']
    curr = latest_full.iloc[idx]['current']
    indicators = []
    if temp > 80: indicators.append("High Temp")
    if vib > 0.2: indicators.append("High Vib")
    if fan < 1200: indicators.append("Low Fan")
    if curr > 12.0: indicators.append("High Current")

    # Predict each model
    risks = {}
    X_input = row[features].values.reshape(1, -1)

    for name in failure_types:
        model_path = f'{MODELS_DIR}/{name}_predictor.pkl'
        if not os.path.exists(model_path):
            risks[name] = 0.0
            continue

        model = joblib.load(model_path)
        proba = model.predict_proba(X_input)

        # Handle single-class output
        failure_prob = proba[0, 1] if proba.shape[1] > 1 else 0.0
        risks[name] = failure_prob

    # Find highest risk
    if not risks or all(v == 0.0 for v in risks.values()):
        top_failure = "none"
        confidence = 0.0
        risk_level = "🟢 Low"
        icon = "✅"
    else:
        top_failure = max(risks, key=risks.get)
        confidence = risks[top_failure]
        risk_level = "🔴 High" if confidence > 0.7 else "🟡 Medium" if confidence > 0.4 else "🟢 Low"
        icon = icons.get(top_failure, "⚠️")

    print(f"{machine_id:<10} "
          f"{icon + ' ' + top_failure.replace('_', ' ').title():<18} "
          f"{risk_level:<10} "
          f"{confidence:6.1%}     "
          f"{'; '.join(indicators) if indicators else 'None'}")