# System Metrics Anomaly Detection Suite

A comprehensive real-time system monitoring and anomaly detection suite with machine learning capabilities and interactive web dashboards. This project provides multiple tools for monitoring system performance, detecting anomalies in real-time, and analyzing historical data patterns.

## 🚀 Features

### Real-time Monitoring
- **Live System Metrics**: Continuously tracks CPU, memory, disk I/O, and network traffic
- **Interactive Web Dashboard**: Real-time visualization with Socket.IO updates
- **Smart Anomaly Detection**: Machine learning-powered unusual behavior detection
- **Multi-severity Alerts**: Critical, high, and medium severity classifications

### Data Analysis & Processing
- **CSV Batch Processing**: Analyze historical metrics data from CSV files
- **RabbitMQ Integration**: Queue-based metrics processing for distributed systems
- **VM Performance Monitoring**: Specialized virtual machine metrics analysis
- **Comprehensive Logging**: Detailed system logs and anomaly records

### Machine Learning
- **Isolation Forest Algorithm**: Unsupervised anomaly detection
- **Adaptive Learning**: Continuous model retraining with new data
- **Statistical Analysis**: Z-score based threshold detection
- **Pattern Recognition**: Identifies unusual metric combinations

## 📊 System Metrics Monitored

| Metric | Description | Update Frequency |
|--------|-------------|-----------------|
| **CPU Usage** | Processor utilization percentage | 1 second |
| **Memory Usage** | RAM consumption and availability | 1 second |
| **Disk I/O** | Read/write operations (MB/s) | 1 second |
| **Network Traffic** | Sent/received data rates (MB/s) | 1 second |
| **CPU Frequency** | Current processor frequency | 1 second |

## 🔍 Anomaly Detection

### Severity Levels
- **🔴 Critical** (Score < -0.7): Extremely unusual system behavior requiring immediate attention
- **🟡 High** (Score -0.5 to -0.7): Significant deviations from normal patterns
- **🟢 Medium** (Score -0.3 to -0.5): Minor deviations worth monitoring

### Detection Methods
1. **Statistical Analysis**: Z-score based threshold detection
2. **Machine Learning**: Isolation Forest unsupervised learning
3. **Rule-based**: Critical threshold violations
4. **Pattern Recognition**: Unusual metric combinations

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.7+
- pip (Python package installer)
- Modern web browser (for dashboard)

### Required Packages
```

### Optional Dependencies
```bash
# For RabbitMQ integration
pip install pika

# For enhanced data visualization
pip install matplotlib seaborn
```

## 🚀 Quick Start

### 1. Real-time System Monitoring
Launch the main dashboard for live system monitoring:
```bash
python anomaly_detector_csv_realtime_dashboard.py
```
- **Web Dashboard**: http://localhost:5000
- **Auto-training**: 60 seconds baseline data collection
- **Real-time Updates**: Live metrics via WebSocket

### 2. CSV Data Analysis
Analyze historical data from CSV files:
```bash
python anomaly_detector_csv_realtime_dashboard.py --csv-file sample_metrics2k.csv --output-file results.csv
```

### 3. VM Metrics Processing
Monitor virtual machine performance:
```bash
python anomaly_detection.py
```

### 4. Generate Sample Data
Create test datasets for development:
```bash
python datagen.py
```

## 📁 Project Structure

```
metrics-anomaly-detection/
├── 📊 Core Components
│   ├── anomaly_detector_csv_realtime_dashboard.py    # Main application
│   ├── anomaly_detection.py                         # VM anomaly detection
│   ├── realtime_anomaly_detector.py                 # Real-time detector
│   └── realtime_anomaly_detector2.py               # Enhanced version
├── 🌐 Dashboard Versions
│   ├── anomaly_detector_dashboard.py                # Basic dashboard
│   └── anomaly_detector_dashboard2.py              # Advanced dashboard
├── 🔧 Utilities
│   ├── datagen.py                                   # Sample data generator
│   ├── metrics_producer.py                         # RabbitMQ producer
│   └── clean.py                                     # Data cleaning utility
├── 📂 Data & Logs
│   ├── logs/                                        # System logs
│   ├── templates/                                   # HTML templates
│   ├── sample_metrics2k.csv                        # Sample dataset
│   └── vmCloud_data.csv                           # VM dataset
└── 📚 Documentation
    ├── README.md                                    # This file
    └── technical.md                                 # Technical details
```

## 🖥️ Web Dashboard Features

### Real-time Metrics Display
- **Live Charts**: 30-point rolling window with Chart.js
- **Metric Cards**: Current CPU, memory, disk, and network usage
- **Status Indicators**: System health at a glance
- **Progress Bars**: Visual usage indicators

### Anomaly Alerts
- **Real-time Notifications**: Instant anomaly alerts
- **Severity Classification**: Color-coded alert levels
- **Detailed Information**: Metrics context and reasoning
- **Historical View**: Recent anomaly history

### Performance Statistics
- **Data Points**: Total metrics collected
- **Anomaly Count**: Total anomalies detected
- **System Uptime**: Monitoring duration
- **Training Status**: Model readiness indicator

## 🔧 Configuration Options

### Command Line Arguments
```bash
# Basic usage
python anomaly_detector_csv_realtime_dashboard.py

# Custom parameters
python anomaly_detector_csv_realtime_dashboard.py \
    --contamination 0.05 \
    --window-size 120 \
    --csv-file data.csv \
    --output-file results.csv
