#!/usr/bin/env python3
"""
Lumen Predictive Maintenance Dashboard Launcher
==============================================

This script launches the reactive dashboard for the Lumen predictive maintenance system.
It automatically runs the ML models and serves a web-based dashboard with real-time alerts.

Usage:
    python launch_dashboard.py [--port 8080] [--no-browser]

Features:
- Real-time machine health monitoring
- Predictive failure alerts with risk levels
- Email notifications for critical issues
- Auto-refreshing dashboard every 30 seconds
- Manual refresh triggers ML model re-training
- Lumen branding with professional UI

The dashboard will be available at: http://localhost:8080
"""

import os
import sys
import argparse
from datetime import datetime

def main():
    print("🚀 LUMEN PREDICTIVE MAINTENANCE DASHBOARD")
    print("=" * 50)
    print(f"⏰ Starting at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🏢 Powered by Lumen Technologies")
    print("=" * 50)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Launch the Lumen Predictive Maintenance Dashboard',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python launch_dashboard.py                    # Start on default port 8080
  python launch_dashboard.py --port 9000       # Start on custom port
  python launch_dashboard.py --no-browser      # Don't auto-open browser
        """
    )
    parser.add_argument('--port', type=int, default=8080, 
                      help='Port to run the dashboard server on (default: 8080)')
    parser.add_argument('--no-browser', action='store_true',
                      help='Do not automatically open the browser')
    
    args = parser.parse_args()
    
    # Check if required files exist
    required_files = [
        'dashboard.html',
        'dashboard_server.py',
        'enhanced_failure_prediction.py'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("❌ ERROR: Missing required files:")
        for file in missing_files:
            print(f"   - {file}")
        print("\nPlease ensure all files are in the current directory.")
        sys.exit(1)
    
    print("✅ All required files found")
    
    # Import and start the dashboard server
    try:
        from dashboard_server import start_dashboard_server
        
        print(f"🌐 Starting dashboard server on port {args.port}...")
        
        if args.no_browser:
            print("🔧 Browser auto-open disabled")
        
        # Start the server
        start_dashboard_server(port=args.port, auto_open=not args.no_browser)
        
    except ImportError as e:
        print(f"❌ Error importing dashboard server: {e}")
        print("Please ensure dashboard_server.py is available and all dependencies are installed")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Dashboard stopped by user")
        print("👋 Thank you for using Lumen Predictive Maintenance Dashboard!")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
