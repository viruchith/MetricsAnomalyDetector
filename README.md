# System Metrics Anomaly Detector

A real-time PC hardware monitoring and anomaly detection system with a web dashboard. This tool continuously monitors CPU usage, memory usage, disk I/O, and network traffic, using machine learning to detect unusual system behavior.

## Features

- **Real-time Monitoring**: Continuously tracks system metrics every second
- **Machine Learning Detection**: Uses Isolation Forest algorithm to identify anomalies
- **Web Dashboard**: Interactive web interface for monitoring system health
- **Smart Filtering**: Only shows high-severity anomalies to reduce noise
- **Comprehensive Logging**: Detailed logs of all metrics and detected anomalies
- **Performance Optimized**: Efficient data collection and chart rendering

## System Metrics Monitored

- **CPU Usage**: Percentage of CPU utilization
- **Memory Usage**: RAM consumption percentage and available memory
- **Disk I/O**: Read/write operations in MB/s
- **Network Traffic**: Incoming/outgoing data transfer rates in MB/s

## Anomaly Detection

The system uses Isolation Forest machine learning algorithm to detect unusual patterns:

- **Severity Levels**: 
  - **Critical** (Score < -0.7): Very unusual system behavior
  - **High** (Score -0.5 to -0.7): Significant deviations from normal
- **Smart Thresholds**: Learns your system's normal behavior patterns
- **Real-time Alerts**: Instant notifications when anomalies are detected

## Installation

### Prerequisites

- Python 3.6+
- pip (Python package installer)

### Required Packages

```bash
pip install psutil scikit-learn pandas numpy flask flask-socketio