```

### Parameters
| Parameter | Default | Description |
|-----------|---------|-------------|
| `--contamination` | 0.05 | Expected anomaly rate (0.0-1.0) |
| `--window-size` | 120 | Training window size in seconds |
| `--csv-file` | None | CSV file for batch processing |
| `--output-file` | None | Output file for results |

## 📊 Output & Logging

### Log Files (in `logs/` directory)
- **`system_monitor.log`**: Main application logs
- **`metrics_history.csv`**: Complete metrics timeline
- **`anomalies.json`**: Detailed anomaly records
- **`csv_analysis.log`**: CSV processing logs

### CSV Output Format
```csv
timestamp,cpu_percent,memory_percent,disk_read_mb,network_sent_mb,is_anomaly,anomaly_score
2025-07-30 10:30:00,15.2,45.6,2.1,0.8,False,0.123
2025-07-30 10:30:01,85.7,78.9,150.3,45.2,True,-0.756
```

## 🔬 Advanced Usage

### RabbitMQ Integration
Set up message queue processing for distributed monitoring:

1. **Install RabbitMQ Server**
2. **Start Producer**:
   ```bash
   python metrics_producer.py
   ```
3. **Process Messages**:
   ```bash
   python anomaly_detection.py
   ```

### Custom Threshold Configuration
Modify detection sensitivity in the code:
```python
# In anomaly_detector_csv_realtime_dashboard.py
detector = RealTimeAnomalyDetector(
    contamination=0.05,     # Expected anomaly rate
    window_size=120,        # Training window
    log_file="custom.log"   # Custom log file
)
```

## 🧠 Machine Learning Details

### Isolation Forest Algorithm
- **Unsupervised Learning**: No labeled training data required
- **Outlier Detection**: Identifies data points that deviate from normal patterns
- **Ensemble Method**: Multiple decision trees for robust detection
- **Contamination Parameter**: Controls expected anomaly percentage

### Feature Engineering
The system uses these normalized features:
- CPU utilization percentage
- Memory usage percentage  
- Disk I/O rates (MB/s)
- Network traffic rates (MB/s)
- CPU frequency (MHz)

### Model Training
- **Initial Training**: 60 seconds of baseline data
- **Continuous Learning**: Periodic retraining every 5 minutes
- **Adaptive Thresholds**: Automatically adjusts to system patterns
- **Performance Optimization**: Efficient buffer management

## 🚨 Anomaly Types Detected

### Performance Anomalies
- **High CPU Usage**: Sustained >80% utilization
- **Memory Pressure**: >80% RAM consumption
- **Disk Bottlenecks**: >50 MB/s sustained I/O
- **Network Spikes**: >50 MB/s traffic bursts

### Pattern Anomalies
- **Unusual Combinations**: Atypical metric relationships
- **Temporal Patterns**: Time-based behavioral changes
- **Statistical Outliers**: Values beyond normal distribution
- **Resource Contention**: Multiple high-usage metrics

## 🔍 Troubleshooting

### Common Issues

**Dashboard not loading**
```bash
# Check Flask installation
pip install flask flask-socketio

# Verify port availability
netstat -an | findstr :5000
```

**No anomalies detected**
```bash
# Check contamination parameter (try 0.1 for more sensitivity)
python anomaly_detector_csv_realtime_dashboard.py --contamination 0.1
```

**High false positive rate**
```bash
# Reduce sensitivity
python anomaly_detector_csv_realtime_dashboard.py --contamination 0.02
```

**CSV processing errors**
- Ensure CSV has required columns: `cpu_percent`, `memory_percent`, `disk_read_mb`, `network_sent_mb`
- Check timestamp format compatibility
- Verify numeric data types

## 📈 Performance Considerations

### System Impact
- **CPU Usage**: ~1-2% overhead for monitoring
- **Memory**: ~50-100MB RAM usage
- **Disk**: Minimal I/O for logging
- **Network**: WebSocket updates only

### Optimization Tips
1. **Adjust Window Size**: Smaller windows for faster training
2. **Reduce Chart Points**: Limit dashboard data points
3. **Batch Processing**: Use CSV mode for large datasets
4. **Log Rotation**: Implement log file rotation for long runs

## 🤝 Contributing

### Development Setup
1. **Clone Repository**
2. **Install Dependencies**: `pip install -r requirements.txt`
3. **Run Tests**: Test with sample data
4. **Submit Pull Request**: Follow code style guidelines

### Code Structure
- **Main Classes**: `RealTimeAnomalyDetector`, `VMAnomalyDetector`
- **Web Framework**: Flask with Socket.IO
- **ML Library**: scikit-learn Isolation Forest
- **System Metrics**: psutil library

## 📝 License

This project is open source. Feel free to use, modify, and distribute according to your needs.

## 🔗 Related Tools

- **Grafana**: For enterprise monitoring dashboards
- **Prometheus**: For metrics collection and alerting
- **ELK Stack**: For log analysis and visualization
- **Nagios**: For network monitoring and alerting

## 📞 Support

For issues, questions, or contributions:
1. **Check Documentation**: Review this README and technical.md
2. **Search Issues**: Look for similar problems
3. **Create Issue**: Provide detailed problem description
4. **Community Support**: Share experiences and solutions

---

**Happy Monitoring!** 🔍📊bash
pip install psutil scikit-learn pandas numpy flask flask-socketio pika