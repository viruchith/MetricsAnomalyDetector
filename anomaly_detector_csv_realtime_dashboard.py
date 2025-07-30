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
import argparse
import sqlite3
import hashlib

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
        
        # CSV data storage
        self.csv_data = None
        self.csv_anomalies = []
        
        # Setup logging
        self.log_file = log_file
        self._setup_logging()
        
        # Setup SQLite database
        self._setup_database()
        
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
    
    def _setup_database(self):
        """Setup SQLite database for storing CSV analysis history"""
        self.db_path = "anomaly_history.db"
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.execute('''CREATE TABLE IF NOT EXISTS csv_analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            file_hash TEXT UNIQUE,
            upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_records INTEGER,
            anomalies_found INTEGER,
            anomaly_rate REAL,
            analysis_data TEXT
        )''')
        
        self.conn.execute('''CREATE TABLE IF NOT EXISTS csv_anomalies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_id INTEGER,
            row_index INTEGER,
            timestamp REAL,
            anomaly_score REAL,
            reason TEXT,
            severity_factors TEXT,
            metrics TEXT,
            FOREIGN KEY (analysis_id) REFERENCES csv_analyses (id)
        )''')
        
        self.conn.commit()
        self.logger.info("Database initialized successfully")
    
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
                'metrics': anomaly_data['metrics'],
                'reason': anomaly_data.get('reason', 'Unknown'),
                'severity_factors': anomaly_data.get('severity_factors', [])
            })
            
            # Also log to file
            anomalies = list(self.anomalies)
            with open(self.anomalies_log_file, 'w') as f:
                json.dump(anomalies, f, indent=2, default=str)
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
    
    def analyze_anomaly_reason(self, metrics, anomaly_score):
        """Analyze and determine the reason for an anomaly"""
        reasons = []
        severity_factors = []
        
        # CPU Analysis
        if metrics['cpu_percent'] > 80:
            reasons.append("High CPU usage detected")
            severity_factors.append(f"CPU: {metrics['cpu_percent']:.1f}%")
        
        # Memory Analysis
        if metrics['memory_percent'] > 80:
            reasons.append("High memory consumption")
            severity_factors.append(f"Memory: {metrics['memory_percent']:.1f}%")
        
        # Disk I/O Analysis
        if metrics['disk_read_mb'] > 50 or metrics['disk_write_mb'] > 50:
            reasons.append("High disk activity")
            severity_factors.append(f"Disk I/O: {max(metrics['disk_read_mb'], metrics['disk_write_mb']):.1f} MB/s")
        
        # Network Analysis
        if metrics['network_sent_mb'] > 50 or metrics['network_recv_mb'] > 50:
            reasons.append("High network traffic")
            severity_factors.append(f"Network: {max(metrics['network_sent_mb'], metrics['network_recv_mb']):.1f} MB/s")
        
        # Anomaly score severity
        if anomaly_score < -0.8:
            reasons.append("Extremely unusual system behavior pattern")
        elif anomaly_score < -0.6:
            reasons.append("Significantly abnormal system behavior")
        
        # If no specific reasons found, use general analysis
        if not reasons:
            reasons.append("Unusual combination of system metrics")
        
        return {
            'reason': " | ".join(reasons) if reasons else "Unknown anomaly pattern",
            'severity_factors': severity_factors
        }
    
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
                    # Analyze anomaly reason
                    reason_analysis = self.analyze_anomaly_reason(self.data_buffer[-1], score)
                    
                    anomaly_details = {
                        'timestamp': datetime.fromtimestamp(result['timestamp']).isoformat(),
                        'anomaly_score': float(score),
                        'metrics': {k: float(v) if isinstance(v, (int, float)) else v 
                                   for k, v in self.data_buffer[-1].items()},
                        'reason': reason_analysis['reason'],
                        'severity_factors': reason_analysis['severity_factors']
                    }
                    self.log_anomaly_details(anomaly_details)
                    
                    # Emit anomaly to dashboard (only high severity)
                    if self.socketio:
                        self.socketio.emit('anomaly_detected', {
                            'timestamp': anomaly_details['timestamp'],
                            'anomaly_score': anomaly_details['anomaly_score'],
                            'metrics': anomaly_details['metrics'],
                            'reason': anomaly_details['reason'],
                            'severity_factors': anomaly_details['severity_factors']
                        })
                    
            return results
        except Exception as e:
            self.logger.error(f"Error detecting anomalies: {e}")
            return []

    def load_csv_data(self, csv_file_path):
        """Load historical metrics from CSV file"""
        try:
            # Read CSV file
            df = pd.read_csv(csv_file_path)
            
            # Convert timestamp column to datetime if it's string
            if 'timestamp' in df.columns:
                if pd.api.types.is_string_dtype(df['timestamp']):
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    # Convert to timestamp if needed
                    df['timestamp'] = df['timestamp'].apply(lambda x: x.timestamp())
            
            # Convert to list of dictionaries
            metrics_list = df.to_dict('records')
            
            self.csv_data = df
            self.logger.info(f"Loaded {len(metrics_list)} records from {csv_file_path}")
            return metrics_list
        except Exception as e:
            self.logger.error(f"Error loading CSV  {e}")
            return []
    
    def _calculate_file_hash(self, file_path):
        """Calculate SHA256 hash of a file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def save_csv_analysis_to_db(self, filename, results):
        """Save CSV analysis results to database"""
        try:
            # Calculate file hash
            file_hash = self._calculate_file_hash(filename)
            
            # Calculate statistics
            total_records = len(results)
            anomalies = [r for r in results if r['is_anomaly']]
            anomalies_found = len(anomalies)
            anomaly_rate = (anomalies_found / total_records * 100) if total_records > 0 else 0
            
            # Save analysis summary
            cursor = self.conn.cursor()
            cursor.execute('''INSERT OR IGNORE INTO csv_analyses 
                (filename, file_hash, total_records, anomalies_found, anomaly_rate, analysis_data)
                VALUES (?, ?, ?, ?, ?, ?)''',
                (os.path.basename(filename), file_hash, total_records, anomalies_found, anomaly_rate, 
                 json.dumps({'summary_only': True}, default=str)))
            
            # Get the analysis ID
            analysis_id = cursor.lastrowid
            if analysis_id == 0:  # If IGNORE was triggered (duplicate)
                cursor.execute('SELECT id FROM csv_analyses WHERE file_hash = ?', (file_hash,))
                analysis_id = cursor.fetchone()[0]
            
            # Save individual anomalies
            for result in anomalies:
                cursor.execute('''INSERT INTO csv_anomalies 
                    (analysis_id, row_index, timestamp, anomaly_score, reason, severity_factors, metrics)
                    VALUES (?, ?, ?, ?, ?, ?, ?)''',
                    (analysis_id, result.get('index', 0), result.get('timestamp', 0),
                     result.get('anomaly_score', 0), result.get('reason', ''),
                     json.dumps(result.get('severity_factors', []), default=str),
                     json.dumps(result.get('metrics', {}), default=str)))
            
            self.conn.commit()
            self.logger.info(f"Analysis results saved to database for {filename}")
            return analysis_id
            
        except Exception as e:
            self.logger.error(f"Error saving analysis to database: {e}")
            return None
    
    def get_csv_analysis_history(self):
        """Retrieve CSV analysis history from database"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''SELECT id, filename, upload_time, total_records, anomalies_found, anomaly_rate
                FROM csv_analyses ORDER BY upload_time DESC LIMIT 50''')
            rows = cursor.fetchall()
            
            history = []
            for row in rows:
                history.append({
                    'id': row[0],
                    'filename': row[1],
                    'upload_time': row[2],
                    'total_records': row[3],
                    'anomalies_found': row[4],
                    'anomaly_rate': row[5]
                })
            return history
        except Exception as e:
            self.logger.error(f"Error retrieving analysis history: {e}")
            return []
    
    def get_analysis_details(self, analysis_id):
        """Retrieve detailed results for a specific analysis"""
        try:
            cursor = self.conn.cursor()
            
            # Get analysis summary
            cursor.execute('''SELECT filename, upload_time, total_records, anomalies_found, anomaly_rate
                FROM csv_analyses WHERE id = ?''', (analysis_id,))
            summary = cursor.fetchone()
            
            if not summary:
                return None
            
            # Get anomalies for this analysis
            cursor.execute('''SELECT row_index, timestamp, anomaly_score, reason, severity_factors, metrics
                FROM csv_anomalies WHERE analysis_id = ? ORDER BY anomaly_score ASC''', (analysis_id,))
            anomaly_rows = cursor.fetchall()
            
            anomalies = []
            for row in anomaly_rows:
                anomalies.append({
                    'index': row[0],
                    'timestamp': row[1],
                    'anomaly_score': row[2],
                    'reason': row[3],
                    'severity_factors': json.loads(row[4]) if row[4] else [],
                    'metrics': json.loads(row[5]) if row[5] else {}
                })
            
            return {
                'summary': {
                    'id': analysis_id,
                    'filename': summary[0],
                    'upload_time': summary[1],
                    'total_records': summary[2],
                    'anomalies_found': summary[3],
                    'anomaly_rate': summary[4]
                },
                'anomalies': anomalies
            }
        except Exception as e:
            self.logger.error(f"Error retrieving analysis details: {e}")
            return None
    
    def detect_anomalies_from_csv(self, csv_file_path, output_file=None):
        """Detect anomalies in historical CSV data"""
        self.logger.info(f"Starting anomaly detection on CSV file: {csv_file_path}")
        
        # Load data from CSV
        metrics_data = self.load_csv_data(csv_file_path)
        
        if not metrics_data:
            self.logger.error("No data loaded from CSV file")
            return []
        
        # Prepare data for training
        df = pd.DataFrame(metrics_data)
        
        # Check if required columns exist
        required_columns = ['cpu_percent', 'memory_percent', 'disk_read_mb', 'network_sent_mb']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            self.logger.error(f"Missing required columns: {missing_columns}")
            return []
        
        # Prepare features (exclude non-feature columns)
        feature_columns = [col for col in df.columns if col not in ['timestamp', 'is_anomaly', 'anomaly_score']]
        features = df[feature_columns]
        
        # Train model on historical data
        try:
            self.logger.info("Training model on historical data...")
            self.model.fit(features)
            self.is_trained = True
            self.logger.info("Model trained successfully")
        except Exception as e:
            self.logger.error(f"Error training model: {e}")
            return []
        
        # Detect anomalies
        try:
            self.logger.info("Detecting anomalies in historical data...")
            predictions = self.model.predict(features)
            anomaly_scores = self.model.decision_function(features)
            
            # Create results
            results = []
            anomalies_found = 0
            
            for i, (pred, score) in enumerate(zip(predictions, anomaly_scores)):
                is_anomaly = pred == -1
                if is_anomaly:
                    anomalies_found += 1
                
                # Analyze anomaly reason
                reason_analysis = self.analyze_anomaly_reason(df.iloc[i].to_dict(), score)
                
                result = {
                    'index': i,
                    'timestamp': df.iloc[i]['timestamp'] if 'timestamp' in df.columns else i,
                    'is_anomaly': is_anomaly,
                    'anomaly_score': float(score),  # Ensure it's JSON serializable
                    'metrics': {k: float(v) if isinstance(v, (int, float, np.integer, np.floating)) else str(v) 
                               for k, v in df.iloc[i].to_dict().items()},
                    'reason': reason_analysis['reason'],
                    'severity_factors': reason_analysis['severity_factors']
                }
                results.append(result)
            
            self.csv_anomalies = [r for r in results if r['is_anomaly']]
            self.logger.info(f"Anomaly detection complete. Found {anomalies_found} anomalies out of {len(results)} records")
            
            # Save results to database
            analysis_id = self.save_csv_analysis_to_db(csv_file_path, results)
            
            # Save results to output file if specified
            if output_file:
                self.save_anomaly_results(results, output_file)
            
            return {
                'results': results,
                'analysis_id': analysis_id
            }
            
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
            # Only return high severity anomalies (-0.1 and below)
            high_severity_anomalies = []
            for anomaly in reversed(detector.anomalies):
                if anomaly['anomaly_score'] < -0.1:
                    high_severity_anomalies.append({
                        'timestamp': anomaly['timestamp'],
                        'anomaly_score': anomaly['anomaly_score'],
                        'metrics': anomaly['metrics'],
                        'reason': anomaly.get('reason', 'Unknown'),
                        'severity_factors': anomaly.get('severity_factors', [])
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

    @app.route('/api/csv-data')
    def get_csv_data():
        if detector and detector.csv_data is not None:
            # Return CSV data for visualization
            df = detector.csv_data.copy()
            
            # Limit to 100 points for performance
            if len(df) > 100:
                df = df.tail(100)
            
            # Convert timestamp if needed
            if 'timestamp' in df.columns:
                df['display_time'] = df['timestamp'].apply(
                    lambda x: datetime.fromtimestamp(x).strftime('%H:%M:%S') if isinstance(x, (int, float)) 
                    else str(x)
                )
            
            # Convert to JSON-serializable format
            result = []
            for _, row in df.iterrows():
                row_dict = {}
                for key, value in row.items():
                    if isinstance(value, (np.integer, np.floating)):
                        row_dict[key] = float(value)
                    elif isinstance(value, (int, float)):
                        row_dict[key] = value
                    else:
                        row_dict[key] = str(value)
                result.append(row_dict)
            
            return jsonify(result)
        return jsonify([])

    @app.route('/api/csv-anomalies')
    def get_csv_anomalies():
        if detector:
            # Ensure all data is JSON serializable
            serializable_anomalies = []
            for anomaly in detector.csv_anomalies:
                serializable_anomaly = {}
                for key, value in anomaly.items():
                    if isinstance(value, (np.integer, np.floating)):
                        serializable_anomaly[key] = float(value)
                    elif isinstance(value, (int, float)):
                        serializable_anomaly[key] = value
                    elif isinstance(value, dict):
                        # Handle nested dictionary
                        serializable_dict = {}
                        for k, v in value.items():
                            if isinstance(v, (np.integer, np.floating)):
                                serializable_dict[k] = float(v)
                            elif isinstance(v, (int, float)):
                                serializable_dict[k] = v
                            else:
                                serializable_dict[k] = str(v)
                        serializable_anomaly[key] = serializable_dict
                    elif isinstance(value, list):
                        # Handle lists
                        serializable_list = []
                        for item in value:
                            if isinstance(item, (np.integer, np.floating)):
                                serializable_list.append(float(item))
                            elif isinstance(item, (int, float)):
                                serializable_list.append(item)
                            else:
                                serializable_list.append(str(item))
                        serializable_anomaly[key] = serializable_list
                    else:
                        serializable_anomaly[key] = str(value)
                serializable_anomalies.append(serializable_anomaly)
            return jsonify(serializable_anomalies)
        return jsonify([])

    @app.route('/api/upload-csv', methods=['POST'])
    def upload_csv():
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        try:
            # Save uploaded file temporarily
            temp_path = 'temp_uploaded_file.csv'
            file.save(temp_path)
            
            # Process the CSV file
            result = detector.detect_anomalies_from_csv(temp_path)
            
            # Clean up temp file
            os.remove(temp_path)
            
            if result and 'results' in result:
                results = result['results']
                anomalies = [r for r in results if r['is_anomaly']]
                anomaly_rate = len(anomalies)/len(results)*100 if results else 0
                
                return jsonify({
                    'success': True,
                    'total_records': len(results),
                    'anomalies_found': len(anomalies),
                    'anomaly_rate': anomaly_rate,
                    'analysis_id': result.get('analysis_id')
                })
            else:
                return jsonify({'error': 'Failed to process CSV file'}), 500
                
        except Exception as e:
            return jsonify({'error': f'Error processing file: {str(e)}'}), 500

    @app.route('/api/analysis-history')
    def get_analysis_history():
        if detector:
            history = detector.get_csv_analysis_history()
            return jsonify(history)
        return jsonify([])

    @app.route('/api/analysis-details/<int:analysis_id>')
    def get_analysis_details(analysis_id):
        if detector:
            details = detector.get_analysis_details(analysis_id)
            if details:
                # Make sure all data is JSON serializable
                serializable_details = {
                    'summary': details['summary'],
                    'anomalies': []
                }
                
                for anomaly in details['anomalies']:
                    serializable_anomaly = {}
                    for key, value in anomaly.items():
                        if isinstance(value, (np.integer, np.floating)):
                            serializable_anomaly[key] = float(value)
                        elif isinstance(value, (int, float)):
                            serializable_anomaly[key] = value
                        elif isinstance(value, dict):
                            serializable_dict = {}
                            for k, v in value.items():
                                if isinstance(v, (np.integer, np.floating)):
                                    serializable_dict[k] = float(v)
                                elif isinstance(v, (int, float)):
                                    serializable_dict[k] = v
                                else:
                                    serializable_dict[k] = str(v)
                            serializable_anomaly[key] = serializable_dict
                        elif isinstance(value, list):
                            serializable_list = []
                            for item in value:
                                if isinstance(item, (np.integer, np.floating)):
                                    serializable_list.append(float(item))
                                elif isinstance(item, (int, float)):
                                    serializable_list.append(item)
                                else:
                                    serializable_list.append(str(item))
                            serializable_anomaly[key] = serializable_list
                        else:
                            serializable_anomaly[key] = str(value)
                    serializable_details['anomalies'].append(serializable_anomaly)
                
                return jsonify(serializable_details)
            else:
                return jsonify({'error': 'Analysis not found'}), 404
        return jsonify({'error': 'Detector not initialized'}), 500

    @app.route('/api/status')
    def get_status():
        if detector:
            return jsonify({
                'status': detector.system_status,
                'is_trained': detector.is_trained,
                'data_points': len(detector.data_buffer),
                'anomalies_count': len(detector.anomalies),
                'uptime': len(detector.metrics_history),
                'has_csv_data': detector.csv_data is not None
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
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='System Metrics Anomaly Detector')
    parser.add_argument('--csv-file', type=str, help='Path to CSV file for batch anomaly detection')
    parser.add_argument('--output-file', type=str, help='Output file for CSV anomaly results')
    parser.add_argument('--contamination', type=float, default=0.05, help='Anomaly contamination rate (0.0-1.0)')
    parser.add_argument('--window-size', type=int, default=120, help='Training window size in seconds')
    args = parser.parse_args()
    
    # Check if CSV mode is requested
    if args.csv_file:
        # Batch processing mode
        detector = RealTimeAnomalyDetector(
            window_size=args.window_size,
            contamination=args.contamination,
            log_file="csv_analysis.log"
        )
        
        print(f"Processing CSV file: {args.csv_file}")
        if args.output_file:
            print(f"Output will be saved to: {args.output_file}")
        
        result = detector.detect_anomalies_from_csv(args.csv_file, args.output_file)
        
        if result and 'results' in result:
            results = result['results']
            anomalies = [r for r in results if r['is_anomaly']]
            print(f"\nAnalysis complete!")
            print(f"Total records processed: {len(results)}")
            print(f"Anomalies detected: {len(anomalies)}")
            print(f"Anomaly rate: {len(anomalies)/len(results)*100:.2f}%")
            
            # Show top anomalies with reasons
            if anomalies:
                print("\nTop anomalies with reasons:")
                sorted_anomalies = sorted(anomalies, key=lambda x: x['anomaly_score'])[:10]
                for i, anomaly in enumerate(sorted_anomalies):
                    timestamp = anomaly['timestamp']
                    if isinstance(timestamp, (int, float)):
                        timestamp = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                    print(f"  {i+1}. Score: {anomaly['anomaly_score']:.3f} | Time: {timestamp}")
                    print(f"     Reason: {anomaly['reason']}")
                    if anomaly['severity_factors']:
                        print(f"     Severity Factors: {', '.join(anomaly['severity_factors'])}")
                    print()
        else:
            print("No results generated. Check logs for errors.")
        
        return
    
    # Create detector for real-time monitoring
    detector = RealTimeAnomalyDetector(
        window_size=args.window_size, 
        contamination=args.contamination,
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
        .anomaly-reason { font-style: italic; color: #666; margin-top: 5px; padding: 8px; background: #f8f9fa; border-radius: 4px; }
        .severity-factors { font-size: 0.9em; color: #888; margin-top: 5px; }
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
        
        /* CSV Upload Section */
        .csv-upload { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.08); margin-bottom: 30px; }
        .upload-form { display: flex; gap: 10px; align-items: center; }
        .upload-form input[type="file"] { flex: 1; }
        .upload-form button { background: #3498db; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; }
        .upload-form button:hover { background: #2980b9; }
        .upload-status { margin-top: 10px; padding: 10px; border-radius: 5px; }
        .upload-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .upload-error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        
        /* CSV Chart */
        .csv-chart-container { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.08); margin-bottom: 30px; }
        .csv-chart-wrapper { height: 400px; position: relative; }
        
        /* CSV Anomalies */
        .csv-anomalies { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.08); margin-bottom: 30px; }
        .csv-anomaly-item { padding: 15px; border-left: 4px solid #e74c3c; margin-bottom: 10px; background: #fdf2f2; border-radius: 5px; }
        
        /* Analysis History */
        .history-section { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.08); margin-bottom: 30px; }
        .history-table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        .history-table th, .history-table td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        .history-table th { background-color: #f8f9fa; font-weight: bold; }
        .history-table tr:hover { background-color: #f5f5f5; }
        .history-table button { background: #3498db; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer; }
        .history-table button:hover { background: #2980b9; }
        
        /* Analysis Details */
        .analysis-details { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.08); }
        .details-header { border-bottom: 2px solid #3498db; padding-bottom: 10px; margin-bottom: 20px; }
        .detail-item { padding: 10px; border-bottom: 1px solid #eee; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>System Monitor Dashboard</h1>
            <div id="status">Status: <span class="status-indicator status-initializing"></span> <span id="status-text">Initializing...</span></div>
        </div>

        <!-- CSV Upload Section -->
        <div class="csv-upload">
            <h2>Upload CSV Data for Analysis</h2>
            <div class="upload-form">
                <input type="file" id="csv-file" accept=".csv">
                <button onclick="uploadCSV()">Analyze CSV</button>
            </div>
            <div id="upload-status"></div>
        </div>

        <!-- Analysis History Section -->
        <div class="history-section">
            <h2>Analysis History</h2>
            <button onclick="loadAnalysisHistory()">Refresh History</button>
            <div id="history-container">
                <p>Loading analysis history...</p>
            </div>
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

        <!-- Real-time Chart -->
        <div class="chart-container">
            <h2>Real-time System Metrics (Last 30 samples)</h2>
            <div class="chart-wrapper">
                <canvas id="metricsChart"></canvas>
            </div>
        </div>

        <!-- CSV Data Chart -->
        <div class="csv-chart-container">
            <h2>CSV Data Analysis</h2>
            <div class="chart-wrapper">
                <canvas id="csvChart"></canvas>
            </div>
        </div>

        <!-- CSV Anomalies -->
        <div class="csv-anomalies">
            <h2>Detected CSV Anomalies</h2>
            <div id="csv-anomalies-container">
                <p>No CSV data analyzed yet.</p>
            </div>
        </div>

        <!-- Analysis Details (Hidden by default) -->
        <div class="analysis-details" id="analysis-details-section" style="display: none;">
            <div class="details-header">
                <h2 id="analysis-details-title">Analysis Details</h2>
            </div>
            <div id="analysis-details-content"></div>
        </div>

        <!-- Real-time Anomalies -->
        <div class="anomalies-list">
            <h2>Real-time Critical Anomalies Only (Score < -0.1)</h2>
            <div id="anomalies-container">
                <p>No critical anomalies detected. System appears normal.</p>
            </div>
        </div>
    </div>

    <script>
        const socket = io();
        let metricsChart = null;
        let csvChart = null;
        let chartInitialized = false;
        let csvChartInitialized = false;

        // Initialize real-time chart
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
                const timeStr = new Date(item.timestamp * 1000).toLocaleTimeString();
                labels.push(timeStr);
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
                    maintainAspectRatio: false,
                    animation: false,
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
                                maxTicksLimit: 8
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

        // Initialize CSV chart
        function initCSVChart(csvData) {
            const ctx = document.getElementById('csvChart').getContext('2d');
            
            // Prepare chart data
            const labels = [];
            const cpuData = [];
            const memoryData = [];
            const diskData = [];
            const networkData = [];
            
            // Process CSV data
            for (let i = 0; i < csvData.length; i++) {
                const item = csvData[i];
                const timeStr = item.display_time || (item.timestamp ? new Date(item.timestamp * 1000).toLocaleTimeString() : i);
                labels.push(timeStr);
                cpuData.push(item.cpu_percent || 0);
                memoryData.push(item.memory_percent || 0);
                diskData.push(item.disk_read_mb || 0);
                networkData.push(item.network_sent_mb || 0);
            }
            
            csvChart = new Chart(ctx, {
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
                    maintainAspectRatio: false,
                    animation: false,
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
                                maxTicksLimit: 15
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
            
            csvChartInitialized = true;
        }

        // Update real-time chart with new data point
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
            metricsChart.update('none');
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

        // Upload CSV file
        function uploadCSV() {
            const fileInput = document.getElementById('csv-file');
            const file = fileInput.files[0];
            
            if (!file) {
                showUploadStatus('Please select a CSV file first.', 'error');
                return;
            }
            
            const formData = new FormData();
            formData.append('file', file);
            
            showUploadStatus('Uploading and analyzing CSV file...', 'info');
            
            fetch('/api/upload-csv', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    showUploadStatus('Error: ' + data.error, 'error');
                } else {
                    showUploadStatus('Success! Processed ' + data.total_records + ' records. Found ' + data.anomalies_found + ' anomalies (' + data.anomaly_rate.toFixed(2) + '%).', 'success');
                    // Refresh CSV data and anomalies
                    refreshCSVData();
                    // Refresh analysis history
                    loadAnalysisHistory();
                }
            })
            .catch(error => {
                showUploadStatus('Error uploading file: ' + error.message, 'error');
            });
        }

        // Show upload status
        function showUploadStatus(message, type) {
            const statusDiv = document.getElementById('upload-status');
            statusDiv.textContent = message;
            statusDiv.className = 'upload-status';
            if (type === 'success') {
                statusDiv.classList.add('upload-success');
            } else if (type === 'error') {
                statusDiv.classList.add('upload-error');
            }
        }

        // Refresh CSV data
        function refreshCSVData() {
            // Fetch CSV data for chart
            fetch('/api/csv-data')
                .then(response => response.json())
                .then(data => {
                    if (data.length > 0) {
                        if (csvChartInitialized) {
                            csvChart.destroy();
                        }
                        initCSVChart(data);
                    }
                })
                .catch(console.error);
            
            // Fetch CSV anomalies
            fetch('/api/csv-anomalies')
                .then(response => response.json())
                .then(anomalies => {
                    const container = document.getElementById('csv-anomalies-container');
                    if (anomalies.length > 0) {
                        container.innerHTML = '';
                        // Show only top 20 anomalies
                        const topAnomalies = anomalies.slice(0, 20);
                        topAnomalies.forEach(anomaly => {
                            const anomalyDiv = document.createElement('div');
                            anomalyDiv.className = 'csv-anomaly-item';
                            const timestamp = new Date(anomaly.timestamp * 1000).toLocaleString();
                            let severityFactorsHtml = '';
                            if (anomaly.severity_factors && anomaly.severity_factors.length > 0) {
                                severityFactorsHtml = '<div class="severity-factors"><strong>Severity Factors:</strong> ' + anomaly.severity_factors.join(', ') + '</div>';
                            }
                            anomalyDiv.innerHTML = 
                                '<div><strong>Row ' + anomaly.index + '</strong> - ' + timestamp + '</div>' +
                                '<div>Anomaly Score: <span class="anomaly-score">' + anomaly.anomaly_score.toFixed(3) + '</span></div>' +
                                '<div class="anomaly-reason"><strong>Reason:</strong> ' + anomaly.reason + '</div>' +
                                severityFactorsHtml +
                                '<div>' +
                                '<span style="color: #3498db;">CPU: ' + anomaly.metrics.cpu_percent.toFixed(1) + '%</span> | ' +
                                '<span style="color: #9b59b6;">Memory: ' + anomaly.metrics.memory_percent.toFixed(1) + '%</span> | ' +
                                '<span style="color: #2ecc71;">Disk: ' + anomaly.metrics.disk_read_mb.toFixed(2) + ' MB/s</span> | ' +
                                '<span style="color: #e74c3c;">Network: ' + anomaly.metrics.network_sent_mb.toFixed(2) + ' MB/s</span>' +
                                '</div>';
                            container.appendChild(anomalyDiv);
                        });
                    } else {
                        container.innerHTML = '<p>No anomalies detected in CSV data.</p>';
                    }
                })
                .catch(console.error);
        }

        // Load analysis history
        function loadAnalysisHistory() {
            fetch('/api/analysis-history')
                .then(response => response.json())
                .then(history => {
                    const container = document.getElementById('history-container');
                    if (history.length > 0) {
                        let html = '<table class="history-table">';
                        html += '<thead><tr><th>File Name</th><th>Date</th><th>Records</th><th>Anomalies</th><th>Rate</th><th>Actions</th></tr></thead>';
                        html += '<tbody>';
                        
                        history.forEach(item => {
                            html += '<tr>';
                            html += '<td>' + item.filename + '</td>';
                            html += '<td>' + new Date(item.upload_time).toLocaleString() + '</td>';
                            html += '<td>' + item.total_records + '</td>';
                            html += '<td>' + item.anomalies_found + '</td>';
                            html += '<td>' + item.anomaly_rate.toFixed(2) + '%</td>';
                            html += '<td><button onclick="viewAnalysisDetails(' + item.id + ')">View Details</button></td>';
                            html += '</tr>';
                        });
                        
                        html += '</tbody></table>';
                        container.innerHTML = html;
                    } else {
                        container.innerHTML = '<p>No analysis history found.</p>';
                    }
                })
                .catch(error => {
                    console.error('Error loading history:', error);
                    document.getElementById('history-container').innerHTML = '<p>Error loading analysis history.</p>';
                });
        }

        // View analysis details
        function viewAnalysisDetails(analysisId) {
            fetch('/api/analysis-details/' + analysisId)
                .then(response => response.json())
                .then(details => {
                    if (details.error) {
                        alert('Error: ' + details.error);
                        return;
                    }
                    
                    const section = document.getElementById('analysis-details-section');
                    const title = document.getElementById('analysis-details-title');
                    const content = document.getElementById('analysis-details-content');
                    
                    // Set title
                    title.textContent = 'Analysis Details: ' + details.summary.filename;
                    
                    // Set content
                    let html = '<div style="margin-bottom: 20px;">';
                    html += '<strong>Upload Time:</strong> ' + new Date(details.summary.upload_time).toLocaleString() + '<br>';
                    html += '<strong>Total Records:</strong> ' + details.summary.total_records + '<br>';
                    html += '<strong>Anomalies Found:</strong> ' + details.summary.anomalies_found + '<br>';
                    html += '<strong>Anomaly Rate:</strong> ' + details.summary.anomaly_rate.toFixed(2) + '%<br>';
                    html += '</div>';
                    
                    if (details.anomalies.length > 0) {
                        html += '<h3>Detected Anomalies (' + details.anomalies.length + ')</h3>';
                        
                        // Show top 50 anomalies
                        const topAnomalies = details.anomalies.slice(0, 50);
                        topAnomalies.forEach(anomaly => {
                            html += '<div class="detail-item">';
                            html += '<div><strong>Row ' + anomaly.index + '</strong> - Score: <span class="anomaly-score">' + anomaly.anomaly_score.toFixed(3) + '</span></div>';
                            html += '<div class="anomaly-reason"><strong>Reason:</strong> ' + anomaly.reason + '</div>';
                            if (anomaly.severity_factors && anomaly.severity_factors.length > 0) {
                                html += '<div class="severity-factors"><strong>Severity Factors:</strong> ' + anomaly.severity_factors.join(', ') + '</div>';
                            }
                            html += '<div>';
                            html += '<span style="color: #3498db;">CPU: ' + (anomaly.metrics.cpu_percent ? parseFloat(anomaly.metrics.cpu_percent).toFixed(1) : 'N/A') + '%</span> | ';
                            html += '<span style="color: #9b59b6;">Memory: ' + (anomaly.metrics.memory_percent ? parseFloat(anomaly.metrics.memory_percent).toFixed(1) : 'N/A') + '%</span> | ';
                            html += '<span style="color: #2ecc71;">Disk: ' + (anomaly.metrics.disk_read_mb ? parseFloat(anomaly.metrics.disk_read_mb).toFixed(2) : 'N/A') + ' MB/s</span> | ';
                            html += '<span style="color: #e74c3c;">Network: ' + (anomaly.metrics.network_sent_mb ? parseFloat(anomaly.metrics.network_sent_mb).toFixed(2) : 'N/A') + ' MB/s</span>';
                            html += '</div>';
                            html += '</div>';
                        });
                    } else {
                        html += '<p>No anomalies detected in this analysis.</p>';
                    }
                    
                    content.innerHTML = html;
                    section.style.display = 'block';
                    
                    // Scroll to details section
                    section.scrollIntoView({ behavior: 'smooth' });
                })
                .catch(error => {
                    console.error('Error loading analysis details:', error);
                    alert('Error loading analysis details.');
                });
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
            
            anomalyDiv.className = 'anomaly-item ' + severityClass;
            
            let severityFactorsHtml = '';
            if (data.severity_factors && data.severity_factors.length > 0) {
                severityFactorsHtml = '<div class="severity-factors"><strong>Severity Factors:</strong> ' + data.severity_factors.join(', ') + '</div>';
            }
            
            anomalyDiv.innerHTML = 
                '<div><strong>' + new Date(data.timestamp).toLocaleString() + '</strong> <span class="timestamp">(' + new Date(data.timestamp).toLocaleTimeString() + ')</span></div>' +
                '<div>Severity: <strong>' + severityText + '</strong> | Anomaly Score: <span class="anomaly-score">' + data.anomaly_score.toFixed(3) + '</span></div>' +
                '<div class="anomaly-reason"><strong>Reason:</strong> ' + data.reason + '</div>' +
                severityFactorsHtml +
                '<div>' +
                '<span style="color: #3498db;">CPU: ' + data.metrics.cpu_percent.toFixed(1) + '%</span> | ' +
                '<span style="color: #9b59b6;">Memory: ' + data.metrics.memory_percent.toFixed(1) + '%</span> | ' +
                '<span style="color: #2ecc71;">Disk: ' + data.metrics.disk_read_mb.toFixed(2) + ' MB/s</span> | ' +
                '<span style="color: #e74c3c;">Network: ' + data.metrics.network_sent_mb.toFixed(2) + ' MB/s</span>' +
                '</div>';
            container.insertBefore(anomalyDiv, container.firstChild);
            
            // Remove old anomalies if more than 15
            while (container.children.length > 15) {
                container.removeChild(container.lastChild);
            }
        });

        // Fetch initial data
        Promise.all([
            fetch('/api/status').then(response => response.json()),
            fetch('/api/chart-data').then(response => response.json()),
            fetch('/api/csv-data').then(response => response.json())
        ]).then(function(results) {
            var statusData = results[0];
            var chartData = results[1];
            var csvData = results[2];
            
            updateStatus(statusData.status);
            updateStats(statusData);
            
            // Initialize real-time chart with historical data
            if (chartData.length > 0) {
                initChart(chartData);
            } else {
                // Initialize with empty chart
                initChart([]);
            }
            
            // Initialize CSV chart if data available
            if (csvData.length > 0) {
                initCSVChart(csvData);
            }
            
            // Refresh CSV anomalies
            refreshCSVData();
            
            // Load analysis history
            loadAnalysisHistory();
        }).catch(function(error) {
            console.error('Error fetching initial ', error);
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
                        
                        anomalyDiv.className = 'anomaly-item ' + severityClass;
                        const timestamp = new Date(anomaly.timestamp).toLocaleString();
                        
                        let severityFactorsHtml = '';
                        if (anomaly.severity_factors && anomaly.severity_factors.length > 0) {
                            severityFactorsHtml = '<div class="severity-factors"><strong>Severity Factors:</strong> ' + anomaly.severity_factors.join(', ') + '</div>';
                        }
                        
                        anomalyDiv.innerHTML = 
                            '<div><strong>' + timestamp + '</strong></div>' +
                            '<div>Severity: <strong>' + severityText + '</strong> | Anomaly Score: <span class="anomaly-score">' + anomaly.anomaly_score.toFixed(3) + '</span></div>' +
                            '<div class="anomaly-reason"><strong>Reason:</strong> ' + anomaly.reason + '</div>' +
                            severityFactorsHtml +
                            '<div>' +
                            '<span style="color: #3498db;">CPU: ' + anomaly.metrics.cpu_percent.toFixed(1) + '%</span> | ' +
                            '<span style="color: #9b59b6;">Memory: ' + anomaly.metrics.memory_percent.toFixed(1) + '%</span> | ' +
                            '<span style="color: #2ecc71;">Disk: ' + anomaly.metrics.disk_read_mb.toFixed(2) + ' MB/s</span> | ' +
                            '<span style="color: #e74c3c;">Network: ' + anomaly.metrics.network_sent_mb.toFixed(2) + ' MB/s</span>' +
                            '</div>';
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