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
import sys
from io import StringIO
import warnings

# Set console encoding for Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Import email alerts module
try:
    from email_alerts import send_maintenance_alert, log_email_alert
    EMAIL_ALERTS_ENABLED = True
except ImportError:
    EMAIL_ALERTS_ENABLED = False
    print("⚠️ Email alerts module not available. Continuing without email notifications.")

warnings.filterwarnings('ignore')

# -----------------------------
# Helper Functions for Incremental Learning
# -----------------------------
def get_training_files_list():
    """Get list of CSV files to process in order"""
    import glob
    csv_files = glob.glob("input*.csv")
    if not csv_files:
        csv_files = [DATA_FILE]  # Fallback to default
    return sorted(csv_files)

def save_training_history(file_name, num_samples, timestamp):
    """Save training history for tracking"""
    history_file = f"{TRAINING_HISTORY_DIR}/training_log.csv"
    log_entry = pd.DataFrame({
        'file': [file_name],
        'samples': [num_samples],
        'timestamp': [timestamp],
        'training_time': [pd.Timestamp.now()]
    })
    
    if os.path.exists(history_file):
        existing = pd.read_csv(history_file)
        log_entry = pd.concat([existing, log_entry], ignore_index=True)
    
    log_entry.to_csv(history_file, index=False)
    print(f"   📝 Logged training: {file_name} ({num_samples} samples)")

def add_ttf(group):
    """Calculate Time to Failure for each record in a machine group"""
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

def load_and_preprocess_data(file_path):
    """Load and preprocess data with consistent feature engineering"""
    print(f"🚀 Loading data from: {file_path}")
    
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(file_path, encoding='latin-1')
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding='cp1252')
    
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values(['machine_id', 'timestamp']).reset_index(drop=True)
    
    print(f"📊 Loaded {len(df)} sensor readings from {df['machine_id'].nunique()} machines.")
    
    # Feature Engineering
    print("⚙️ Engineering features...")
    df['hour'] = df['timestamp'].dt.hour
    df['minute'] = df['timestamp'].dt.minute

    for col in ['temperature', 'vibration', 'current']:
        df[f'{col}_rolling_avg'] = df.groupby('machine_id')[col].transform(lambda x: x.rolling(3, 1).mean())

    df['temp_fan_ratio'] = df['temperature'] / (df['fan_speed'] / 100)
    df['current_pressure_ratio'] = df['current'] / df['pressure']
    df['vibration_temp_interaction'] = df['vibration'] * df['temperature']
    df['hardware_failure_type'] = df['hardware_failure_type'].fillna('none')
    
    return df

def train_incremental_models(df_new, existing_models=None):
    """Train models incrementally or from scratch"""
    X = df_new[features].copy()
    
    # Calculate TTF for new data
    print("⏳ Calculating 'Time to Failure' for new data...")
    df_processed = df_new.groupby('machine_id', group_keys=False).apply(add_ttf)
    df_processed['ttf'] = df_processed['ttf'].fillna(60)
    
    # Train models for each failure type
    for failure in failure_types:
        print(f"🤖 Training models for '{failure}'...")

        # Classification: Will it fail in next 3 steps?
        y_cls = pd.Series(0, index=df_processed.index)
        for idx in df_processed.index:
            end_idx = min(idx + 3, len(df_processed))
            window = df_processed.iloc[idx:end_idx]
            if (window['hardware_failure_type'] == failure).any():
                y_cls.iloc[idx] = 1

        # Regression: Minutes until failure
        y_reg = df_processed['ttf'].copy()

        # For incremental learning, use all data (no train/test split)
        # In production, you might want to keep a validation set
        X_train = X
        y_cls_train = y_cls
        y_reg_train = y_reg

        # Classifier
        cls_path = f'{MODELS_DIR}/{failure}_classifier.pkl'
        if y_cls_train.nunique() >= 2:
            if INCREMENTAL_MODE and os.path.exists(cls_path) and not FORCE_RETRAIN:
                # Load existing model and retrain (partial_fit for some models)
                # Note: RandomForest doesn't support partial_fit, so we'll retrain
                print(f"   🔄 Updating existing classifier for '{failure}'")
                clf = joblib.load(cls_path)
                # For RandomForest, we need to retrain completely
                # In practice, you might want to use models that support incremental learning
                clf = RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42)
            else:
                clf = RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42)
            
            clf.fit(X_train, y_cls_train)
            joblib.dump(clf, cls_path)
        else:
            print(f"   ⚠️  Skipping classifier for '{failure}' (single class)")

        # Regressor
        reg_path = f'{MODELS_DIR}/{failure}_regressor.pkl'
        if INCREMENTAL_MODE and os.path.exists(reg_path) and not FORCE_RETRAIN:
            print(f"   🔄 Updating existing regressor for '{failure}'")
            reg = joblib.load(reg_path)
            # For RandomForest, we need to retrain completely
            reg = RandomForestRegressor(n_estimators=100, random_state=42)
        else:
            reg = RandomForestRegressor(n_estimators=100, random_state=42)
        
        reg.fit(X_train, y_reg_train)
        joblib.dump(reg, reg_path)

    return df_processed

# -----------------------------
# Configuration
# -----------------------------
DATA_FILE = 'machinedata copy.csv'  # Default file - can be overridden
MODELS_DIR = 'models'
ENCODERS_DIR = 'encoders'
TRAINING_HISTORY_DIR = 'training_history'
FORCE_RETRAIN = False  # Set to True to retrain from scratch
INCREMENTAL_MODE = True  # Set to True for incremental learning

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(ENCODERS_DIR, exist_ok=True)
os.makedirs(TRAINING_HISTORY_DIR, exist_ok=True)

# -----------------------------
# Main Execution Flow
# -----------------------------

