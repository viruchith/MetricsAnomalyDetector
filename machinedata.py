import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Read existing data
df = pd.read_csv('machinedata copy.csv')

# Get the last timestamp and machine IDs from existing data
last_timestamp = pd.to_datetime(df['timestamp'].max())
existing_machines = df['machine_id'].unique()
max_machine_id = max(existing_machines)

# Define new failure types and scenarios
failure_types = ['hard_disk', 'power_supply', 'fan', 'network_card', 'motherboard', 'cpu', 'memory', 'thermal']
status_values = ['normal', 'warning', 'failed']

# Generate new machine data
new_machines = range(max_machine_id + 1, max_machine_id + 6)  # Adding 5 new machines
time_duration = 30  # 30 minutes of data

new_data = []
start_time = last_timestamp + timedelta(minutes=1)

for machine_id in new_machines:
    base_temp = np.random.uniform(65, 75)
    base_vibration = np.random.uniform(0.05, 0.12)
    base_pressure = np.random.uniform(37, 42)
    base_current = np.random.uniform(9, 11)
    base_fan_speed = np.random.choice([1600, 1700, 1800, 1900, 2000, 2100])
    
    for minute in range(time_duration):
        timestamp = start_time + timedelta(minutes=minute)
        
        # Randomly inject failures (20% chance)
        failure_occurred = np.random.random() < 0.2
        
        if failure_occurred:
            failure_type = np.random.choice(failure_types)
            
            # Simulate failure effects on metrics
            if failure_type in ['cpu', 'thermal']:
                temperature = base_temp + np.random.uniform(15, 25)
                vibration = base_vibration + np.random.uniform(0.15, 0.3)
                pressure = base_pressure + np.random.uniform(2, 5)
                current = base_current + np.random.uniform(2, 5)
            elif failure_type == 'fan':
                temperature = base_temp + np.random.uniform(18, 28)
                fan_speed = np.random.choice([400, 500, 600, 700, 800])
                vibration = base_vibration + np.random.uniform(0.2, 0.35)
                pressure = base_pressure + np.random.uniform(3, 6)
                current = base_current + np.random.uniform(3, 6)
            elif failure_type == 'power_supply':
                temperature = base_temp + np.random.uniform(20, 30)
                vibration = base_vibration + np.random.uniform(0.25, 0.4)
                pressure = base_pressure + np.random.uniform(4, 7)
                current = base_current + np.random.uniform(4, 7)
                fan_speed = base_fan_speed
            elif failure_type == 'memory':
                temperature = base_temp + np.random.uniform(8, 15)
                vibration = base_vibration + np.random.uniform(0.1, 0.2)
                pressure = base_pressure + np.random.uniform(1, 3)
                current = base_current + np.random.uniform(1, 3)
                fan_speed = base_fan_speed
            else:
                temperature = base_temp + np.random.uniform(10, 20)
                vibration = base_vibration + np.random.uniform(0.12, 0.25)
                pressure = base_pressure + np.random.uniform(1.5, 4)
                current = base_current + np.random.uniform(1.5, 4)
                fan_speed = base_fan_speed
            
            # Set component statuses based on failure type
            hard_disk_status = 'failed' if failure_type == 'hard_disk' else 'normal'
            power_supply_status = 'failed' if failure_type == 'power_supply' else ('warning' if failure_type in ['cpu', 'thermal'] else 'normal')
            network_card_status = 'failed' if failure_type == 'network_card' else 'normal'
            motherboard_status = 'failed' if failure_type == 'motherboard' else ('warning' if failure_type in ['memory', 'cpu'] else 'normal')
            
            failure_flag = 1
            hardware_failure_type = failure_type
            
        else:
            # Normal operation with small variations
            temperature = base_temp + np.random.uniform(-2, 3)
            vibration = base_vibration + np.random.uniform(-0.02, 0.03)
            pressure = base_pressure + np.random.uniform(-1, 1.5)
            current = base_current + np.random.uniform(-0.5, 0.8)
            fan_speed = base_fan_speed + np.random.choice([-100, -50, 0, 50, 100])
            
            hard_disk_status = 'normal'
            power_supply_status = 'normal'
            network_card_status = 'normal'
            motherboard_status = 'normal'
            
            failure_flag = 0
            hardware_failure_type = ''
        
        new_data.append({
            'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'machine_id': machine_id,
            'temperature': round(temperature, 1),
            'vibration': round(vibration, 2),
            'pressure': round(pressure, 1),
            'current': round(current, 1),
            'hard_disk_status': hard_disk_status,
            'fan_speed': int(fan_speed),
            'power_supply_status': power_supply_status,
            'network_card_status': network_card_status,
            'motherboard_status': motherboard_status,
            'hardware_failure_type': hardware_failure_type,
            'failure': failure_flag
        })

# Create DataFrame from new data
new_df = pd.DataFrame(new_data)

# Append to existing data
extended_df = pd.concat([df, new_df], ignore_index=True)

# Save back to the same file
extended_df.to_csv('machinedata copy.csv', index=False)

print(f"Dataset extended with {len(new_data)} new records")
print(f"Added machines: {list(new_machines)}")
print(f"New failure types included: {failure_types}")
print(f"Total records: {len(extended_df)}")
