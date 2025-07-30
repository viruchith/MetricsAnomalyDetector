# 🛠️ Predictive Maintenance System
# With User-Friendly Output: Failure Risk + Time to Failure
# Reuses saved models across runs

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
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
DATA_FILE = 'machinedata copy.csv'
MODELS_DIR = 'models'
ENCODERS_DIR = 'encoders'
FORCE_RETRAIN = False  # Set to True to retrain

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(ENCODERS_DIR, exist_ok=True)

# -----------------------------
# Step 1: Load Data
# -----------------------------
print("🚀 Loading machine sensor data...\n")

df = pd.read_csv(DATA_FILE)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.sort_values(['machine_id', 'timestamp']).reset_index(drop=True)

print(f"📊 Loaded {len(df)} sensor readings from {df['machine_id'].nunique()} machines.\n")

# Define failure types
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

for col in status_cols:
    path = f'{ENCODERS_DIR}/{col}_encoder.pkl'
    if os.path.exists(path) and not FORCE_RETRAIN:
        le = joblib.load(path)
        df[col] = le.transform(df[col].astype(str))
        print(f"   🔄 Loaded encoder for '{col}'")
    else:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col].astype(str))
        joblib.dump(le, path)
        print(f"   ✅ Saved encoder for '{col}'")

# Machine ID
path = f'{ENCODERS_DIR}/machine_id_encoder.pkl'
if os.path.exists(path) and not FORCE_RETRAIN:
    le_machine = joblib.load(path)
    df['machine_id_encoded'] = le_machine.transform(df['machine_id'])
else:
    le_machine = LabelEncoder()
    df['machine_id_encoded'] = le_machine.fit_transform(df['machine_id'])
    joblib.dump(le_machine, path)
    print("   ✅ Saved machine_id encoder")

# -----------------------------
# Step 4: Calculate Time to Failure (TTF)
# -----------------------------
print("⏳ Calculating 'Time to Failure' for regression targets...")

def add_ttf(group):
    failure_times = group[group['failure'] == 1].index.tolist()
    if not failure_times:
        group['ttf'] = 60
        return group
    ttf_vals = []
    for idx in group.index:
        future = [i for i in failure_times if i >= idx]
        if future:
            next_fail = future[0]
            mins = (group.loc[next_fail, 'timestamp'] - group.loc[idx, 'timestamp']).seconds // 60
            ttf_vals.append(mins if group.loc[idx, 'failure'] == 0 else 0)
        else:
            ttf_vals.append(60)
    group['ttf'] = ttf_vals
    return group

df = df.groupby('machine_id', group_keys=False).apply(add_ttf)
df['ttf'] = df['ttf'].fillna(60)

# -----------------------------
# Step 5: Train or Load Models
# -----------------------------
X = df[features].copy()

# Check if models exist
cls_models_exist = all(os.path.exists(f'{MODELS_DIR}/{ft}_classifier.pkl') for ft in failure_types)
reg_models_exist = all(os.path.exists(f'{MODELS_DIR}/{ft}_regressor.pkl') for ft in failure_types)

if (cls_models_exist and reg_models_exist) and not FORCE_RETRAIN:
    print("🟢 Models found. Skipping training. Using saved models.\n")
else:
    print("🟡 Training classification and regression models...\n")

    for failure in failure_types:
        print(f"🤖 Training models for '{failure}'...")

        # Classification: Will it fail in next 3 steps?
        y_cls = pd.Series(0, index=df.index)
        for idx in df.index:
            end_idx = min(idx + 3, len(df))
            window = df.iloc[idx:end_idx]
            if (window['hardware_failure_type'] == failure).any():
                y_cls.iloc[idx] = 1

        # Regression: Minutes until failure
        y_reg = df['ttf'].copy()

        # Time-based split
        split_idx = int(0.7 * len(df))
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_cls_train = y_cls.iloc[:split_idx]
        y_reg_train = y_reg.iloc[:split_idx]

        # Classifier
        if y_cls_train.nunique() >= 2:
            clf = RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42)
            clf.fit(X_train, y_cls_train)
            joblib.dump(clf, f'{MODELS_DIR}/{failure}_classifier.pkl')
        else:
            print(f"   ⚠️  Skipping classifier for '{failure}' (single class)")

        # Regressor
        reg = RandomForestRegressor(n_estimators=100, random_state=42)
        reg.fit(X_train, y_reg_train)
        joblib.dump(reg, f'{MODELS_DIR}/{failure}_regressor.pkl')

    print("✅ All models trained and saved.\n")

