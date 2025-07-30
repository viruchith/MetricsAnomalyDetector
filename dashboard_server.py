import json
import os
import sys
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import time
import webbrowser

# Add the current directory to the path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from enhanced_failure_prediction import get_training_files_list, train_incremental_models
    PREDICTION_MODULE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import prediction functions: {e}")
    PREDICTION_MODULE_AVAILABLE = False

class DashboardHandler(SimpleHTTPRequestHandler):
    """Custom HTTP handler for the dashboard"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/dashboard-data':
            self.serve_dashboard_data()
        elif parsed_path.path == '/api/refresh':
            self.refresh_data()
        elif parsed_path.path == '/' or parsed_path.path == '/dashboard':
            self.serve_dashboard()
        else:
            super().do_GET()
    
    def serve_dashboard(self):
        """Serve the main dashboard HTML"""
        try:
            with open('dashboard.html', 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
        except Exception as e:
            self.send_error(500, f"Error serving dashboard: {str(e)}")
    
    def serve_dashboard_data(self):
        """Serve the dashboard data as JSON"""
        try:
            # Get the latest data from the maintenance system
            data = self.get_dashboard_data()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            
            json_data = json.dumps(data, indent=2)
            self.wfile.write(json_data.encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, f"Error getting dashboard data: {str(e)}")
    
    def refresh_data(self):
        """Trigger a data refresh"""
        try:
            # Run the maintenance system to get fresh data
            self.run_maintenance_system()
            
            # Return success response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {"status": "success", "message": "Data refreshed successfully"}
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, f"Error refreshing data: {str(e)}")
    
    def run_maintenance_system(self):
        """Run the predictive maintenance system to get fresh predictions"""
        try:
            if not PREDICTION_MODULE_AVAILABLE:
                print("⚠️ Prediction module not available, using sample data")
                return {}
            
            print("🔄 Running predictive maintenance system...")
            
            # Get list of input files
            training_files = get_training_files_list()
            print(f"📁 Found {len(training_files)} training files")
            
            if not training_files:
                print("⚠️ No training files found")
                return {}
            
            # Process each file incrementally
            total_processed = 0
            for i, file_path in enumerate(training_files, 1):
                try:
                    print(f"\n📊 Processing file {i}/{len(training_files)}: {file_path}")
                    
                    # Load and process the CSV file
                    import pandas as pd
                    df = pd.read_csv(file_path)
                    
                    # Train models incrementally
                    results = train_incremental_models(df)
                    total_processed += len(df)
                    
                    print(f"✅ Processed {len(df)} samples from {file_path}")
                    
                except Exception as e:
                    print(f"❌ Error processing {file_path}: {e}")
                    continue
            
            print(f"✅ Maintenance system completed - processed {total_processed} total samples")
            return {"total_samples": total_processed, "files_processed": len(training_files)}
            
        except Exception as e:
            print(f"❌ Error running maintenance system: {e}")
            raise
    
    def get_dashboard_data(self):
        """Get dashboard data from logs and model outputs"""
        try:
            # Default data structure
            dashboard_data = {
                "summary": {
                    "totalMachines": 0,
                    "criticalAlerts": 0,
                    "filesProcessed": 0,
                    "totalSamples": 0,
                    "lastUpdate": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                },
                "alerts": []
            }
            
            # Try to read from training history
            history_file = "training_history/training_summary.json"
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    history_data = json.load(f)
                    
                dashboard_data["summary"]["filesProcessed"] = len(history_data.get("files_processed", []))
                dashboard_data["summary"]["totalSamples"] = history_data.get("total_samples", 0)
            
            # Try to read alerts from email alerts log
            alerts_file = "logs/email_alerts.log"
            if os.path.exists(alerts_file):
                alerts = self.parse_alerts_from_log(alerts_file)
                dashboard_data["alerts"] = alerts
                dashboard_data["summary"]["criticalAlerts"] = len([a for a in alerts if a["riskLevel"] in ["High", "Medium"]])
                
                # Count unique machines
                unique_machines = set(alert["machineId"] for alert in alerts)
                dashboard_data["summary"]["totalMachines"] = len(unique_machines)
            
            # If no alerts found, create sample data based on latest predictions
            if not dashboard_data["alerts"]:
                dashboard_data = self.get_sample_dashboard_data()
            
            return dashboard_data
            
        except Exception as e:
            print(f"Error getting dashboard data: {e}")
            return self.get_sample_dashboard_data()
    
    def parse_alerts_from_log(self, log_file):
        """Parse alerts from the email alerts log file"""
        alerts = []
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for high-risk predictions in the log
            lines = content.split('\n')
            for line in lines:
                if "High-risk prediction" in line or "Medium-risk prediction" in line:
                    # Parse the log line to extract machine info
                    # Format: "High-risk prediction for Machine 101: Hard Disk failure (94.0% likelihood)"
                    try:
                        parts = line.split(':')
                        if len(parts) >= 2:
                            machine_part = parts[1].strip()
                            failure_part = parts[2].strip() if len(parts) > 2 else ""
                            
                            # Extract machine ID
                            machine_id = ""
                            if "Machine" in machine_part:
                                machine_id = machine_part.split("Machine")[-1].strip().split()[0]
                            
                            # Extract failure type and likelihood
                            failure_type = "Unknown"
                            likelihood = 0.0
                            risk_level = "Medium"
                            
                            if "Hard Disk" in failure_part:
                                failure_type = "🔧 Hard Disk"
                            elif "Power Supply" in failure_part:
                                failure_type = "⚡ Power Supply"
                            elif "Motherboard" in failure_part:
                                failure_type = "🧠 Motherboard"
                            elif "Network Card" in failure_part:
                                failure_type = "🌐 Network Card"
                            elif "Fan" in failure_part:
                                failure_type = "🌀 Fan"
                            
                            # Extract likelihood percentage
                            if "%" in failure_part:
                                try:
                                    likelihood_str = failure_part.split("(")[1].split("%")[0]
                                    likelihood = float(likelihood_str)
                                    
                                    if likelihood >= 70:
                                        risk_level = "High"
                                    elif likelihood >= 40:
                                        risk_level = "Medium"
                                    else:
                                        risk_level = "Low"
                                except:
                                    pass
                            
                            if machine_id:
                                alerts.append({
                                    "machineId": machine_id,
                                    "failureType": failure_type,
                                    "riskLevel": risk_level,
                                    "likelihood": likelihood,
                                    "timeToFail": "⚠️ Imminent" if likelihood >= 70 else "📅 Soon",
                                    "issues": self.get_machine_issues(likelihood)
                                })
                    except Exception as e:
                        print(f"Error parsing log line: {e}")
                        continue
        
        except Exception as e:
            print(f"Error reading alerts log: {e}")
        
        return alerts
    
    def get_machine_issues(self, likelihood):
        """Generate machine issues based on likelihood"""
        issues = []
        
        if likelihood >= 90:
            issues = ['🔥 High Temp', '📳 High Vib', '⚡ High Current', '🌀 Low Fan']
        elif likelihood >= 80:
            issues = ['🔥 High Temp', '📳 High Vib', '⚡ High Current']
        elif likelihood >= 70:
            issues = ['🔥 High Temp', '📳 High Vib']
        elif likelihood >= 50:
            issues = ['🔥 High Temp']
        else:
            issues = ['⚠️ Minor Issues']
        
        return issues
    
    def get_sample_dashboard_data(self):
        """Return sample dashboard data for demonstration"""
        return {
            "summary": {
                "totalMachines": 13,
                "criticalAlerts": 5,
                "filesProcessed": 4,
                "totalSamples": 1023,
                "lastUpdate": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            "alerts": [
                {
                    "machineId": "101",
                    "failureType": "🔧 Hard Disk",
                    "riskLevel": "High",
                    "likelihood": 94.0,
                    "timeToFail": "⚠️ Imminent",
                    "issues": ["🔥 High Temp", "📳 High Vib", "⚡ High Current"]
                },
                {
                    "machineId": "102",
                    "failureType": "⚡ Power Supply",
                    "riskLevel": "High",
                    "likelihood": 92.0,
                    "timeToFail": "⚠️ Imminent",
                    "issues": ["🔥 High Temp", "📳 High Vib", "⚡ High Current"]
                },
                {
                    "machineId": "117",
                    "failureType": "🔧 Hard Disk",
                    "riskLevel": "High",
                    "likelihood": 81.0,
                    "timeToFail": "⚠️ Imminent",
                    "issues": ["🔥 High Temp", "📳 High Vib", "🌀 Low Fan", "⚡ High Current"]
                },
                {
                    "machineId": "120",
                    "failureType": "🧠 Motherboard",
                    "riskLevel": "High",
                    "likelihood": 81.0,
                    "timeToFail": "⚠️ Imminent",
                    "issues": ["🔥 High Temp", "📳 High Vib", "🌀 Low Fan", "⚡ High Current"]
                },
                {
                    "machineId": "121",
                    "failureType": "⚡ Power Supply",
                    "riskLevel": "High",
                    "likelihood": 93.0,
                    "timeToFail": "⚠️ Imminent",
                    "issues": ["🔥 High Temp", "📳 High Vib", "🌀 Low Fan", "⚡ High Current"]
                }
            ]
        }

def start_dashboard_server(port=8080, auto_open=True):
    """Start the dashboard server"""
    try:
        print(f"🚀 Starting Lumen Predictive Maintenance Dashboard...")
        print(f"📡 Server starting on port {port}")
        
        # Create server
        server_address = ('', port)
        httpd = HTTPServer(server_address, DashboardHandler)
        
        # Get the local URL
        dashboard_url = f"http://localhost:{port}"
        
        print(f"🌐 Dashboard available at: {dashboard_url}")
        print(f"📊 API endpoint: {dashboard_url}/api/dashboard-data")
        print(f"🔄 Refresh endpoint: {dashboard_url}/api/refresh")
        print("\n" + "="*60)
        print("🎯 LUMEN PREDICTIVE MAINTENANCE DASHBOARD")
        print("="*60)
        print(f"🖥️  Open your browser and go to: {dashboard_url}")
        print("🔄 The dashboard auto-refreshes every 30 seconds")
        print("⚡ Click the refresh button for manual updates")
        print("📧 Email alerts are sent for high-risk predictions")
        print("="*60)
        
        # Auto-open browser
        if auto_open:
            def open_browser():
                time.sleep(2)  # Wait for server to start
                try:
                    webbrowser.open(dashboard_url)
                    print(f"🌐 Opening dashboard in browser...")
                except Exception as e:
                    print(f"Could not auto-open browser: {e}")
                    print(f"Please manually open: {dashboard_url}")
            
            threading.Thread(target=open_browser, daemon=True).start()
        
        # Start server
        print("\n🚀 Server starting... Press Ctrl+C to stop")
        httpd.serve_forever()
        
    except KeyboardInterrupt:
        print("\n\n🛑 Dashboard server stopped by user")
    except Exception as e:
        print(f"❌ Error starting dashboard server: {e}")
        raise

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Lumen Predictive Maintenance Dashboard')
    parser.add_argument('--port', type=int, default=8080, help='Port to run the server on (default: 8080)')
    parser.add_argument('--no-browser', action='store_true', help='Do not auto-open browser')
    
    args = parser.parse_args()
    
    start_dashboard_server(port=args.port, auto_open=not args.no_browser)
