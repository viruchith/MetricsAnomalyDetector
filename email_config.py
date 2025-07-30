# Email Configuration for Predictive Maintenance System
# Copy this file to email_config.py and fill in your email settings

EMAIL_SETTINGS = {
    # SMTP Configuration
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    
    # Sender Email (Your email account)
    'sender_email': 'zuhamujawar@gmail.com',
    'sender_password': 'hycx kfkq przu ztut',
    
    # Recipient Email (Where alerts will be sent)
    'recipient_email': 'Zuha.Mujawar@lumen.com',
    
    # Alert Thresholds
    'medium_risk_threshold': 0.4,
    'high_risk_threshold': 0.7,
    
    # Email Settings
    'enable_html_email': True,
    'enable_email_logs': True,
    'demo_mode': False,  # Set to False to send real emails
}

# Instructions for Gmail Setup:
"""
To use Gmail for sending alerts:

1. Enable 2-Factor Authentication on your Gmail account
2. Generate an App Password:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate a new app password for "Mail"
   - Use this password (not your regular password) in 'sender_password'

3. Update the settings above with your email information

4. For other email providers, update smtp_server and smtp_port accordingly:
   - Outlook: smtp-mail.outlook.com, port 587
   - Yahoo: smtp.mail.yahoo.com, port 587
   - Custom: Check your email provider's SMTP settings
"""

# Security Note:
"""
IMPORTANT: Never commit real passwords to version control!

For production use:
1. Store the password in an environment variable:
   os.environ['EMAIL_PASSWORD'] = 'your-app-password'

2. Or use a secure credential management system

3. Consider using OAuth2 for enhanced security
"""
