import json
import threading
from datetime import datetime
from flask import Flask, jsonify

import google.generativeai as genai
import pika

app = Flask(__name__)

# Global list to store critical log messages
critical_log_messages = []

# Dashboard HTML as a string
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Log Monitor Dashboard</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .header {
            background-color: #2c3e50;
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .stats {
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            flex: 1;
        }
        .critical-logs {
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .log-entry {
            border-bottom: 1px solid #eee;
            padding: 15px;
        }
        .log-entry:last-child {
            border-bottom: none;
        }
        .log-timestamp {
            color: #666;
            font-size: 0.9em;
            margin-bottom: 5px;
        }
        .log-message {
            font-weight: bold;
            margin-bottom: 10px;
            color: #e74c3c;
        }
        .log-reason {
            color: #555;
            font-style: italic;
        }
        .refresh-btn {
            background-color: #3498db;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            margin-bottom: 20px;
        }
        .refresh-btn:hover {
            background-color: #2980b9;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Critical Log Monitor Dashboard</h1>
        <p>Real-time monitoring of critical log messages</p>
    </div>
    
    <button class="refresh-btn" onclick="loadCriticalLogs()">Refresh</button>
    
    <div class="stats">
        <div class="stat-card">
            <h3>Total Critical Logs</h3>
            <div id="total-logs">Loading...</div>
        </div>
        <div class="stat-card">
            <h3>Last Updated</h3>
            <div id="last-updated">Loading...</div>
        </div>
    </div>
    
    <div class="critical-logs">
        <div style="padding: 20px; background-color: #34495e; color: white;">
            <h2>Critical Log Messages</h2>
        </div>
        <div id="logs-container">
            <div style="padding: 20px; text-align: center; color: #666;">
                Loading critical logs...
            </div>
        </div>
    </div>

    <script>
        function loadCriticalLogs() {
            fetch('/api/critical-logs')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('total-logs').textContent = data.length;
                    document.getElementById('last-updated').textContent = new Date().toLocaleString();
                    
                    const container = document.getElementById('logs-container');
                    
                    if (data.length === 0) {
                        container.innerHTML = '<div style="padding: 20px; text-align: center; color: #666;">No critical logs found</div>';
                        return;
                    }
                    
                    container.innerHTML = data.map(log => `
                        <div class="log-entry">
                            <div class="log-timestamp">${log.timestamp}</div>
                            <div class="log-message">${log.message}</div>
                            <div class="log-reason">Reason: ${log.reason}</div>
                        </div>
                    `).join('');
                })
                .catch(error => {
                    console.error('Error loading logs:', error);
                    document.getElementById('logs-container').innerHTML = 
                        '<div style="padding: 20px; text-align: center; color: #e74c3c;">Error loading logs</div>';
                });
        }
        
        // Load logs on page load
        loadCriticalLogs();
        
        // Auto-refresh every 30 seconds
        setInterval(loadCriticalLogs, 30000);
    </script>
</body>
</html>
"""

def read_api_key_from_file(file_path: str) -> str:
    """Reads the Gemini API key from a file."""
    with open(file_path, 'r') as file:
        return file.read().strip()

# Set your Gemini API key
genai.configure(api_key=read_api_key_from_file("apikey.txt"))

negative_keywords = {
    "exceeded", "failed", "fail", "failure", "error", "exception", "fatal",
    "critical", "panic", "abort", "denied", "rejected", "timeout",
    "unavailable", "unreachable", "invalid", "corrupt", "overflow",
    "underflow", "missing", "not found", "cannot", "unable", "disconnect",
    "down", "crash", "bug", "broken", "halt", "stopped", "stop", "off",
    "refused", "lost", "terminated", "deprecated", "blocked", "conflict",
    "unauthorized", "forbidden", "expired", "malformed", "incomplete",
    "limit", "overflow", "retry", "shutdown", "warning", "assert",
    "traceback", "stacktrace"
}
negative_log_messages = []
batch_size = 10  # Define batch_size variable

def is_log_critical(log_message: str) -> dict:
    """
    Uses Gemini API to determine whether a log message is critical.
    Returns a dictionary with critical status, message, and reason.
    """
    prompt = (
        "You are a helpful assistant. Determine if the following log message is critical.\n"
        "Return only whether log message is 'CRITICAL' true or false along with the log message itself as 'message' attribute and the reason for its criticality as 'reason' attribute, as a JSON response only.\n"
        f"Log message: {log_message}"
    )

    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content(prompt)

    try:
        print(f"Response from Gemini API: {response.text.strip()}")
        # Clean response text - remove markdown formatting if present
        response_text = response.text.strip()
        if response_text.startswith('```json'):
            response_text = response_text[7:]  # Remove ```json
        if response_text.endswith('```'):
            response_text = response_text[:-3]  # Remove trailing ```
        response_text = response_text.strip()
        
        output = json.loads(response_text)
        print(f"Parsed output: {output}")
        return output
    except json.JSONDecodeError:
        return {"CRITICAL": False, "message": log_message, "reason": "Failed to parse response"}

def is_log_message_negative(log_message: str) -> bool:
    """
    Checks if the log message contains any negative keywords.
    Returns True if it contains a negative keyword, False otherwise.
    """
    log_message_lower = log_message.lower()
    for keyword in negative_keywords:
        if keyword in log_message_lower:
            return True
    return False

def process_log_message(log_message: str) -> None:
    """
    Processes a log message to determine if it is critical or contains negative keywords.
    """
    global critical_log_messages
    
    if is_log_message_negative(log_message) and len(negative_log_messages) < batch_size:
        negative_log_messages.append(log_message)
    else:
        combined_message = "\n".join(negative_log_messages)
        if combined_message:
            analysis_result = is_log_critical(combined_message)
            
            if  analysis_result.get("CRITICAL", False):
                critical_entry = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "message": analysis_result.get("message", combined_message),
                    "reason": analysis_result.get("reason", "No reason provided"),
                    "original_logs": negative_log_messages.copy()
                }
                critical_log_messages.append(critical_entry)
                
                # Keep only the last 100 critical messages
                if len(critical_log_messages) > 100:
                    critical_log_messages.pop(0)
                
                print(f"Critical log detected: {analysis_result}")
            
            negative_log_messages.clear()

def consume_messages_from_queue():
    """
    Consumes messages from the RabbitMQ queue and processes them.
    """
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='q.logs', durable=True)

    def callback(_ch, _method, _properties, body):
        log_message = body.decode('utf-8')
        process_log_message(log_message)
        print(f"Log message: {log_message}")
    channel.basic_consume(queue='q.logs', on_message_callback=callback, auto_ack=True)
    print('Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

# Flask routes for the web dashboard
@app.route('/')
def dashboard():
    """Render the main dashboard page."""
    return DASHBOARD_HTML

@app.route('/api/critical-logs')
def get_critical_logs():
    """API endpoint to get critical log messages as JSON."""
    return jsonify(critical_log_messages)

def run_web_server():
    """Run the Flask web server."""
    app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == '__main__':
    # Start the web server in a separate thread
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    
    print("Web dashboard started at http://localhost:5000")
    
    # Start consuming messages from the queue
    consume_messages_from_queue()
