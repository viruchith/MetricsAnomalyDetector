import json
import numpy as np
import pandas as pd
from collections import deque
import time
from datetime import datetime
import logging
import pika

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("vm_anomalies.log"),
        logging.StreamHandler()
    ]
)

class VMAnomalyDetector:
    def __init__(self, window_size=100, z_score_threshold=3.0):
        """
        Initialize the anomaly detector.
        
        Args:
            window_size: Number of data points to keep in history
            z_score_threshold: Z-score threshold for anomaly detection
        """
        self.window_size = window_size
        self.z_score_threshold = z_score_threshold
        
        # Historical data storage
        self.history = deque(maxlen=window_size)
        
        # Define which metrics to monitor
        self.numeric_metrics = [
            'cpu_usage', 'memory_usage', 'network_traffic', 
            'power_consumption', 'num_executed_instructions',
            'execution_time', 'energy_efficiency'
        ]
        
        # Define normal ranges for each metric (can be adjusted based on domain knowledge)
        self.normal_ranges = {
            'cpu_usage': (0, 90),            # Percent
            'memory_usage': (0, 85),         # Percent
            'network_traffic': (0, 1000),    # Arbitrary units
            'power_consumption': (0, 500),   # Watts
            'execution_time': (0, 200),      # Seconds
            'energy_efficiency': (0, 1)      # Normalized value
        }
        
        # Critical thresholds that indicate immediate problems
        self.critical_thresholds = {
            'cpu_usage': 95,                # Percent
            'memory_usage': 95,             # Percent
            'power_consumption': 600,       # Watts
            'execution_time': 300           # Seconds
        }
        
        # Task failure indicators
        self.failure_indicators = {
            'task_status': ['failed', 'timeout', 'error']
        }

    def add_data_point(self, data_point):
        """Add a new data point to the history."""
        self.history.append(data_point)
        
    def detect_anomalies(self, data_point):
        """
        Detect anomalies in the given data point.
        
        Args:
            data_point: Dict containing VM metrics
            
        Returns:
            Dict with anomaly results
        """
        anomalies = {}
        
        # 1. Check for direct failure indicators
        for indicator, failure_values in self.failure_indicators.items():
            if indicator in data_point and data_point[indicator] in failure_values:
                anomalies[indicator] = {
                    'is_anomaly': True,
                    'severity': 'critical',
                    'message': f"Task failure detected: {indicator}={data_point[indicator]}"
                }
        
        # 2. Check for critical threshold violations
        for metric, threshold in self.critical_thresholds.items():
            if metric in data_point:
                # Convert to float in case it's a string from CSV
                try:
                    value = float(data_point[metric])
                    if value > threshold:
                        anomalies[metric] = {
                            'is_anomaly': True,
                            'severity': 'critical',
                            'message': f"Critical threshold exceeded: {metric}={value} (threshold: {threshold})"
                        }
                except (ValueError, TypeError):
                    logging.warning(f"Could not convert {metric} value to float: {data_point[metric]}")
        
        # 3. Statistical anomaly detection using Z-scores (if enough history)
        if len(self.history) >= 10:  # Need some history for statistical methods
            for metric in self.numeric_metrics:
                if metric in data_point:
                    try:
                        # Convert to float in case it's a string from CSV
                        value = float(data_point[metric])
                        
                        # Calculate mean and std from history
                        historical_values = []
                        for point in self.history:
                            if metric in point:
                                try:
                                    historical_values.append(float(point[metric]))
                                except (ValueError, TypeError):
                                    pass
                        
                        if historical_values:
                            mean_value = np.mean(historical_values)
                            std_value = np.std(historical_values)
                            
                            # Avoid division by zero
                            if std_value > 0:
                                z_score = abs((value - mean_value) / std_value)
                                
                                if z_score > self.z_score_threshold:
                                    severity = 'medium' if z_score < self.z_score_threshold * 1.5 else 'high'
                                    anomalies[metric] = {
                                        'is_anomaly': True,
                                        'severity': severity,
                                        'z_score': z_score,
                                        'message': f"Statistical anomaly detected: {metric}={value} (z-score: {z_score:.2f})"
                                    }
                    except (ValueError, TypeError):
                        logging.warning(f"Could not process {metric} for statistical anomaly detection")
        
        # 4. Check if values are outside normal ranges
        for metric, (min_val, max_val) in self.normal_ranges.items():
            if metric in data_point:
                try:
                    value = float(data_point[metric])
                    if value < min_val or value > max_val:
                        # Only add if not already detected by other methods
                        if metric not in anomalies:
                            anomalies[metric] = {
                                'is_anomaly': True,
                                'severity': 'low',
                                'message': f"Value outside normal range: {metric}={value} (range: {min_val}-{max_val})"
                            }
                except (ValueError, TypeError):
                    logging.warning(f"Could not convert {metric} value to float: {data_point[metric]}")
        
        return anomalies

    def process_data_point(self, data_point_json):
        """
        Process a new data point and detect anomalies.
        
        Args:
            data_point_json: JSON string or dict with VM metrics
            
        Returns:
            Dict with processing results including anomalies
        """
        try:
            # Parse JSON data if needed
            if isinstance(data_point_json, str):
                data_point = json.loads(data_point_json)
            else:
                data_point = data_point_json
                
            # Add to history
            self.add_data_point(data_point)
            
            # Detect anomalies
            anomalies = self.detect_anomalies(data_point)
            
            # Determine overall status
            has_anomalies = len(anomalies) > 0
            has_critical = any(a['severity'] == 'critical' for a in anomalies.values())
            
            result = {
                'timestamp': datetime.now().isoformat(),
                'vm_id': data_point.get('vm_id', 'unknown'),
                'has_anomalies': has_anomalies,
                'status': 'critical' if has_critical else 'warning' if has_anomalies else 'normal',
                'anomalies': anomalies
            }
            
            # Log any anomalies
            if has_anomalies:
                severity = logging.CRITICAL if has_critical else logging.WARNING
                logging.log(severity, f"VM {result['vm_id']} anomalies detected: {len(anomalies)}")
                for metric, anomaly in anomalies.items():
                    logging.log(severity, anomaly['message'])
            
            return result
            
        except Exception as e:
            logging.error(f"Error processing data point: {str(e)}")
            return {
                'error': str(e),
                'status': 'error'
            }

rabbitmq_host = 'localhost'
rabbitmq_queue = 'q.metrics'

def consume_metrics_from_queue(queue_name=rabbitmq_queue):
    """Consume metrics from RabbitMQ queue and process them."""
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    
    channel.queue_declare(queue=queue_name, durable=True)
    
    def callback(ch, method, properties, body):
        data_point = json.loads(body.decode('utf-8'))
        logging.info(f"Received data point: {data_point}")
        
        # Process the data point
        detector = VMAnomalyDetector(window_size=300, z_score_threshold=3.0)
        result = detector.process_data_point(data_point)
        
        logging.info(f"Processing result: {result}")
        
        ch.basic_ack(delivery_tag=method.delivery_tag)
    
    channel.basic_consume(queue=queue_name, on_message_callback=callback)
    
    logging.info("Waiting for messages. To exit press CTRL+C")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    
    connection.close()


# Example usage with the provided data point
if __name__ == "__main__":
    consume_metrics_from_queue()