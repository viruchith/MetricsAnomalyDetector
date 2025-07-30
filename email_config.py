# Demo Email Configuration for Testing
# This version will show email content without actually sending emails

EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'sender_email': 'zuhamujawar@gmail.com',
    'sender_password': 'hycx kfkq przu ztut',
    'recipient_email': 'zuhamujawar@gmail.com',
    'demo_mode': False  # Set to False for actual email sending
}

print("📧 Email alerts module loaded in LIVE mode.")
print("   Real emails WILL be sent to zuhamujawar@gmail.com")
print("   Sender: zuhamujawar@gmail.com")
