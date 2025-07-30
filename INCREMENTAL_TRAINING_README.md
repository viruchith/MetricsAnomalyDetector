# 🔄 Incremental Predictive Maintenance System

## Overview
This enhanced system allows you to train machine learning models incrementally using multiple CSV files. Instead of retraining from scratch each time, the system updates existing models with new data.

## How It Works

### 1. **File-based Incremental Training**
- Place your CSV files as: `input1.csv`, `input2.csv`, `input3.csv`, etc.
- The system processes files in alphabetical order
- Models trained on `input1.csv` are updated with data from `input2.csv`, then `input3.csv`, and so on

### 2. **Model Persistence**
- Trained models are saved in `./models/` directory
- Encoders for categorical data are saved in `./encoders/` directory
- Training history is logged in `./training_history/` directory

### 3. **Smart Encoding**
- Handles new machine IDs and component statuses automatically
- Updates encoders when new categories are encountered
- Maintains consistency across different datasets

## Usage

### Quick Start
```bash
# Method 1: Use the incremental training script
python run_incremental_training.py

# Method 2: Run the main script directly
python enhanced_failure_prediction.py
```

### Setting Up Your Data
1. **Prepare your CSV files:**
   ```
   input1.csv  # First dataset (initial training)
   input2.csv  # Second dataset (incremental update)
   input3.csv  # Third dataset (incremental update)
   ...
   ```

2. **CSV Structure:** Each file should have the same columns as your original data:
   ```
   machine_id, timestamp, temperature, vibration, pressure, current,
   hard_disk_status, fan_speed, power_supply_status, network_card_status,
   motherboard_status, hardware_failure_type, failure
   ```

### Configuration Options

In `enhanced_failure_prediction.py`, you can modify:

```python
# Configuration
DATA_FILE = 'machinedata copy.csv'     # Fallback if no input*.csv found
MODELS_DIR = 'models'                  # Where to save trained models
ENCODERS_DIR = 'encoders'              # Where to save encoders
TRAINING_HISTORY_DIR = 'training_history'  # Training logs
FORCE_RETRAIN = False                  # Set True to retrain from scratch
INCREMENTAL_MODE = True                # Enable incremental learning
```

## Workflow Example

### Day 1: Initial Training
```bash
# Place your first dataset
input1.csv  # Contains data from machines A, B, C

# Run training
python run_incremental_training.py
# → Models trained on machines A, B, C
```

### Day 2: Add New Data
```bash
# Add second dataset
input2.csv  # Contains new data from machines A, B, C, D

# Run incremental training
python run_incremental_training.py
# → Models updated with new data
# → Now handles machine D automatically
```

### Day 3: Continue Growing
```bash
# Add third dataset
input3.csv  # Contains data from machines A-F

# Run incremental training
python run_incremental_training.py
# → Models further updated
# → Now handles machines E and F
```

## Features

### ✅ **What's New**
- **Incremental Learning**: Update models without starting from scratch
- **Multi-file Processing**: Automatically processes `input1.csv`, `input2.csv`, etc.
- **Smart Encoding**: Handles new machine IDs and component types
- **Training History**: Logs what files were processed and when
- **Flexible Configuration**: Easy to customize for different scenarios

### 🔧 **Model Types** (unchanged)
For each component (hard_disk, fan, power_supply, network_card, motherboard):
- **Classifier**: Predicts failure probability in next 3 time steps
- **Regressor**: Estimates time until failure (in minutes)

### 📊 **Output Dashboard** (enhanced)
```
🚨 PREDICTIVE MAINTENANCE DASHBOARD
============================================================
🗂️  Trained on 3 file(s): input1.csv, input2.csv, input3.csv
📊 Total machines monitored: 15
📅 Latest data timestamp: 2025-07-30 14:30:00
============================================================
Machine    Failure Type    Risk Level   Likelihood   Time to Fail   Issues
--------------------------------------------------------------------
M001       🔧 Hard_disk    🔴 High       85.2%       ⏱️ 12 min      🔥 High Temp
M002       🌀 Fan          🟡 Medium     45.1%       ⏱️ 45 min      📳 High Vib
...
```

## File Structure
```
📁 Project Directory
├── 📄 enhanced_failure_prediction.py    # Main training/prediction script
├── 📄 run_incremental_training.py       # Helper script for incremental training
├── 📄 input1.csv                        # First training dataset
├── 📄 input2.csv                        # Second training dataset
├── 📄 input3.csv                        # Third training dataset
├── 📁 models/                           # Saved ML models
│   ├── hard_disk_classifier.pkl
│   ├── hard_disk_regressor.pkl
│   └── ...
├── 📁 encoders/                         # Saved encoders
│   ├── machine_id_encoder.pkl
│   ├── hard_disk_status_encoder.pkl
│   └── ...
└── 📁 training_history/                 # Training logs
    └── training_log.csv
```

## Best Practices

### 📋 **Data Management**
- Keep consistent column names across all CSV files
- Ensure timestamps are properly formatted
- Include both normal operations and failure events in each dataset

### ⚙️ **Model Updates**
- Run incremental training regularly (daily/weekly)
- Monitor training history to track data growth
- Set `FORCE_RETRAIN = True` occasionally for full retraining

### 🔍 **Monitoring**
- Check the dashboard output for prediction quality
- Review training logs in `training_history/training_log.csv`
- Monitor model performance on new data

## Troubleshooting

### ❌ **Common Issues**

**No input files found:**
```bash
⚠️  No input*.csv files found!
📝 Please create your CSV files with names: input1.csv, input2.csv, etc.
```
**Solution:** Create files named `input1.csv`, `input2.csv`, etc.

**New categories in data:**
```bash
🆕 New categories found in 'machine_id', updating encoder...
```
**Solution:** This is normal - the system handles it automatically.

**Model file errors:**
```bash
❌ Error loading model: file not found
```
**Solution:** Set `FORCE_RETRAIN = True` to rebuild models.

## Technical Notes

### 🏗️ **Architecture**
- Uses RandomForest models (both Classifier and Regressor)
- LabelEncoder for categorical variables with automatic expansion
- Time-series aware feature engineering
- Persistent model storage with joblib

### ⚡ **Performance**
- Models are saved/loaded to avoid retraining overhead
- Encoders are reused and expanded as needed
- Training history tracks processing efficiency

### 🔬 **Limitations**
- RandomForest doesn't support true incremental learning (models are retrained)
- For true online learning, consider using SGDClassifier/SGDRegressor
- Memory usage scales with total dataset size

---

## Next Steps
1. **Start with your first dataset:** `input1.csv`
2. **Run initial training:** `python run_incremental_training.py`
3. **Add new data regularly:** `input2.csv`, `input3.csv`, etc.
4. **Monitor and maintain:** Check dashboard and training history

Happy Predicting! 🚀
