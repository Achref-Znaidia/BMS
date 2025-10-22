# Email Configuration Setup

This document explains how to configure email functionality for the BMS application.

## Email Service Configuration

The BMS application uses Python's built-in `smtplib` and `email` modules for sending emails. You need to configure your email service provider settings.

### Environment Variables

Set the following environment variables or update the EmailService configuration:

```bash
# Gmail Configuration (Recommended)
export BMS_SMTP_SERVER=smtp.gmail.com
export BMS_SMTP_PORT=587
export BMS_EMAIL_USERNAME=your-email@gmail.com
export BMS_EMAIL_PASSWORD=your-app-password

# Outlook Configuration
export BMS_SMTP_SERVER=smtp-mail.outlook.com
export BMS_SMTP_PORT=587
export BMS_EMAIL_USERNAME=your-email@outlook.com
export BMS_EMAIL_PASSWORD=your-password

# Custom SMTP Server
export BMS_SMTP_SERVER=your-smtp-server.com
export BMS_SMTP_PORT=587
export BMS_EMAIL_USERNAME=your-email@domain.com
export BMS_EMAIL_PASSWORD=your-password
```

### Gmail Setup (Recommended)

1. **Enable 2-Factor Authentication** on your Google account
2. **Generate an App Password**:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate a password for "Mail"
   - Use this password as `BMS_EMAIL_PASSWORD`

3. **Configure the application**:
   ```python
   email_service = EmailService(
       smtp_server="smtp.gmail.com",
       smtp_port=587,
       username="your-email@gmail.com",
       password="your-app-password"
   )
   ```

### Outlook Setup

1. **Enable SMTP Authentication** in your Outlook account
2. **Use your regular password** (no app password needed for most Outlook accounts)
3. **Configure the application**:
   ```python
   email_service = EmailService(
       smtp_server="smtp-mail.outlook.com",
       smtp_port=587,
       username="your-email@outlook.com",
       password="your-password"
   )
   ```

### Custom SMTP Server

For custom SMTP servers, configure as follows:

```python
email_service = EmailService(
    smtp_server="your-smtp-server.com",
    smtp_port=587,  # or 465 for SSL
    username="your-email@domain.com",
    password="your-password",
    use_tls=True  # or False for SSL
)
```

## Email Features

The BMS application sends the following types of emails:

### 1. User Registration
- **Verification Email**: Sent when a user registers
- **Welcome Email**: Sent after email verification

### 2. Password Management
- **Password Reset**: Sent when user requests password reset
- **Password Change Confirmation**: Sent when password is changed

### 3. Notifications
- **System Notifications**: Sent to all users
- **Admin Notifications**: Sent to administrators
- **Status Updates**: Sent for important system events

## Email Templates

The application includes HTML email templates for:

- User verification
- Password reset
- Welcome messages
- System notifications
- Status updates

Templates are automatically generated with proper styling and branding.

## Testing Email Configuration

You can test your email configuration by running:

```python
from src.services.email_service import EmailService

# Test connection
email_service = EmailService()
if email_service.test_connection():
    print("Email configuration is working!")
else:
    print("Email configuration failed. Check your settings.")
```

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Check username and password
   - For Gmail, ensure you're using an App Password
   - Verify 2FA is enabled for Gmail

2. **Connection Refused**
   - Check SMTP server and port
   - Verify firewall settings
   - Try different ports (587, 465, 25)

3. **TLS/SSL Errors**
   - Ensure `use_tls=True` for port 587
   - Use `use_tls=False` for port 465 (SSL)

4. **Email Not Delivered**
   - Check spam folder
   - Verify recipient email addresses
   - Check SMTP server logs

### Debug Mode

Enable debug mode to see detailed SMTP logs:

```python
import smtplib
import logging

# Enable SMTP debug logging
logging.basicConfig(level=logging.DEBUG)
smtplib.SMTP.debuglevel = 1
```

## Security Considerations

1. **Never hardcode passwords** in your code
2. **Use environment variables** for sensitive information
3. **Use App Passwords** for Gmail instead of your main password
4. **Enable 2FA** on all email accounts
5. **Use TLS encryption** for email transmission
6. **Regularly rotate passwords** and app passwords

## Production Deployment

For production deployment:

1. **Use a dedicated email service** (SendGrid, Mailgun, etc.)
2. **Set up proper DNS records** (SPF, DKIM, DMARC)
3. **Monitor email delivery** and bounce rates
4. **Implement rate limiting** to prevent abuse
5. **Use environment-specific configurations**

## Support

If you encounter issues with email configuration:

1. Check the application logs for error messages
2. Verify your email provider's SMTP settings
3. Test with a simple email client first
4. Contact your system administrator for help
