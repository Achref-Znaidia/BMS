"""
Email service for notifications and user verification.
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Dict, Any, Optional
import os
from datetime import datetime
import json

from ..config import SecurityConfig

class EmailService:
    """Service for sending emails and notifications."""
    
    def __init__(self, smtp_server: str = None, smtp_port: int = 587,
                 username: str = None, password: str = None,
                 use_tls: bool = True):
        """
        Initialize email service.
        
        Args:
            smtp_server: SMTP server address
            smtp_port: SMTP server port
            username: Email username
            password: Email password
            use_tls: Use TLS encryption
        """
        self.smtp_server = smtp_server or os.environ.get('BMS_SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = smtp_port
        self.username = username or os.environ.get('BMS_EMAIL_USERNAME')
        self.password = password or os.environ.get('BMS_EMAIL_PASSWORD')
        self.use_tls = use_tls
        self.from_email = self.username
        self.from_name = "BMS System"
    
    def send_email(self, to_emails: List[str], subject: str, 
                  body: str, html_body: str = None, 
                  attachments: List[Dict[str, Any]] = None) -> bool:
        """
        Send email to recipients.
        
        Args:
            to_emails: List of recipient email addresses
            subject: Email subject
            body: Plain text body
            html_body: HTML body (optional)
            attachments: List of attachment dictionaries with 'filename' and 'content'
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.username or not self.password:
            print("Email credentials not configured")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject
            
            # Add text part
            text_part = MIMEText(body, 'plain', 'utf-8')
            msg.attach(text_part)
            
            # Add HTML part if provided
            if html_body:
                html_part = MIMEText(html_body, 'html', 'utf-8')
                msg.attach(html_part)
            
            # Add attachments
            if attachments:
                for attachment in attachments:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment['content'])
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {attachment["filename"]}'
                    )
                    msg.attach(part)
            
            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls(context=context)
                server.login(self.username, self.password)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            return False
    
    def send_verification_email(self, user_email: str, username: str, 
                              verification_token: str, 
                              verification_url: str = None) -> bool:
        """Send email verification email."""
        if not verification_url:
            verification_url = f"http://localhost:8000/verify?token={verification_token}"
        
        subject = "Verify Your BMS Account"
        
        body = f"""
Hello {username},

Welcome to the Business Management System (BMS)!

Please verify your email address by clicking the link below:
{verification_url}

This link will expire in 24 hours.

If you didn't create an account, please ignore this email.

Best regards,
BMS Team
        """
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f4f4f4; }}
        .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 20px; margin-bottom: 20px; }}
        .button {{ display: inline-block; background-color: #3498db; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        .footer {{ text-align: center; color: #7f8c8d; font-size: 12px; margin-top: 30px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Welcome to BMS</h1>
            <p>Business Management System</p>
        </div>
        
        <h2>Hello {username}!</h2>
        <p>Welcome to the Business Management System (BMS)!</p>
        <p>Please verify your email address by clicking the button below:</p>
        
        <div style="text-align: center;">
            <a href="{verification_url}" class="button">Verify Email Address</a>
        </div>
        
        <p>This link will expire in 24 hours.</p>
        <p>If you didn't create an account, please ignore this email.</p>
        
        <div class="footer">
            <p>Best regards,<br>BMS Team</p>
        </div>
    </div>
</body>
</html>
        """
        
        return self.send_email([user_email], subject, body, html_body)
    
    def send_password_reset_email(self, user_email: str, username: str, 
                                reset_token: str, reset_url: str = None) -> bool:
        """Send password reset email."""
        if not reset_url:
            reset_url = f"http://localhost:8000/reset-password?token={reset_token}"
        
        subject = "Reset Your BMS Password"
        
        body = f"""
Hello {username},

You requested a password reset for your BMS account.

Click the link below to reset your password:
{reset_url}

This link will expire in 24 hours.

If you didn't request this reset, please ignore this email.

Best regards,
BMS Team
        """
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f4f4f4; }}
        .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; color: #2c3e50; border-bottom: 2px solid #e74c3c; padding-bottom: 20px; margin-bottom: 20px; }}
        .button {{ display: inline-block; background-color: #e74c3c; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        .footer {{ text-align: center; color: #7f8c8d; font-size: 12px; margin-top: 30px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Password Reset</h1>
            <p>Business Management System</p>
        </div>
        
        <h2>Hello {username}!</h2>
        <p>You requested a password reset for your BMS account.</p>
        <p>Click the button below to reset your password:</p>
        
        <div style="text-align: center;">
            <a href="{reset_url}" class="button">Reset Password</a>
        </div>
        
        <p>This link will expire in 24 hours.</p>
        <p>If you didn't request this reset, please ignore this email.</p>
        
        <div class="footer">
            <p>Best regards,<br>BMS Team</p>
        </div>
    </div>
</body>
</html>
        """
        
        return self.send_email([user_email], subject, body, html_body)
    
    def send_notification_email(self, user_emails: List[str], subject: str, 
                              message: str, notification_type: str = "info") -> bool:
        """Send notification email to multiple users."""
        
        # Choose color based on notification type
        colors = {
            'info': '#3498db',
            'success': '#27ae60',
            'warning': '#f39c12',
            'error': '#e74c3c'
        }
        color = colors.get(notification_type, '#3498db')
        
        body = f"""
BMS Notification

{message}

This is an automated notification from the Business Management System.

Best regards,
BMS Team
        """
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f4f4f4; }}
        .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; color: #2c3e50; border-bottom: 2px solid {color}; padding-bottom: 20px; margin-bottom: 20px; }}
        .notification {{ background-color: #f8f9fa; padding: 15px; border-left: 4px solid {color}; margin: 20px 0; }}
        .footer {{ text-align: center; color: #7f8c8d; font-size: 12px; margin-top: 30px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>BMS Notification</h1>
            <p>Business Management System</p>
        </div>
        
        <div class="notification">
            <p>{message}</p>
        </div>
        
        <p>This is an automated notification from the Business Management System.</p>
        
        <div class="footer">
            <p>Best regards,<br>BMS Team</p>
        </div>
    </div>
</body>
</html>
        """
        
        return self.send_email(user_emails, subject, body, html_body)
    
    def send_welcome_email(self, user_email: str, username: str, 
                          login_url: str = None) -> bool:
        """Send welcome email to new user."""
        if not login_url:
            login_url = "http://localhost:8000/login"
        
        subject = "Welcome to BMS - Your Account is Ready!"
        
        body = f"""
Hello {username},

Your BMS account has been successfully created and verified!

You can now log in to the system using your credentials:
Login URL: {login_url}

If you have any questions, please contact your system administrator.

Best regards,
BMS Team
        """
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f4f4f4; }}
        .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; color: #2c3e50; border-bottom: 2px solid #27ae60; padding-bottom: 20px; margin-bottom: 20px; }}
        .button {{ display: inline-block; background-color: #27ae60; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        .footer {{ text-align: center; color: #7f8c8d; font-size: 12px; margin-top: 30px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Welcome to BMS!</h1>
            <p>Your account is ready</p>
        </div>
        
        <h2>Hello {username}!</h2>
        <p>Your BMS account has been successfully created and verified!</p>
        <p>You can now log in to the system using your credentials.</p>
        
        <div style="text-align: center;">
            <a href="{login_url}" class="button">Login to BMS</a>
        </div>
        
        <p>If you have any questions, please contact your system administrator.</p>
        
        <div class="footer">
            <p>Best regards,<br>BMS Team</p>
        </div>
    </div>
</body>
</html>
        """
        
        return self.send_email([user_email], subject, body, html_body)
    
    def test_connection(self) -> bool:
        """Test email service connection."""
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls(context=context)
                server.login(self.username, self.password)
            return True
        except Exception as e:
            print(f"Email connection test failed: {str(e)}")
            return False