# Get list of training files
training_files = get_training_files_list()
print(f"🎯 Found {len(training_files)} CSV files to process: {training_files}\n")

# Define failure types and features (moved here for clarity)
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

# Process each file incrementally
all_processed_data = []

for file_idx, csv_file in enumerate(training_files):
    print(f"\n{'='*60}")
    print(f"📁 PROCESSING FILE {file_idx + 1}/{len(training_files)}: {csv_file}")
    print(f"{'='*60}")
    
    # Load and preprocess current file
    df = load_and_preprocess_data(csv_file)
    
    # Encode categorical features (reuse existing encoders or create new ones)
    print("🔐 Encoding categorical features...")
    for col in status_cols:
        path = f'{ENCODERS_DIR}/{col}_encoder.pkl'
        if os.path.exists(path):
            le = joblib.load(path)
            # Handle new categories that weren't in training
            try:
                df[col] = le.transform(df[col].astype(str))
                print(f"   🔄 Used existing encoder for '{col}'")
            except ValueError as e:
                # New categories found - need to update encoder
                print(f"   🆕 New categories found in '{col}', updating encoder...")
                unique_vals = list(le.classes_) + [x for x in df[col].astype(str).unique() if x not in le.classes_]
                le.classes_ = np.array(unique_vals)
                df[col] = le.transform(df[col].astype(str))
                joblib.dump(le, path)
        else:
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col].astype(str))
            joblib.dump(le, path)
            print(f"   ✅ Created new encoder for '{col}'")

    # Machine ID encoding
    path = f'{ENCODERS_DIR}/machine_id_encoder.pkl'
    if os.path.exists(path):
        le_machine = joblib.load(path)
        try:
            df['machine_id_encoded'] = le_machine.transform(df['machine_id'])
            print("   🔄 Used existing machine_id encoder")
        except ValueError:
            # New machine IDs found
            print("   🆕 New machine IDs found, updating encoder...")
            unique_vals = list(le_machine.classes_) + [x for x in df['machine_id'].unique() if x not in le_machine.classes_]
            le_machine.classes_ = np.array(unique_vals)
            df['machine_id_encoded'] = le_machine.transform(df['machine_id'])
            joblib.dump(le_machine, path)
    else:
        le_machine = LabelEncoder()
        df['machine_id_encoded'] = le_machine.fit_transform(df['machine_id'])
        joblib.dump(le_machine, path)
        print("   ✅ Created new machine_id encoder")
    
    # Train models incrementally
    if file_idx == 0 or FORCE_RETRAIN:
        print(f"\n� Training initial models with {csv_file}...")
    else:
        print(f"\n🔄 Updating models with new data from {csv_file}...")
    
    df_processed = train_incremental_models(df)
    all_processed_data.append(df_processed)
    
    # Save training history
    save_training_history(csv_file, len(df), df['timestamp'].max())
    
    print(f"✅ Completed processing {csv_file}")

# Combine all data for final predictions
print(f"\n{'='*60}")
print("🔮 GENERATING FINAL PREDICTIONS")
print(f"{'='*60}")

# Use the most recent data for predictions
latest_data = all_processed_data[-1] if all_processed_data else df_processed

# -----------------------------
# Generate Predictions
# -----------------------------
print("🔮 Generating user-friendly failure forecast...\n")

# Get latest readings for each machine from the most recent dataset
latest_encoded = latest_data.groupby('machine_id').last().reset_index()
X_latest = latest_encoded[features].copy()

# Also get original values for diagnostics
latest_original = latest_data.groupby('machine_id').last().reset_index()

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
print(f"🗂️  Trained on {len(training_files)} file(s): {', '.join(training_files)}")
print(f"📊 Total machines monitored: {latest_data['machine_id'].nunique()}")
print(f"📅 Latest data timestamp: {latest_data['timestamp'].max()}")
print("=" * 80)
print(f"{'Machine':<10} {'Failure Type':<15} {'Risk Level':<12} {'Likelihood':<12} {'Time to Fail':<14} {'Issues'}")
print("-" * 80)

# Collect alert data for email notifications
alert_data = []
training_summary = {
    'files_count': len(training_files),
    'total_machines': latest_data['machine_id'].nunique(),
    'latest_timestamp': latest_data['timestamp'].max(),
    'total_samples': sum(len(all_processed_data[i]) for i in range(len(all_processed_data)))
}

for idx, row in X_latest.iterrows():
    machine_id = latest_original.iloc[idx]['machine_id']

    # Diagnose issues
    temp = latest_original.iloc[idx]['temperature']
    vib = latest_original.iloc[idx]['vibration']
    fan = latest_original.iloc[idx]['fan_speed']
    curr = latest_original.iloc[idx]['current']
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
    
    # Collect alert data for email notifications
    if confidence > 0.4:  # Medium or High risk
        risk_level_text = "High" if confidence > 0.7 else "Medium"
        alert_data.append({
            'machine_id': machine_id,
            'failure_type': top_failure.title(),
            'icon': icon,
            'risk_level': risk_level_text,
            'likelihood': confidence,
            'time_to_fail': ttf_display,
            'issues': issue_text
        })

print("-" * 80)
print("✅ Forecast generated. Use this to prioritize maintenance actions.")

# Send email alerts for medium and high risk failures
if EMAIL_ALERTS_ENABLED and alert_data:
    print(f"\n📧 Sending email alerts for {len(alert_data)} critical issues...")
    success = send_maintenance_alert(alert_data, training_summary)
    log_email_alert(alert_data, success)
elif alert_data:
    print(f"\n⚠️ {len(alert_data)} critical alerts detected but email module not available.")
    print("📧 To enable email alerts, ensure email_alerts.py is properly configured.")
else:
    print("\n✅ No critical alerts to send - all systems operating normally.")