# -----------------------------
# Step 6: Predict on Latest Data
# -----------------------------
print("🔮 Generating user-friendly failure forecast...\n")

# Reload original for indicators
original_df = pd.read_csv(DATA_FILE)
original_df['timestamp'] = pd.to_datetime(original_df['timestamp'])
latest_full = original_df.groupby('machine_id').last().reset_index()
latest_encoded = df.groupby('machine_id').last().reset_index()
X_latest = latest_encoded[features].copy()

# Icons and risk levels
icons = {
    'hard_disk': '🔧',
    'fan': '🌀',
    'power_supply': '⚡',
    'network_card': '📡',
    'motherboard': '🧠'
}

def format_risk(confidence):
    if confidence > 0.7:
        return "🔴 High"
    elif confidence > 0.4:
        return "🟡 Medium"
    else:
        return "🟢 Low"

def format_ttf(minutes):
    if minutes < 1:
        return "⚠️ Imminent"
    elif minutes < 5:
        return f"⏱️ {minutes:.0f} min"
    elif minutes < 60:
        return f"⏱️ {minutes:.0f} min"
    else:
        return "✅ Stable"

# Header
print("=" * 80)
print("           🚨 PREDICTIVE MAINTENANCE DASHBOARD")
print("=" * 80)
print(f"{'Machine':<10} {'Failure Type':<15} {'Risk Level':<12} {'Likelihood':<12} {'Time to Fail':<14} {'Issues'}")
print("-" * 80)

for idx, row in X_latest.iterrows():
    machine_id = latest_full.iloc[idx]['machine_id']

    # Diagnose issues
    temp = latest_full.iloc[idx]['temperature']
    vib = latest_full.iloc[idx]['vibration']
    fan = latest_full.iloc[idx]['fan_speed']
    curr = latest_full.iloc[idx]['current']
    issues = []
    if temp > 80: issues.append("🔥 High Temp")
    if vib > 0.2: issues.append("📳 High Vib")
    if fan < 1200: issues.append("🌀 Low Fan")
    if curr > 12.0: issues.append("⚡ High Current")

    risks = {}
    ttf_preds = {}
    X_input = row[features].values.reshape(1, -1)

    for name in failure_types:
        cls_path = f'{MODELS_DIR}/{name}_classifier.pkl'
        reg_path = f'{MODELS_DIR}/{name}_regressor.pkl'

        # Classification
        if os.path.exists(cls_path):
            clf = joblib.load(cls_path)
            proba = clf.predict_proba(X_input)
            risk = proba[0, 1] if proba.shape[1] > 1 else 0.0
        else:
            risk = 0.0
        risks[name] = risk

        # Regression
        if os.path.exists(reg_path):
            reg = joblib.load(reg_path)
            ttf = max(reg.predict(X_input)[0], 0)
        else:
            ttf = 60
        ttf_preds[name] = ttf

    # Find highest risk
    if not risks or all(v == 0 for v in risks.values()):
        top_failure = "None"
        confidence = 0.0
        ttf_display = "✅ Stable"
        icon = "✅"
        risk_level = "🟢 Low"
        issue_text = "All systems nominal"
    else:
        top_failure = max(risks, key=risks.get)
        confidence = risks[top_failure]
        ttf_display = format_ttf(ttf_preds[top_failure])
        icon = icons.get(top_failure, "⚠️")
        risk_level = format_risk(confidence)
        issue_text = ", ".join(issues) if issues else "Monitoring"

    print(f"{machine_id:<10} "
          f"{icon} {top_failure.title():<13} "
          f"{risk_level:<12} "
          f"{confidence:6.1%}    "
          f"{ttf_display:<14} "
          f"{issue_text}")

print("-" * 80)
print("✅ Forecast generated. Use this to prioritize maintenance actions.")