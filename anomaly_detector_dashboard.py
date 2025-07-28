import psutil
import time
import pandas as pd
from sklearn.ensemble import IsolationForest
import numpy as np
import threading
from collections import deque
import warnings
import json
import os
from datetime import datetime
import logging

# Flask imports for web dashboard
try:
    from flask import Flask, render_template, jsonify, request
    from flask_socketio import SocketIO, emit
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("Flask not available. Install with: pip install flask flask-socketio")

warnings.filterwarnings("ignore")

class RealTimeAnomalyDetector:
    def __init__(self, window_size=60, contamination=0.1, log_file="system_monitor.log"):
        self.window_size = window_size
        self.contamination = contamination
        self.model = IsolationForest(contamination=contamination, random_state=42)
        self.data_buffer = deque(maxlen=window_size)
        self.is_trained = False
        self.metrics_history = []
        self.anomalies = deque(maxlen=100)  # Keep last 100 anomalies
        self.system_status = "initializing"  # Track system status
        
        # Chart data for dashboard (limit to 30 points for performance)
        self.chart_data = deque(maxlen=30)
        
        # Setup logging
        self.log_file = log_file
        self._setup_logging()
        
        # For dashboard updates
        self.latest_metrics = {}
        self.socketio = None
        
    def set_socketio(self, socketio):
        """Set socketio instance for real-time updates"""
        self.socketio = socketio
        
    def _setup_logging(self):
        """Configure logging to file and console"""
        # Create logs directory if it doesn't exist
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # Full log file path
        full_log_path = os.path.join(log_dir, self.log_file)
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(full_log_path),
                logging.StreamHandler()  # Also log to console
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Create separate CSV log for metrics
        self.metrics_log_file = os.path.join(log_dir, "metrics_history.csv")
        self.anomalies_log_file = os.path.join(log_dir, "anomalies.json")
        
        # Initialize CSV if it doesn't exist
        if not os.path.exists(self.metrics_log_file):
            with open(self.metrics_log_file, 'w') as f:
                f.write("timestamp,cpu_percent,cpu_frequency,memory_percent,memory_available_gb,disk_read_mb,disk_write_mb,network_sent_mb,network_recv_mb,is_anomaly,anomaly_score\n")
    
    def log_metrics(self, metrics, is_anomaly=False, anomaly_score=None):
        """Log metrics to CSV file"""
        try:
            with open(self.metrics_log_file, 'a') as f:
                f.write(f"{datetime.fromtimestamp(metrics['timestamp'])},"
                       f"{metrics['cpu_percent']},"
                       f"{metrics['cpu_frequency']},"
                       f"{metrics['memory_percent']},"
                       f"{metrics['memory_available_gb']:.2f},"
                       f"{metrics['disk_read_mb']:.2f},"
                       f"{metrics['disk_write_mb']:.2f},"
                       f"{metrics['network_sent_mb']:.2f},"
                       f"{metrics['network_recv_mb']:.2f},"
                       f"{is_anomaly},"
                       f"{anomaly_score if anomaly_score is not None else ''}\n")
        except Exception as e:
            self.logger.error(f"Failed to log metrics to CSV: {e}")
    
    def log_anomaly_details(self, anomaly_data):
        """Log detailed anomaly information"""
        try:
            # Add to in-memory anomalies list
            self.anomalies.append({
                'timestamp': anomaly_data['timestamp'],
                'anomaly_score': anomaly_data['anomaly_score'],
                'metrics': anomaly_data['metrics']
            })
            
            # Also log to file
            anomalies = list(self.anomalies)
            with open(self.anomalies_log_file, 'w') as f:
                json.dump(anomalies, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to log anomaly details: {e}")
    
    def get_system_metrics(self):
        """Collect current system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_freq = psutil.cpu_freq()
            cpu_freq_current = cpu_freq.current if cpu_freq else 0
            
            # Memory metrics
            mem = psutil.virtual_memory()
            mem_percent = mem.percent
            mem_available = mem.available / (1024**3)  # GB
            
            # Disk I/O metrics (calculate per second)
            disk_io_1 = psutil.disk_io_counters()
            time.sleep(0.5)
            disk_io_2 = psutil.disk_io_counters()
            
            if disk_io_1 and disk_io_2:
                disk_read_bytes = (disk_io_2.read_bytes - disk_io_1.read_bytes) / (1024**2) * 2  # MB/s
                disk_write_bytes = (disk_io_2.write_bytes - disk_io_1.write_bytes) / (1024**2) * 2  # MB/s
            else:
                disk_read_bytes = 0
                disk_write_bytes = 0
            
            # Network metrics (calculate per second)
            net_io_1 = psutil.net_io_counters()
            time.sleep(0.5)
            net_io_2 = psutil.net_io_counters()
            
            net_sent = (net_io_2.bytes_sent - net_io_1.bytes_sent) / (1024**2) * 2  # MB/s
            net_recv = (net_io_2.bytes_recv - net_io_1.bytes_recv) / (1024**2) * 2  # MB/s
            
            metrics = {
                'timestamp': time.time(),
                'cpu_percent': cpu_percent,
                'cpu_frequency': cpu_freq_current,
                'memory_percent': mem_percent,
                'memory_available_gb': mem_available,
                'disk_read_mb': disk_read_bytes,
                'disk_write_mb': disk_write_bytes,
                'network_sent_mb': net_sent,
                'network_recv_mb': net_recv
            }
            
            return metrics
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
            return None
    
    def collect_data(self):
        """Continuously collect system metrics"""
        self.logger.info("Starting data collection thread")
        chart_counter = 0
        while True:
            try:
                metrics = self.get_system_metrics()
                if metrics:
                    self.data_buffer.append(metrics)
                    self.metrics_history.append(metrics)
                    self.latest_metrics = metrics
                    
                    # Add to chart data every 2 seconds (to reduce data points)
                    chart_counter += 1
                    if chart_counter >= 2:
                        chart_data_point = {
                            'timestamp': metrics['timestamp'],
                            'cpu_percent': metrics['cpu_percent'],
                            'memory_percent': metrics['memory_percent'],
                            'disk_read_mb': metrics['disk_read_mb'],
                            'network_sent_mb': metrics['network_sent_mb']
                        }
                        self.chart_data.append(chart_data_point)
                        chart_counter = 0
                    
                    # Log every data point to CSV
                    self.log_metrics(metrics)
                    
                    # Emit real-time update to dashboard
                    if self.socketio:
                        self.socketio.emit('metrics_update', {
                            'timestamp': datetime.fromtimestamp(metrics['timestamp']).isoformat(),
                            'cpu_percent': metrics['cpu_percent'],
                            'memory_percent': metrics['memory_percent'],
                            'disk_read_mb': metrics['disk_read_mb'],
                            'disk_write_mb': metrics['disk_write_mb'],
                            'network_sent_mb': metrics['network_sent_mb'],
                            'network_recv_mb': metrics['network_recv_mb']
                        })
                time.sleep(1)
            except Exception as e:
                self.logger.error(f"Error in data collection: {e}")
                time.sleep(1)
    
    def train_model(self):
        """Train the anomaly detection model"""
        if len(self.data_buffer) < 10:
            self.logger.warning("Insufficient data for training")
            return False
            
        try:
            df = pd.DataFrame(list(self.data_buffer))
            features = df.drop(['timestamp'], axis=1)
            
            self.model.fit(features)
            self.is_trained = True
            self.system_status = "active"
            self.logger.info("Model trained successfully with {} data points".format(len(self.data_buffer)))
            
            # Notify dashboard of status change
            if self.socketio:
                self.socketio.emit('status_update', {'status': 'active'})
                
            return True
        except Exception as e:
            self.logger.error(f"Error training model: {e}")
            return False
    
    def detect_anomalies(self):
        """Detect anomalies in the latest metrics"""
        if not self.is_trained or len(self.data_buffer) == 0:
            return []
            
        try:
            df = pd.DataFrame([self.data_buffer[-1]])
            features = df.drop(['timestamp'], axis=1)
            
            predictions = self.model.predict(features)
            anomaly_scores = self.model.decision_function(features)
            
            results = []
            for i, (pred, score) in enumerate(zip(predictions, anomaly_scores)):
                is_anomaly = pred == -1
                result = {
                    'timestamp': df.iloc[i]['timestamp'],
                    'is_anomaly': is_anomaly,
                    'anomaly_score': score,
                    'metrics': self.data_buffer[-1]
                }
                results.append(result)
                
                # Log to CSV with anomaly info
                self.log_metrics(self.data_buffer[-1], is_anomaly, score)
                
                # Handle anomalies - only show high severity in dashboard
                if is_anomaly and score < -0.1:  # High severity threshold
                    anomaly_details = {
                        'timestamp': datetime.fromtimestamp(result['timestamp']).isoformat(),
                        'anomaly_score': float(score),
                        'metrics': {k: float(v) if isinstance(v, (int, float)) else v 
                                   for k, v in self.data_buffer[-1].items()}
                    }
                    self.log_anomaly_details(anomaly_details)
                    
                    # Emit anomaly to dashboard (only high severity)
                    if self.socketio:
                        self.socketio.emit('anomaly_detected', {
                            'timestamp': anomaly_details['timestamp'],
                            'anomaly_score': anomaly_details['anomaly_score'],
                            'metrics': anomaly_details['metrics']
                        })
                    
            return results
        except Exception as e:
            self.logger.error(f"Error detecting anomalies: {e}")
            return []

# Flask Dashboard Application
if FLASK_AVAILABLE:
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key-change-this'
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
    detector = None

    @app.route('/')
    def index():
        return render_template('dashboard.html')

    @app.route('/api/metrics')
    def get_latest_metrics():
        if detector and detector.latest_metrics:
            metrics = detector.latest_metrics.copy()
            metrics['timestamp'] = datetime.fromtimestamp(metrics['timestamp']).isoformat()
            return jsonify(metrics)
        return jsonify({})

    @app.route('/api/anomalies')
    def get_anomalies():
        if detector:
            # Only return high severity anomalies (-0.5 and below)
            high_severity_anomalies = []
            for anomaly in reversed(detector.anomalies):
                if anomaly['anomaly_score'] < -0.1:
                    high_severity_anomalies.append({
                        'timestamp': anomaly['timestamp'],
                        'anomaly_score': anomaly['anomaly_score'],
                        'metrics': anomaly['metrics']
                    })
            return jsonify(high_severity_anomalies[:10])  # Return only top 10
        return jsonify([])

    @app.route('/api/chart-data')
    def get_chart_data():
        if detector:
            # Return last 30 chart data points
            chart_data = list(detector.chart_data)
            return jsonify(chart_data)
        return jsonify([])

    @app.route('/api/status')
    def get_status():
        if detector:
            return jsonify({
                'status': detector.system_status,
                'is_trained': detector.is_trained,
                'data_points': len(detector.data_buffer),
                'anomalies_count': len(detector.anomalies),
                'uptime': len(detector.metrics_history)
            })
        return jsonify({'status': 'offline'})

    @socketio.on('connect')
    def handle_connect():
        print('Client connected')
        # Send current status on connect
        if detector:
            emit('status_update', {'status': detector.system_status})

    @socketio.on('disconnect')
    def handle_disconnect():
        print('Client disconnected')

def main():
    global detector, socketio
    
    # Create detector
    detector = RealTimeAnomalyDetector(
        window_size=120, 
        contamination=0.05,
        log_file="system_monitor.log"
    )
    
    # Set up socketio for real-time updates if available
    if FLASK_AVAILABLE:
        detector.set_socketio(socketio)
    
    # Start data collection in background thread
    collection_thread = threading.Thread(target=detector.collect_data, daemon=True)
    collection_thread.start()
    
    detector.logger.info("=" * 50)
    detector.logger.info("Starting real-time anomaly detection system")
    detector.logger.info("Log files location: logs/")
    detector.logger.info("Collecting baseline data for 60 seconds...")
    detector.logger.info("=" * 50)
    
    # Start web dashboard if Flask is available
    if FLASK_AVAILABLE:
        detector.logger.info("Starting web dashboard at http://localhost:5000")
        # Run Flask app in a separate thread
        dashboard_thread = threading.Thread(target=lambda: socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False), daemon=True)
        dashboard_thread.start()
    
    # Wait for baseline data collection
    time.sleep(60)
    
    # Initial training
    if detector.train_model():
        detector.logger.info("[SUCCESS] Model trained successfully!")
    else:
        detector.logger.error("[ERROR] Failed to train model. Insufficient data.")
        detector.system_status = "error"
        if FLASK_AVAILABLE and detector.socketio:
            detector.socketio.emit('status_update', {'status': 'error'})
        return
    
    detector.logger.info("Starting real-time monitoring...")
    detector.logger.info("Checking for anomalies every 2 seconds")
    
    # Main detection loop
    anomaly_count = 0
    while True:
        try:
            results = detector.detect_anomalies()
            for result in results:
                if result['is_anomaly']:
                    anomaly_count += 1
                    timestamp = datetime.fromtimestamp(result['timestamp'])
                    score = result['anomaly_score']
                    metrics = result['metrics']
                    
                    # Log to file and console
                    detector.logger.warning(
                        f"ANOMALY #{anomaly_count} DETECTED at {timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                    detector.logger.warning(f"  Anomaly Score: {score:.3f}")
                    detector.logger.warning(
                        f"  CPU: {metrics['cpu_percent']:.1f}% | "
                        f"Memory: {metrics['memory_percent']:.1f}% | "
                        f"Disk Read: {metrics['disk_read_mb']:.2f}MB/s | "
                        f"Network Sent: {metrics['network_sent_mb']:.2f}MB/s"
                    )
                    detector.logger.warning("-" * 60)
                    
            time.sleep(2)
            
            # Retrain periodically
            if len(detector.metrics_history) % 300 == 0:  # Every 5 minutes
                if detector.train_model():
                    detector.logger.info("Model retrained with new data")
                    
        except KeyboardInterrupt:
            detector.logger.info("Shutting down monitoring system...")
            detector.logger.info(f"Total anomalies detected: {anomaly_count}")
            detector.system_status = "stopped"
            if FLASK_AVAILABLE and detector.socketio:
                detector.socketio.emit('status_update', {'status': 'stopped'})
            break
        except Exception as e:
            detector.logger.error(f"Error in main loop: {e}")
            time.sleep(2)

if __name__ == "__main__":
    # Create templates directory and HTML file
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # Create dashboard HTML template with UTF-8 encoding
    dashboard_html = '''<!DOCTYPE html>
<html>
<head>
    <title>System Monitor Dashboard</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: #f5f7fa; color: #333; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .metric-card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.08); transition: transform 0.2s; }
        .metric-card:hover { transform: translateY(-2px); box-shadow: 0 4px 20px rgba(0,0,0,0.15); }
        .metric-value { font-size: 2em; font-weight: bold; color: #2c3e50; margin: 10px 0; }
        .metric-label { color: #7f8c8d; font-size: 0.9em; text-transform: uppercase; letter-spacing: 1px; }
        .chart-container { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.08); margin-bottom: 30px; }
        /* FIXED HEIGHT FOR CHART CONTAINER */
        .chart-wrapper { height: 300px; position: relative; }
        .anomalies-list { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.08); }
        .anomaly-item { padding: 15px; border-left: 4px solid #e74c3c; margin-bottom: 10px; background: #fdf2f2; border-radius: 5px; }
        .anomaly-item:nth-child(odd) { background: #f8f9fa; }
        .anomaly-score { font-weight: bold; color: #e74c3c; }
        .status-indicator { display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 10px; }
        .status-active { background: #2ecc71; box-shadow: 0 0 10px #2ecc71; }
        .status-initializing { background: #f39c12; }
        .status-error { background: #e74c3c; }
        .status-stopped { background: #95a5a6; }
        h1, h2, h3 { margin-top: 0; }
        .critical { color: #e74c3c; }
        .warning { color: #f39c12; }
        .normal { color: #2ecc71; }
        .progress-bar { height: 10px; background: #ecf0f1; border-radius: 5px; margin-top: 10px; overflow: hidden; }
        .progress-fill { height: 100%; border-radius: 5px; transition: width 0.3s ease; }
        .cpu-progress { background: linear-gradient(90deg, #3498db, #2980b9); }
        .memory-progress { background: linear-gradient(90deg, #9b59b6, #8e44ad); }
        .timestamp { color: #95a5a6; font-size: 0.8em; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 15px; }
        .stat-card { background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }
        .stat-value { font-size: 1.5em; font-weight: bold; color: #2c3e50; }
        .stat-label { color: #7f8c8d; font-size: 0.8em; }
        .severity-high { background: #ffebee; border-left-color: #c62828; }
        .severity-medium { background: #fff8e1; border-left-color: #ff8f00; }
        .severity-low { background: #e8f5e9; border-left-color: #2e7d32; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>System Monitor Dashboard</h1>
            <div id="status">Status: <span class="status-indicator status-initializing"></span> <span id="status-text">Initializing...</span></div>
        </div>

        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">CPU Usage</div>
                <div id="cpu-value" class="metric-value">0%</div>
                <div class="progress-bar">
                    <div id="cpu-progress" class="progress-fill cpu-progress" style="width: 0%;"></div>
                </div>
            </div>
            
            <div class="metric-card">
                <div class="metric-label">Memory Usage</div>
                <div id="memory-value" class="metric-value">0%</div>
                <div class="progress-bar">
                    <div id="memory-progress" class="progress-fill memory-progress" style="width: 0%;"></div>
                </div>
            </div>
            
            <div class="metric-card">
                <div class="metric-label">Disk Read</div>
                <div id="disk-read-value" class="metric-value">0 MB/s</div>
                <div class="metric-label">Current Activity</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-label">Network Sent</div>
                <div id="network-value" class="metric-value">0 MB/s</div>
                <div class="metric-label">Outgoing Traffic</div>
            </div>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value" id="data-points">0</div>
                <div class="stat-label">Data Points</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="anomalies-count">0</div>
                <div class="stat-label">Anomalies</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="uptime">0</div>
                <div class="stat-label">Uptime (sec)</div>
            </div>
        </div>

        <div class="chart-container">
            <h2>System Metrics (Last 30 samples)</h2>
            <!-- FIXED HEIGHT CHART WRAPPER -->
            <div class="chart-wrapper">
                <canvas id="metricsChart"></canvas>
            </div>
        </div>

        <div class="anomalies-list">
            <h2>Critical Anomalies Only</h2>
            <div id="anomalies-container">
                <p>No critical anomalies detected. System appears normal.</p>
            </div>
        </div>
    </div>

    <script>
        const socket = io();
        let metricsChart = null;
        let chartInitialized = false;

        // Initialize chart
        function initChart(initialData) {
            const ctx = document.getElementById('metricsChart').getContext('2d');
            
            // Prepare chart data
            const labels = [];
            const cpuData = [];
            const memoryData = [];
            const diskData = [];
            const networkData = [];
            
            // Process initial data
            for (let i = 0; i < initialData.length; i++) {
                const item = initialData[i];
                labels.push(new Date(item.timestamp * 1000).toLocaleTimeString());
                cpuData.push(item.cpu_percent);
                memoryData.push(item.memory_percent);
                diskData.push(item.disk_read_mb);
                networkData.push(item.network_sent_mb);
            }
            
            metricsChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'CPU %',
                            data: cpuData,
                            borderColor: '#3498db',
                            backgroundColor: 'rgba(52, 152, 219, 0.1)',
                            tension: 0.1,
                            fill: true,
                            pointRadius: 0
                        },
                        {
                            label: 'Memory %',
                            data: memoryData,
                            borderColor: '#9b59b6',
                            backgroundColor: 'rgba(155, 89, 182, 0.1)',
                            tension: 0.1,
                            fill: true,
                            pointRadius: 0
                        },
                        {
                            label: 'Disk Read (MB/s)',
                            data: diskData,
                            borderColor: '#2ecc71',
                            backgroundColor: 'rgba(46, 204, 113, 0.1)',
                            tension: 0.1,
                            fill: true,
                            pointRadius: 0
                        },
                        {
                            label: 'Network Sent (MB/s)',
                            data: networkData,
                            borderColor: '#e74c3c',
                            backgroundColor: 'rgba(231, 76, 60, 0.1)',
                            tension: 0.1,
                            fill: true,
                            pointRadius: 0
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false, // Allow custom sizing
                    animation: false, // Disable animations for better performance
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: {
                                color: 'rgba(0, 0, 0, 0.05)'
                            }
                        },
                        x: {
                            grid: {
                                color: 'rgba(0, 0, 0, 0.05)'
                            },
                            ticks: {
                                maxTicksLimit: 8 // Limit x-axis labels
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            position: 'top',
                            labels: {
                                usePointStyle: true,
                                padding: 15
                            }
                        },
                        tooltip: {
                            mode: 'index',
                            intersect: false
                        }
                    },
                    interaction: {
                        mode: 'nearest',
                        axis: 'x',
                        intersect: false
                    }
                }
            });
            
            chartInitialized = true;
        }

        // Update chart with new data point
        function updateChart(data) {
            if (!chartInitialized) return;
            
            const timestamp = new Date(data.timestamp).toLocaleTimeString();
            
            // Add new data point
            metricsChart.data.labels.push(timestamp);
            metricsChart.data.datasets[0].data.push(data.cpu_percent);
            metricsChart.data.datasets[1].data.push(data.memory_percent);
            metricsChart.data.datasets[2].data.push(data.disk_read_mb);
            metricsChart.data.datasets[3].data.push(data.network_sent_mb);
            
            // Remove oldest point if we have more than 30 points
            if (metricsChart.data.labels.length > 30) {
                metricsChart.data.labels.shift();
                metricsChart.data.datasets.forEach(dataset => dataset.data.shift());
            }
            
            // Update chart
            metricsChart.update('none'); // No animation for better performance
        }

        // Update metrics display
        function updateMetrics(data) {
            // Update metric cards
            document.getElementById('cpu-value').textContent = data.cpu_percent.toFixed(1) + '%';
            document.getElementById('memory-value').textContent = data.memory_percent.toFixed(1) + '%';
            document.getElementById('disk-read-value').textContent = data.disk_read_mb.toFixed(2) + ' MB/s';
            document.getElementById('network-value').textContent = data.network_sent_mb.toFixed(2) + ' MB/s';
            
            // Update progress bars
            document.getElementById('cpu-progress').style.width = Math.min(data.cpu_percent, 100) + '%';
            document.getElementById('memory-progress').style.width = Math.min(data.memory_percent, 100) + '%';
            
            // Update chart
            updateChart({
                timestamp: new Date(data.timestamp).getTime(),
                cpu_percent: data.cpu_percent,
                memory_percent: data.memory_percent,
                disk_read_mb: data.disk_read_mb,
                network_sent_mb: data.network_sent_mb
            });
        }

        // Update system status
        function updateStatus(status) {
            const statusIndicator = document.querySelector('.status-indicator');
            const statusText = document.getElementById('status-text');
            
            statusIndicator.className = 'status-indicator';
            
            switch(status) {
                case 'active':
                    statusIndicator.classList.add('status-active');
                    statusText.textContent = 'Active and Monitoring';
                    break;
                case 'initializing':
                    statusIndicator.classList.add('status-initializing');
                    statusText.textContent = 'Initializing... Collecting baseline data';
                    break;
                case 'error':
                    statusIndicator.classList.add('status-error');
                    statusText.textContent = 'Error - Check logs';
                    break;
                case 'stopped':
                    statusIndicator.classList.add('status-stopped');
                    statusText.textContent = 'Stopped';
                    break;
                default:
                    statusIndicator.classList.add('status-initializing');
                    statusText.textContent = status;
            }
        }

        // Update system statistics
        function updateStats(stats) {
            document.getElementById('data-points').textContent = stats.data_points || 0;
            document.getElementById('anomalies-count').textContent = stats.anomalies_count || 0;
            document.getElementById('uptime').textContent = stats.uptime || 0;
        }

        // Handle real-time metrics updates
        socket.on('metrics_update', function(data) {
            updateMetrics(data);
        });

        // Handle status updates
        socket.on('status_update', function(data) {
            updateStatus(data.status);
            
            // Refresh stats when status changes
            fetch('/api/status')
                .then(response => response.json())
                .then(updateStats)
                .catch(console.error);
        });

        // Handle anomaly detection - only high severity
        socket.on('anomaly_detected', function(data) {
            const container = document.getElementById('anomalies-container');
            
            // Clear "no anomalies" message if present
            if (container.children.length === 1 && container.children[0].textContent.includes('No critical anomalies')) {
                container.innerHTML = '';
            }
            
            const anomalyDiv = document.createElement('div');
            anomalyDiv.className = 'anomaly-item severity-high';
            
            // Determine severity class based on score
            let severityClass = 'severity-high';
            let severityText = 'CRITICAL';
            if (data.anomaly_score > -0.7) {
                severityClass = 'severity-medium';
                severityText = 'HIGH';
            }
            
            anomalyDiv.className = `anomaly-item ${severityClass}`;
            
            anomalyDiv.innerHTML = `
                <div><strong>${new Date(data.timestamp).toLocaleString()}</strong> <span class="timestamp">(${new Date(data.timestamp).toLocaleTimeString()})</span></div>
                <div>Severity: <strong>${severityText}</strong> | Anomaly Score: <span class="anomaly-score">${data.anomaly_score.toFixed(3)}</span></div>
                <div>
                    <span style="color: #3498db;">CPU: ${data.metrics.cpu_percent.toFixed(1)}%</span> | 
                    <span style="color: #9b59b6;">Memory: ${data.metrics.memory_percent.toFixed(1)}%</span> | 
                    <span style="color: #2ecc71;">Disk: ${data.metrics.disk_read_mb.toFixed(2)} MB/s</span> | 
                    <span style="color: #e74c3c;">Network: ${data.metrics.network_sent_mb.toFixed(2)} MB/s</span>
                </div>
            `;
            container.insertBefore(anomalyDiv, container.firstChild);
            
            // Remove old anomalies if more than 15
            while (container.children.length > 15) {
                container.removeChild(container.lastChild);
            }
        });

        // Fetch initial data
        Promise.all([
            fetch('/api/status').then(response => response.json()),
            fetch('/api/chart-data').then(response => response.json())
        ]).then(([statusData, chartData]) => {
            updateStatus(statusData.status);
            updateStats(statusData);
            
            // Initialize chart with historical data
            if (chartData.length > 0) {
                initChart(chartData);
            } else {
                // Initialize with empty chart
                initChart([]);
            }
        }).catch(error => {
            console.error('Error fetching initial data:', error);
            updateStatus('error');
        });

        // Fetch recent high-severity anomalies only
        fetch('/api/anomalies')
            .then(response => response.json())
            .then(anomalies => {
                const container = document.getElementById('anomalies-container');
                if (anomalies.length > 0) {
                    container.innerHTML = '';
                    anomalies.forEach(anomaly => {
                        const anomalyDiv = document.createElement('div');
                        
                        // Determine severity class based on score
                        let severityClass = 'severity-high';
                        let severityText = 'CRITICAL';
                        if (anomaly.anomaly_score > -0.7) {
                            severityClass = 'severity-medium';
                            severityText = 'HIGH';
                        }
                        
                        anomalyDiv.className = `anomaly-item ${severityClass}`;
                        anomalyDiv.innerHTML = `
                            <div><strong>${new Date(anomaly.timestamp).toLocaleString()}</strong></div>
                            <div>Severity: <strong>${severityText}</strong> | Anomaly Score: <span class="anomaly-score">${anomaly.anomaly_score.toFixed(3)}</span></div>
                            <div>
                                <span style="color: #3498db;">CPU: ${anomaly.metrics.cpu_percent.toFixed(1)}%</span> | 
                                <span style="color: #9b59b6;">Memory: ${anomaly.metrics.memory_percent.toFixed(1)}%</span> | 
                                <span style="color: #2ecc71;">Disk: ${anomaly.metrics.disk_read_mb.toFixed(2)} MB/s</span> | 
                                <span style="color: #e74c3c;">Network: ${anomaly.metrics.network_sent_mb.toFixed(2)} MB/s</span>
                            </div>
                        `;
                        container.appendChild(anomalyDiv);
                    });
                }
            })
            .catch(console.error);
    </script>
</body>
</html>'''
    
    # Write HTML file with UTF-8 encoding
    with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
        f.write(dashboard_html)
    
    main()