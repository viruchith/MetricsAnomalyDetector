# Email Alert Configuration for Predictive Maintenance System
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from datetime import datetime

# Import email configuration
try:
    from email_config import EMAIL_SETTINGS as EMAIL_CONFIG
except ImportError:
    # Default configuration if email_config.py doesn't exist
    EMAIL_CONFIG = {
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'sender_email': 'zuhamujawar@gmail.com',
        'sender_password': 'hycx kfkq przu ztut',
        'recipient_email': 'Zuha.Mujawar@lumen.com',
        'demo_mode': False
    }

def send_maintenance_alert(alerts_data, training_summary):
    """
    Send email alert for medium and high risk failures
    
    Args:
        alerts_data: List of dictionaries containing alert information
        training_summary: Dictionary with training information
    """
    
    # Check if there are any medium or high risk alerts
    medium_high_alerts = [alert for alert in alerts_data if alert['risk_level'] in ['Medium', 'High']]
    
    if not medium_high_alerts:
        print("📧 No medium or high risk alerts to send.")
        return True
    
    try:
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = f"🚨 URGENT: Predictive Maintenance Alert - {len(medium_high_alerts)} Critical Issues"
        message["From"] = EMAIL_CONFIG['sender_email']
        message["To"] = EMAIL_CONFIG['recipient_email']
        
        # Create HTML content
        html_content = create_html_email(medium_high_alerts, training_summary)
        
        # Create plain text content
        text_content = create_text_email(medium_high_alerts, training_summary)
        
        # Turn these into plain/html MIMEText objects
        part1 = MIMEText(text_content, "plain")
        part2 = MIMEText(html_content, "html")
        
        # Add HTML/plain-text parts to MIMEMultipart message
        message.attach(part1)
        message.attach(part2)
        
        # Create secure connection and send email
        context = ssl.create_default_context()
        
        # Check if in demo mode or if password is not configured
        demo_mode = EMAIL_CONFIG.get('demo_mode', True) or not EMAIL_CONFIG.get('sender_password')
        
        if demo_mode:
            # Demo mode - just print the email content
            print("📧 EMAIL ALERT CONTENT (DEMO MODE):")
            print("=" * 80)
            print(f"To: {EMAIL_CONFIG['recipient_email']}")
            print(f"Subject: {message['Subject']}")
            print("=" * 80)
            print(text_content)
            print("=" * 80)
            print("📝 NOTE: This is a demonstration. No actual email was sent.")
            print("📝 To enable real email sending, configure email_config.py with valid credentials.")
        else:
            # Real email sending mode
            with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
                server.starttls(context=context)
                server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
                text = message.as_string()
                server.sendmail(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['recipient_email'], text)
            print(f"📧 Real email sent successfully to {EMAIL_CONFIG['recipient_email']}")
        
        print(f"✅ Email alert processed successfully for {EMAIL_CONFIG['recipient_email']}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send email alert: {str(e)}")
        return False

