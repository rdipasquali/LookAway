#!/usr/bin/env python3
"""
Quick email test script to debug email configuration issues.
"""
import sys
import os
import smtplib
import getpass
import email.mime.text

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_email_directly():
    """Test email functionality directly."""
    print("=" * 50)
    print("Email Configuration Test")
    print("=" * 50)
    
    # Get email configuration
    smtp_server = input("SMTP server: ").strip()
    
    while True:
        try:
            port_input = input("SMTP port (default: 587): ").strip()
            if not port_input:
                smtp_port = 587
            else:
                smtp_port = int(port_input)
            print(f"Using port: {smtp_port}")
            break
        except ValueError:
            print("Please enter a valid port number.")
    
    email_address = input("Your email address: ").strip()
    password = getpass.getpass("Email password: ")
    recipient = input(f"Send test to (default: {email_address}): ").strip()
    
    if not recipient:
        recipient = email_address
    
    print("\nTesting email configuration...")
    print(f"Server: {smtp_server}:{smtp_port}")
    print(f"From: {email_address}")
    print(f"To: {recipient}")
    
    try:
        # Create test message
        msg = email.mime.text.MIMEText("This is a test email from LookAway application.")
        msg['Subject'] = "LookAway Email Test"
        msg['From'] = email_address
        msg['To'] = recipient
        
        # Send test email
        print("\nConnecting to SMTP server...")
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            print("Connected! Starting TLS...")
            server.starttls()
            print("TLS started! Logging in...")
            server.login(email_address, password)
            print("Logged in! Sending message...")
            server.send_message(msg)
        
        print("✅ Test email sent successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Email test failed: {e}")
        print(f"Error type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    test_email_directly()