import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def generate_sample_data(num_rows=100):
    """Generate sample system metrics data"""
    
    # Start time
    start_time = datetime.now() - timedelta(minutes=num_rows)
    
    # Generate timestamps
    timestamps = [start_time + timedelta(minutes=i) for i in range(num_rows)]
    
    # Generate normal baseline data
    cpu_percent = []
    memory_percent = []
    disk_read_mb = []
    disk_write_mb = []
    network_sent_mb = []
    network_recv_mb = []
    
    for i in range(num_rows):
        # Normal system behavior (mostly low usage)
        if random.random() < 0.95:  # 95% normal behavior
            cpu = random.uniform(5, 30)
            memory = random.uniform(20, 50)
            disk_read = random.uniform(0, 5)
            disk_write = random.uniform(0, 3)
            net_sent = random.uniform(0, 2)
            net_recv = random.uniform(0, 2)
        else:  # 5% anomalous behavior
            cpu = random.uniform(70, 95)
            memory = random.uniform(70, 90)
            disk_read = random.uniform(50, 200)
            disk_write = random.uniform(20, 100)
            net_sent = random.uniform(50, 300)
            net_recv = random.uniform(10, 50)
        
        cpu_percent.append(round(cpu, 2))
        memory_percent.append(round(memory, 2))
        disk_read_mb.append(round(disk_read, 2))
        disk_write_mb.append(round(disk_write, 2))
        network_sent_mb.append(round(net_sent, 2))
        network_recv_mb.append(round(net_recv, 2))
    
    # Create DataFrame
    df = pd.DataFrame({
        'timestamp': timestamps,
        'cpu_percent': cpu_percent,
        'cpu_frequency': [2400.0] * num_rows,  # Constant CPU frequency
        'memory_percent': memory_percent,
        'memory_available_gb': [round(16 - (mem/100)*16, 2) for mem in memory_percent],  # Assuming 16GB total RAM
        'disk_read_mb': disk_read_mb,
        'disk_write_mb': disk_write_mb,
        'network_sent_mb': network_sent_mb,
        'network_recv_mb': network_recv_mb
    })
    
    return df

def add_specific_anomalies(df):
    """Add specific, obvious anomalies to the dataset"""
    
    # Add a CPU spike anomaly at row 25
    df.loc[25, 'cpu_percent'] = 92.5
    df.loc[25, 'memory_percent'] = 85.2
    df.loc[25, 'disk_read_mb'] = 156.7
    df.loc[25, 'network_sent_mb'] = 234.8
    
    # Add a memory leak pattern from rows 40-45
    for i in range(40, 46):
        df.loc[i, 'memory_percent'] = 65.0 + (i - 40) * 5
        df.loc[i, 'disk_write_mb'] = 45.2 + (i - 40) * 8
    
    # Add a network spike at row 60
    df.loc[60, 'network_sent_mb'] = 287.3
    df.loc[60, 'network_recv_mb'] = 45.6
    df.loc[60, 'cpu_percent'] = 78.9
    
    # Add disk intensive operation at row 80
    df.loc[80, 'disk_read_mb'] = 187.5
    df.loc[80, 'disk_write_mb'] = 98.7
    df.loc[80, 'cpu_percent'] = 82.1
    
    return df

# Generate sample data
print("Generating sample data...")
df = generate_sample_data(2000)
df = add_specific_anomalies(df)

# Save to CSV
df.to_csv('sample_metrics.csv', index=False)
print("Sample data saved to 'sample_metrics.csv'")

# Display first 10 rows
print("\nFirst 10 rows of generated data:")
print(df.head(10))

# Show some statistics
print(f"\nDataset Info:")
print(f"Total rows: {len(df)}")
print(f"Anomalies added at specific rows: 25, 40-45, 60, 80")
print(f"Columns: {list(df.columns)}")

# Show anomalies summary
print(f"\nSample of anomalies that should be detected:")
print("Row 25: High CPU/Memory/Network spike")
print("Rows 40-45: Gradual memory increase (simulating memory leak)")
print("Row 60: Network traffic spike")
print("Row 80: Disk intensive operation")