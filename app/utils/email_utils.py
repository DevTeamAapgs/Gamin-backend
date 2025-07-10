import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from app.core.config import settings
import random
import string
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

logger = logging.getLogger(__name__)

class EmailManager:
    def __init__(self):
        # SMTP Configuration
        self.username = settings.mail_username
        self.password = settings.mail_password
        self.from_email = settings.mail_from
        self.port = settings.mail_port
        self.server = settings.mail_server
        self.tls = settings.mail_tls
        self.ssl = settings.mail_ssl
        
        # Validate configuration
        self._validate_config()
        
        # Encryption setup
        self.aes_key = self._derive_aes_key(settings.aes_key)
        self.cipher_suite = Fernet(self.aes_key)
    
    def _validate_config(self):
        """Validate SMTP configuration"""
        required = [self.username, self.password, self.server, self.port]
        if not all(required):
            logger.error("Incomplete SMTP configuration - email sending disabled")
            self.email_enabled = False
        else:
            self.email_enabled = True
            logger.info("SMTP configuration validated")

    def _derive_aes_key(self, key: str) -> bytes:
        """Derive encryption key"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=settings.salt.encode(),
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(key.encode()))
    
    def encrypt_data(self, data: str) -> str:
        """Encrypt data using AES encryption"""
        return self.cipher_suite.encrypt(data.encode()).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt data using AES encryption"""
        return self.cipher_suite.decrypt(encrypted_data.encode()).decode()
    
    def get_otp_expiry_time(self) -> datetime:
        """Get OTP expiry time (5 minutes from now)"""
        return datetime.now() + timedelta(minutes=5)
    
    def generate_otp(self, length: int = 6) -> str:
        """Generate numeric OTP"""
        return ''.join(random.choices(string.digits, k=length))
    
    def get_otp_expiry(self, minutes: int = 5) -> datetime:
        """Get OTP expiration time"""
        return datetime.utcnow() + timedelta(minutes=minutes)
    
    def _create_email_template(self, username: str, otp: str) -> str:
        """Generate HTML email template with DODUKU branding"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Password Reset OTP</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f4f4f4;
                }}
                .container {{
                    background-color: #ffffff;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 0 10px rgba(0,0,0,0.1);
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .logo {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #2c3e50;
                    margin-bottom: 10px;
                }}
                .otp-container {{
                    background-color: #ecf0f1;
                    padding: 20px;
                    border-radius: 8px;
                    text-align: center;
                    margin: 20px 0;
                }}
                .otp-code {{
                    font-size: 32px;
                    font-weight: bold;
                    color: #e74c3c;
                    letter-spacing: 5px;
                    font-family: 'Courier New', monospace;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    color: #7f8c8d;
                    font-size: 12px;
                }}
                .warning {{
                    background-color: #fff3cd;
                    border: 1px solid #ffeaa7;
                    color: #856404;
                    padding: 10px;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">DODUKU</div>
                    <h2>Password Reset Request</h2>
                </div>
                
                <p>Hello <strong>{username}</strong>,</p>
                
                <p>We received a request to reset your password. Please use the following OTP (One-Time Password) to complete the password reset process:</p>
                
                <div class="otp-container">
                    <div class="otp-code">{otp}</div>
                </div>
                
                <div class="warning">
                    <strong>Important:</strong> This OTP will expire in 5 minutes for security reasons.
                </div>
                
                <p>If you didn't request this password reset, please ignore this email. Your account will remain secure.</p>
                
                <p>Best regards,<br>
                <strong>DODUKU Team</strong></p>
                
                <div class="footer">
                    <p>This is an automated message. Please do not reply to this email.</p>
                    <p>&copy; 2024 DODUKU. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    async def send_email(self, to: str, subject: str, content: str) -> bool:
        """Core email sending method"""
        if not self.email_enabled:
            logger.warning("Email sending disabled - check configuration")
            return False

        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = to
            msg['Subject'] = subject
            msg.attach(MIMEText(content, 'html'))
            
            # Test mode check
            if "test" in self.username.lower() or not all([self.username, self.password]):
                logger.info(f"TEST MODE: Would send email to {to}")
                return True
            
            # Establish connection
            with self._get_smtp_connection() as server:
                server.send_message(msg)
            
            logger.info(f"Email sent to {to}")
            return True
            
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            return False
        except Exception as e:
            logger.error(f"Email sending failed: {e}")
            return False
    
    def _get_smtp_connection(self) -> smtplib.SMTP:
        """Create SMTP connection with proper security"""
        if self.ssl:
            server = smtplib.SMTP_SSL(self.server, self.port)
        else:
            server = smtplib.SMTP(self.server, self.port)
            if self.tls:
                server.starttls()
        
        server.login(self.username, self.password)
        return server
    
    async def send_otp_email(self, email: str, username: str, otp: str) -> bool:
        """Send OTP email"""
        subject = "Your Verification Code"
        content = self._create_email_template(username, otp)
        return await self.send_email(email, subject, content)

# Global instance
email_manager = EmailManager()