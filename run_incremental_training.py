#!/usr/bin/env python3
"""
🔄 Incremental Training Script for Predictive Maintenance

This script demonstrates how to train models incrementally with multiple CSV files.

Usage:
1. Place your CSV files as: input1.csv, input2.csv, input3.csv, etc.
2. Run this script to train models incrementally
3. Models will be saved and reused across runs

File naming convention:
- input1.csv: First training dataset
- input2.csv: Second training dataset (will update models trained on input1.csv)
- input3.csv: Third training dataset (will update models trained on input1.csv + input2.csv)
- And so on...

Configuration options:
- FORCE_RETRAIN = False: Use existing models and update incrementally
- FORCE_RETRAIN = True: Start training from scratch
- INCREMENTAL_MODE = True: Enable incremental learning
"""

import os
import sys
import glob
import subprocess
from datetime import datetime

def setup_training_files():
    """Setup example input files if they don't exist"""
    csv_files = glob.glob("input*.csv")
    
    if not csv_files:
        print("⚠️  No input*.csv files found!")
        print("📝 Please create your CSV files with names: input1.csv, input2.csv, etc.")
        print("💡 Each file should have the same structure as your original machinedata.csv")
        print("\nFor testing, you can copy your existing data:")
        print("   copy machinedata.csv input1.csv")
        print("   copy \"machinedata copy.csv\" input2.csv")
        return False
    
    print(f"✅ Found {len(csv_files)} input files: {sorted(csv_files)}")
    return True

def run_incremental_training():
    """Run the incremental training process"""
    print("🚀 Starting Incremental Training Process")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    if not setup_training_files():
        return False
    
    # Import and run the main training script
    try:
        print("🔄 Running enhanced_failure_prediction.py...")
        import subprocess
        result = subprocess.run([sys.executable, 'enhanced_failure_prediction.py'], 
                              capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            print(result.stdout)
            print("\n✅ Incremental training completed successfully!")
            return True
        else:
            print(f"\n❌ Error during training: {result.stderr}")
            return False
    except Exception as e:
        print(f"\n❌ Error during training: {str(e)}")
        return False

def show_training_history():
    """Display training history if available"""
    history_file = "training_history/training_log.csv"
    if os.path.exists(history_file):
        import pandas as pd
        print("\n📊 Training History:")
        print("-" * 40)
        history = pd.read_csv(history_file)
        for _, row in history.iterrows():
            print(f"📁 {row['file']}: {row['samples']} samples at {row['training_time']}")
    else:
        print("\n📊 No training history found yet.")

def main():
    """Main execution function"""
    print("🛠️  INCREMENTAL PREDICTIVE MAINTENANCE TRAINER")
    print("=" * 60)
    
    # Show current configuration
    print("⚙️  Configuration:")
    print("   📂 Models saved to: ./models/")
    print("   🔐 Encoders saved to: ./encoders/")
    print("   📝 Training history: ./training_history/")
    print()
    
    # Check if this is first run or incremental
    models_exist = os.path.exists("models") and len(glob.glob("models/*.pkl")) > 0
    
    if models_exist:
        print("🔄 Existing models found - will perform incremental training")
    else:
        print("🆕 No existing models found - will train from scratch")
    
    print()
    
    # Run training
    success = run_incremental_training()
    
    # Show results
    if success:
        show_training_history()
        print("\n🎯 Next Steps:")
        print("   1. Add more input files (input3.csv, input4.csv, etc.)")
        print("   2. Run this script again to update models incrementally")
        print("   3. Use the trained models for real-time predictions")
    
    return success

if __name__ == "__main__":
    main()
