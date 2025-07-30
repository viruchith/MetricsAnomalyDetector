import json
import os
import sys
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse
import webbrowser
import threading
import time

class SimpleDashboardHandler(SimpleHTTPRequestHandler):
    """Simple HTTP handler for the dashboard"""
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/dashboard-data':
            self.serve_dashboard_data()
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
            # Get sample data for now
            data = self.get_sample_dashboard_data()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            
            json_data = json.dumps(data, indent=2)
            self.wfile.write(json_data.encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, f"Error getting dashboard data: {str(e)}")
    
    def get_sample_dashboard_data(self):
        """Return sample dashboard data"""
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

def start_simple_dashboard(port=8080):
    """Start the simple dashboard server"""
    try:
        print(f"🚀 Starting Lumen Dashboard Server on port {port}...")
        
        # Create server
        server_address = ('', port)
        httpd = HTTPServer(server_address, SimpleDashboardHandler)
        
        # Get the local URL
        dashboard_url = f"http://localhost:{port}"
        
        print(f"🌐 Dashboard available at: {dashboard_url}")
        print(f"📊 API endpoint: {dashboard_url}/api/dashboard-data")
        print("\n" + "="*60)
        print("🎯 LUMEN PREDICTIVE MAINTENANCE DASHBOARD")
        print("="*60)
        print(f"🖥️  Open your browser and go to: {dashboard_url}")
        print("🔄 The dashboard shows sample data for demonstration")
        print("="*60)
        
        # Auto-open browser
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
    start_simple_dashboard()
