# Metrics Anomaly Detection System 🔍

A comprehensive real-time system monitoring and anomaly detection suite powered by machine learning. Monitor your system's health, detect unusual behavior patterns, and visualize performance metrics through an interactive web dashboard.

![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![ML](https://img.shields.io/badge/ML-Isolation%20Forest-orange.svg)

## 🌟 Overview

This project provides a complete solution for monitoring system performance and detecting anomalies in real-time. Whether you're monitoring a single machine, analyzing historical data, or processing metrics from virtual machines, this suite has you covered.

### Key Capabilities
- **Real-time System Monitoring** with live web dashboard
- **Machine Learning Anomaly Detection** using Isolation Forest
- **Historical Data Analysis** from CSV files
- **Interactive Visualizations** with real-time charts
- **Comprehensive Logging** and alert management

## 🚀 Features

### 📊 Real-time Monitoring
- **Live Metrics Collection**: CPU, Memory, Disk I/O, Network traffic
- **WebSocket Updates**: Real-time dashboard without page refresh
- **Smart Buffering**: Efficient data management with rolling windows
- **Auto-training**: Automatic baseline establishment

### 🧠 Machine Learning
- **Isolation Forest Algorithm**: Unsupervised anomaly detection
- **Adaptive Learning**: Continuous model retraining
- **Multi-severity Classification**: Critical, High, Medium alerts
- **Statistical Analysis**: Z-score based threshold detection

### 🖥️ Web Dashboard
- **Interactive Charts**: Real-time metrics visualization
- **Anomaly Alerts**: Live notifications with detailed context
- **Performance Metrics**: System health indicators
- **Responsive Design**: Works on desktop and mobile

### 📁 Data Processing
- **CSV Analysis**: Batch processing of historical data
- **Multiple Input Formats**: Flexible data ingestion
- **Export Capabilities**: Results in CSV/JSON formats

## 🛠️ Installation

### Prerequisites
- Python 3.7 or higher
- pip package manager
- Modern web browser

### Dependencies
```bash
# Core dependencies
pip install psutil scikit-learn pandas numpy flask flask-socketio

# Optional: For enhanced visualization
pip install matplotlib seaborn
```

### Quick Setup
```bash
# Clone the repository
git clone https://github.com/viruchith/MetricsAnomalyDetector.git
cd MetricsAnomalyDetector

# Install dependencies
pip install -r requirements.txt

# Run the main application
python anomaly_detector_csv_realtime_dashboard.py
```

## 🎯 Quick Start

### 1. Real-time System Monitoring
Start monitoring your system with the web dashboard:

```bash
python anomaly_detector_csv_realtime_dashboard.py
```

**Access Dashboard**: Open http://localhost:5000 in your browser

**What happens:**
- 60 seconds of baseline data collection
- Automatic model training
- Real-time anomaly detection
- Live web dashboard updates

### 2. Analyze Historical Data
Process CSV files for anomaly detection:

```bash
python anomaly_detector_csv_realtime_dashboard.py --csv-file sample_metrics2k.csv --output-file results.csv
```

**Features:**
- Batch processing of historical metrics
- Detailed anomaly analysis
- Export results to CSV
- Statistical summaries

### 4. Data Generation
Create test datasets for experimentation:

```bash
python datagen.py
```

**Generates:**
- Realistic system metrics
- Normal and anomalous patterns
- Configurable data size
- CSV output format

## 📁 Project Structure

```
metrics-anomaly-detection/
│
├── 🎯 Core Applications
│   ├── anomaly_detector_csv_realtime_dashboard.py  # Main application with dashboard
│   ├── anomaly_detector_dashboard.py              # Alternative dashboard version
│   └── datagen.py                                 # Sample data generator
│
├── 🌐 Web Interface
│   └── templates/
│       └── dashboard.html                          # Interactive web dashboard
│
├── 📊 Data Files
│   ├── sample_metrics2k.csv                       # Sample dataset (2000 records)
│   └── requirements.txt                           # Python dependencies
│
├── 📝 Logs & Output
│   └── logs/                                       # Auto-generated logs
│       ├── system_monitor.log                     # Main application log
│       ├── csv_analysis.log                       # CSV processing log
│       ├── metrics_history.csv                    # Historical metrics data
│       ├── metrics_data.csv                       # Processed metrics
│       └── anomalies.json                         # Detected anomalies
│
├── 📚 Documentation
│   ├── README.md                                   # This file
│   └── technical.md                                # Technical documentation
│
├── ⚙️ Configuration
│   ├── .gitignore                                  # Git ignore rules
│   └── venv/                                       # Python virtual environment
│
└── 🔧 Version Control
    └── .git/                                       # Git repository data
```

## 📊 Monitored Metrics

| Metric | Description | Collection Rate | Units |
|--------|-------------|----------------|-------|
| **CPU Usage** | Processor utilization percentage | 1 second | % |
| **Memory Usage** | RAM consumption and availability | 1 second | % / GB |
| **Disk I/O** | Read/write operations | 1 second | MB/s |
| **Network Traffic** | Data transmission rates | 1 second | MB/s |
| **CPU Frequency** | Current processor speed | 1 second | MHz |

## 🔍 Anomaly Detection

### Detection Methods

#### 1. **Machine Learning (Primary)**
- **Algorithm**: Isolation Forest
- **Type**: Unsupervised learning
- **Advantage**: No labeled data required
- **Sensitivity**: Configurable contamination parameter

#### 2. **Statistical Analysis**
- **Method**: Z-score calculation
- **Threshold**: Configurable standard deviations
- **Context**: Historical data comparison
- **Speed**: Real-time computation

#### 3. **Rule-based Detection**
- **Critical Thresholds**: Hard limits (e.g., CPU > 95%)
- **Pattern Recognition**: Unusual metric combinations
- **Task Failures**: Direct failure indicators
- **Custom Rules**: User-defined conditions

### Severity Levels

| Level | Score Range | Color | Description |
|-------|-------------|-------|-------------|
| 🔴 **Critical** | < -0.7 | Red | Extremely unusual behavior requiring immediate attention |
| 🟡 **High** | -0.7 to -0.5 | Orange | Significant deviations from normal patterns |
| 🟢 **Medium** | -0.5 to -0.3 | Yellow | Minor deviations worth monitoring |

## ⚙️ Configuration

### Command Line Options

```bash
python anomaly_detector_csv_realtime_dashboard.py [OPTIONS]

Options:
  --csv-file PATH         Process historical CSV data
  --output-file PATH      Save analysis results
  --contamination FLOAT   Expected anomaly rate (0.0-1.0) [default: 0.05]
  --window-size INT       Training window size in seconds [default: 120]
```

### Examples

```bash
# Real-time monitoring with default settings
python anomaly_detector_csv_realtime_dashboard.py

# Higher sensitivity monitoring
python anomaly_detector_csv_realtime_dashboard.py --contamination 0.1

# Analyze historical data
python anomaly_detector_csv_realtime_dashboard.py \
    --csv-file historical_data.csv \
    --output-file analysis_results.csv \
    --contamination 0.05

# Quick training for testing
python anomaly_detector_csv_realtime_dashboard.py --window-size 30
```

## 🌐 Web Dashboard

### Features Overview

#### **Real-time Metrics Display**
- Live updating charts (30-point rolling window)
- Current metric values with progress bars
- System status indicators
- Performance statistics

#### **Anomaly Management**
- Real-time anomaly notifications
- Severity-based color coding
- Detailed anomaly information
- Historical anomaly list (last 15)

#### **System Information**
- Data points collected
- Total anomalies detected
- System uptime
- Model training status

### Dashboard Sections

1. **Header**: System status and monitoring state
2. **Metrics Grid**: Current CPU, memory, disk, network values
3. **Statistics**: Data points, anomalies, uptime counters
4. **Charts**: Real-time line charts for all metrics
5. **Anomalies**: Live feed of detected anomalies

## 📈 Output Formats

### Log Files

#### `system_monitor.log`
```
2025-07-30 10:30:00 - INFO - Starting real-time anomaly detection system
2025-07-30 10:30:01 - WARNING - ANOMALY #1 DETECTED at 2025-07-30 10:30:01
2025-07-30 10:30:01 - WARNING -   Anomaly Score: -0.756
```

#### `metrics_history.csv`
```csv
timestamp,cpu_percent,cpu_frequency,memory_percent,memory_available_gb,disk_read_mb,disk_write_mb,network_sent_mb,network_recv_mb,is_anomaly,anomaly_score
2025-07-30 10:30:00,15.2,2400.0,45.6,8.5,2.1,1.3,0.8,0.5,False,
2025-07-30 10:30:01,85.7,2800.0,78.9,3.2,150.3,45.7,45.2,12.1,True,-0.756
```

#### `anomalies.json`
```json
[
  {
    "timestamp": "2025-07-30T10:30:01",
    "anomaly_score": -0.756,
    "metrics": {
      "cpu_percent": 85.7,
      "memory_percent": 78.9,
      "disk_read_mb": 150.3,
      "network_sent_mb": 45.2
    },
    "reason": "High CPU usage detected | High memory consumption",
    "severity_factors": ["CPU: 85.7%", "Memory: 78.9%"]
  }
]
```

## 🔧 Advanced Usage

### Custom Thresholds

Modify detection sensitivity in your code:

```python
# Custom detector configuration
detector = RealTimeAnomalyDetector(
    window_size=180,        # 3-minute training window
    contamination=0.03,     # Expect 3% anomalies
    log_file="custom.log"   # Custom log file
)

# Custom severity thresholds
HIGH_SEVERITY_THRESHOLD = -0.6
CRITICAL_SEVERITY_THRESHOLD = -0.8
```

### CSV Data Requirements

Your CSV files should include these columns:
- `timestamp` (datetime or Unix timestamp)
- `cpu_percent` (0-100)
- `memory_percent` (0-100)
- `disk_read_mb` (MB/s)
- `network_sent_mb` (MB/s)

Optional columns:
- `disk_write_mb`, `network_recv_mb`, `cpu_frequency`

## 🚨 Common Anomaly Patterns

### Performance Issues
- **CPU Spikes**: Sudden high processor usage
- **Memory Leaks**: Gradual memory consumption increase
- **Disk Bottlenecks**: Sustained high I/O operations
- **Network Flooding**: Unusual traffic patterns

### System Behaviors
- **Resource Contention**: Multiple metrics simultaneously high
- **Periodic Patterns**: Unusual timing of high usage
- **Cascade Effects**: One metric triggering others
- **Background Processes**: Unexpected system activity

## 🐛 Troubleshooting

### Common Issues

#### **Dashboard Not Loading**
```bash
# Check if Flask is installed
pip show flask flask-socketio

# Check port availability
netstat -an | findstr :5000

# Try alternative port
python anomaly_detector_csv_realtime_dashboard.py --port 8080
```

#### **No Anomalies Detected**
- Increase sensitivity: `--contamination 0.1`
- Check if system is actually under load
- Verify training window is appropriate
- Review log files for errors

#### **Too Many False Positives**
- Decrease sensitivity: `--contamination 0.02`
- Increase training window: `--window-size 300`
- Check for consistent background processes
- Review threshold configurations

#### **CSV Processing Errors**
- Verify column names match requirements
- Check for missing data values
- Ensure timestamp format consistency
- Validate numeric data types

### Log Analysis

Check log files for diagnostic information:
```bash
# View recent logs
tail -f logs/system_monitor.log

# Check for errors
grep ERROR logs/system_monitor.log

# Review anomaly patterns
cat logs/anomalies.json | jq '.[].reason' | sort | uniq -c
```

## 📊 Performance Considerations

### System Impact
- **CPU Overhead**: ~1-2% during monitoring
- **Memory Usage**: ~50-100MB typical
- **Disk I/O**: Minimal logging impact
- **Network**: WebSocket updates only

### Optimization Strategies

#### **For Real-time Monitoring**
```python
# Reduce chart update frequency
chart_counter_threshold = 5  # Update every 5 seconds

# Limit anomaly history
anomalies = deque(maxlen=50)  # Reduce from 100

# Optimize logging
log_level = logging.WARNING  # Reduce log verbosity
```

#### **For Large Datasets**
```python
# Batch processing mode
detector.detect_anomalies_from_csv(
    csv_file_path="large_dataset.csv",
    batch_size=1000  # Process in chunks
)
```

## 🤝 Contributing

### Development Setup

1. **Fork the Repository**
2. **Create Feature Branch**: `git checkout -b feature/amazing-feature`
3. **Install Dev Dependencies**: `pip install -r requirements-dev.txt`
4. **Make Changes**
5. **Test Thoroughly**
6. **Submit Pull Request**

### Code Guidelines

- **PEP 8**: Follow Python style guidelines
- **Documentation**: Add docstrings for new functions
- **Testing**: Include tests for new features
- **Logging**: Use appropriate log levels
- **Error Handling**: Implement proper exception handling

### Areas for Contribution

- **New Metrics**: Additional system metrics collection
- **Visualization**: Enhanced dashboard features
- **Algorithms**: Alternative anomaly detection methods
- **Integration**: Support for additional data sources
- **Documentation**: Improved guides and examples

## 📚 Technical Details

### Machine Learning Pipeline

1. **Data Collection**: Real-time metric gathering via psutil
2. **Preprocessing**: Normalization and feature selection
3. **Training**: Isolation Forest model fitting
4. **Detection**: Real-time anomaly scoring
5. **Classification**: Severity level assignment
6. **Alerting**: Dashboard notifications and logging

### Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Data Sources  │───▶│  Anomaly Engine  │───▶│  Web Dashboard  │
│                 │    │                  │    │                 │
│ • System Metrics│    │ • ML Detection   │    │ • Real-time UI  │
│ • CSV Files     │    │ • Statistical    │    │ • Alerts        │
│ • Data Files    │    │ • Rule-based     │    │ • Charts        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Data Storage  │
                       │                 │
                       │ • Logs          │
                       │ • Metrics CSV   │
                       │ • Anomalies JSON│
                       └─────────────────┘
```

## 📄 License

This project is released under the MIT License. See LICENSE file for details.

## 🔗 Resources

### Related Tools
- **Grafana**: Enterprise monitoring dashboards
- **Prometheus**: Metrics collection and alerting
- **ELK Stack**: Log analysis and visualization
- **Nagios**: Network monitoring solutions

### Learning Resources
- **Isolation Forest**: [Original Paper](https://cs.nju.edu.cn/zhouzh/zhouzh.files/publication/icdm08b.pdf)
- **Anomaly Detection**: [Comprehensive Guide](https://scikit-learn.org/stable/modules/outlier_detection.html)
- **Flask-SocketIO**: [Documentation](https://flask-socketio.readthedocs.io/)

## 📞 Support

### Getting Help

1. **Documentation**: Check this README and technical.md
2. **Issues**: Search existing GitHub issues
3. **Discussions**: Join community discussions
4. **Bug Reports**: Create detailed issue reports

### Contact Information

- **Repository**: https://github.com/viruchith/MetricsAnomalyDetector
- **Issues**: https://github.com/viruchith/MetricsAnomalyDetector/issues
- **Discussions**: https://github.com/viruchith/MetricsAnomalyDetector/discussions

---

**Start monitoring your system's health today!** 🚀

*This project aims to make system monitoring and anomaly detection accessible to everyone, from individual developers to enterprise teams.*