def create_html_email(alerts, training_summary):
    """Create HTML formatted email content"""
    
    html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; margin: 20px;">
        <div style="background-color: #ff4444; color: white; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
          <h1>🚨 URGENT: Predictive Maintenance Alert</h1>
          <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
          <p><strong>Total Critical Issues:</strong> {len(alerts)}</p>
        </div>
        
        <div style="background-color: #f0f0f0; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
          <h2>📊 Training Summary</h2>
          <p><strong>Files Processed:</strong> {training_summary.get('files_count', 'N/A')}</p>
          <p><strong>Total Machines:</strong> {training_summary.get('total_machines', 'N/A')}</p>
          <p><strong>Latest Data:</strong> {training_summary.get('latest_timestamp', 'N/A')}</p>
          <p><strong>Total Samples:</strong> {training_summary.get('total_samples', 'N/A')}</p>
        </div>

        <h2>⚠️ Critical Machine Alerts</h2>
        <table style="border-collapse: collapse; width: 100%; border: 1px solid #ddd;">
          <thead style="background-color: #f2f2f2;">
            <tr>
              <th style="border: 1px solid #ddd; padding: 12px; text-align: left;">Machine ID</th>
              <th style="border: 1px solid #ddd; padding: 12px; text-align: left;">Failure Type</th>
              <th style="border: 1px solid #ddd; padding: 12px; text-align: left;">Risk Level</th>
              <th style="border: 1px solid #ddd; padding: 12px; text-align: left;">Likelihood</th>
              <th style="border: 1px solid #ddd; padding: 12px; text-align: left;">Time to Fail</th>
              <th style="border: 1px solid #ddd; padding: 12px; text-align: left;">Issues</th>
            </tr>
          </thead>
          <tbody>
    """
    
    for alert in alerts:
        risk_color = "#ff4444" if alert['risk_level'] == 'High' else "#ffaa00"
        html += f"""
            <tr style="background-color: {risk_color}20;">
              <td style="border: 1px solid #ddd; padding: 8px;"><strong>{alert['machine_id']}</strong></td>
              <td style="border: 1px solid #ddd; padding: 8px;">{alert['icon']} {alert['failure_type']}</td>
              <td style="border: 1px solid #ddd; padding: 8px;"><strong>{alert['risk_level']}</strong></td>
              <td style="border: 1px solid #ddd; padding: 8px;"><strong>{alert['likelihood']:.1%}</strong></td>
              <td style="border: 1px solid #ddd; padding: 8px;">{alert['time_to_fail']}</td>
              <td style="border: 1px solid #ddd; padding: 8px;">{alert['issues']}</td>
            </tr>
        """
    
    html += """
          </tbody>
        </table>
        
        <div style="background-color: #ffffcc; padding: 15px; border-radius: 5px; margin-top: 20px;">
          <h3>🎯 Immediate Actions Required:</h3>
          <ul>
    """
    
    for alert in alerts:
        if alert['risk_level'] == 'High':
            html += f"<li><strong>Machine {alert['machine_id']}:</strong> IMMEDIATE inspection and maintenance required - {alert['failure_type']} failure imminent!</li>"
        else:
            html += f"<li><strong>Machine {alert['machine_id']}:</strong> Schedule maintenance within next 24 hours - {alert['failure_type']} showing degradation.</li>"
    
    html += """
          </ul>
        </div>
        
        <div style="margin-top: 20px; font-size: 12px; color: #666;">
          <p>This alert was generated by the Predictive Maintenance System.</p>
          <p>For questions, contact the maintenance team.</p>
        </div>
      </body>
    </html>
    """
    
    return html

def create_text_email(alerts, training_summary):
    """Create plain text email content"""
    
    text = f"""
🚨 URGENT: PREDICTIVE MAINTENANCE ALERT
=====================================

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total Critical Issues: {len(alerts)}

📊 TRAINING SUMMARY
==================
Files Processed: {training_summary.get('files_count', 'N/A')}
Total Machines: {training_summary.get('total_machines', 'N/A')}
Latest Data: {training_summary.get('latest_timestamp', 'N/A')}
Total Samples: {training_summary.get('total_samples', 'N/A')}

⚠️ CRITICAL MACHINE ALERTS
==========================
"""
    
    for alert in alerts:
        text += f"""
Machine: {alert['machine_id']}
Failure Type: {alert['icon']} {alert['failure_type']}
Risk Level: {alert['risk_level']}
Likelihood: {alert['likelihood']:.1%}
Time to Fail: {alert['time_to_fail']}
Issues: {alert['issues']}
{'─' * 50}
"""
    
    text += f"""

🎯 IMMEDIATE ACTIONS REQUIRED:
=============================
"""
    
    for alert in alerts:
        if alert['risk_level'] == 'High':
            text += f"• Machine {alert['machine_id']}: IMMEDIATE inspection and maintenance required - {alert['failure_type']} failure imminent!\n"
        else:
            text += f"• Machine {alert['machine_id']}: Schedule maintenance within next 24 hours - {alert['failure_type']} showing degradation.\n"
    
    text += f"""

This alert was generated by the Predictive Maintenance System.
For questions, contact the maintenance team.
"""
    
    return text

def log_email_alert(alerts, success):
    """Log email alert attempt"""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = f"{log_dir}/email_alerts.log"
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    status = "SUCCESS" if success else "FAILED"
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"{timestamp} - {status} - {len(alerts)} alerts sent to {EMAIL_CONFIG['recipient_email']}\n")
        for alert in alerts:
            f.write(f"  - Machine {alert['machine_id']}: {alert['risk_level']} risk {alert['failure_type']}\n")
        f.write("\n")
