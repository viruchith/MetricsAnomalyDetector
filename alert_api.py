import smtplib
from email.mime.text import MIMEText
import requests
from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse
import asyncio
import os

app = FastAPI()
connected_websockets = set()

# Configuration (set these in your .env or directly below)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp-relay.yourcompany.com")   # Internal relay address
SMTP_PORT = int(os.getenv("SMTP_PORT", 25))                           # Usually 25 or 587
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "alerts@yourcompany.com")    # Must be an allowed sender
TEAMS_WEBHOOK_URL = os.getenv("TEAMS_WEBHOOK_URL", "https://outlook.office.com/webhook/your-webhook-url")

def send_email(subject, body, recipient):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = recipient

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
            # No login or TLS for internal relay (add server.starttls() if required)
            server.sendmail(SENDER_EMAIL, [recipient], msg.as_string())
        print(f"Email sent to {recipient}")
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

def send_teams_alert(message):
    payload = {"text": message}
    try:
        resp = requests.post(TEAMS_WEBHOOK_URL, json=payload, timeout=5)
        print("Teams webhook status:", resp.status_code)
        return resp.status_code == 200
    except Exception as e:
        print("Teams webhook error:", e)
        return False

@app.websocket("/ws/alerts")
async def alerts_ws(websocket: WebSocket):
    await websocket.accept()
    connected_websockets.add(websocket)
    try:
        while True:
            await asyncio.sleep(60)  # Keep connection open
    except Exception:
        pass
    finally:
        connected_websockets.remove(websocket)

@app.post("/alert")
async def post_alert(req: Request):
    alert = await req.json()
    subject = f"ALERT: {alert.get('message', 'Monitoring Event')}"
    body = (
        f"Server: {alert.get('server', 'N/A')}\n"
        f"Metric: {alert.get('metric', 'N/A')}\n"
        f"Value: {alert.get('value', 'N/A')}\n"
        f"Message: {alert.get('message', 'N/A')}\n"
        f"Time: {alert.get('timestamp', 'N/A')}\n"
    )
    # Send email via internal relay
    email_success = send_email(subject, body, alert.get('recipient', SENDER_EMAIL))
    # Send to Teams
    teams_success = send_teams_alert(body)
    # Broadcast to dashboard
    for ws in connected_websockets.copy():
        try:
            await ws.send_json(alert)
        except Exception:
            pass
    return {
        "sent_to_email": email_success,
        "sent_to_teams": teams_success,
        "dashboard_users": len(connected_websockets)
    }

@app.get("/")
async def dashboard():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
      <title>Alert Dashboard</title>
      <style>
        body { font-family: sans-serif; }
        #alerts { margin-top: 20px; }
        .alert { background: #ffe0e0; margin: 5px; padding: 10px; border-radius: 4px;}
      </style>
    </head>
    <body>
      <h2>Live Alerts Dashboard</h2>
      <div id="alerts"></div>
      <script>
        let ws = new WebSocket("ws://" + location.host + "/ws/alerts");
        ws.onmessage = function(event) {
          let data = JSON.parse(event.data);
          let div = document.createElement("div");
          div.className = "alert";
          div.textContent = "🚨 " + JSON.stringify(data);
          document.getElementById("alerts").prepend(div);
        };
        ws.onopen = () => { console.log("WebSocket connected"); };
        ws.onclose = () => { console.log("WebSocket disconnected"); };
      </script>
    </body>
    </html>
    """)