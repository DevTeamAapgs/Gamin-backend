from email.message import EmailMessage
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
from pathlib import Path

from email.message import EmailMessage
import aiosmtplib 
from jinja2 import Environment, FileSystemLoader, select_autoescape

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

        self.jinja_env = Environment(
            loader=FileSystemLoader("templates"),
            autoescape=select_autoescape(['html', 'xml'])
        )
    
    def _validate_config(self):
        """Validate SMTP configuration"""
        required = [self.username, self.password, self.server, self.port]
        print("required",required)
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
    
    
    def _encode_image_base64(self, path: str) -> str:
        with open(path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode("utf-8")
            return f"data:image/png;base64,{encoded}"  # or image/jpeg if using JPG
        
    def _create_email_template(self, username: str, otp: str):
        """Generate HTML email template with DODUKU branding using Jinja2."""
        try:
            template = self.jinja_env.get_template("forgotpassword.html")
            #otp_digits = ''.join(f'<div class="otp-digit">{digit}</div>' for digit in otp)
            otp_digits = ''.join(f'<div class="otp-digit" style="margin:0 12px;display:inline-block;">{digit}</div>' for digit in otp)
            current_year = datetime.now().year
            return template.render(username=username, otp_digits=otp_digits, current_year=current_year)
        except Exception as e:
            return logger.error(f"Error rendering email template: {e}")
    
    
    async def send_email(self, to: str, subject: str, content: str) -> bool:
        """Core email sending method"""
        if not self.email_enabled:
            logger.warning("Email sending disabled - check configuration")
            return False

        try:
            message = EmailMessage()
            message['From'] = self.from_email
            message['To'] = "trainingteam@aapgs.com"
            message['Subject'] = subject
            message.add_alternative(content, subtype="html")
            
            
            print(vars(self),"self")
            # Establish connection
            await aiosmtplib.send(
                message,
                hostname=self.server,
                port= self.port,
                username= self.username,
                password= self.password,
                start_tls=True,
                use_tls=False) 
            
            logger.info(f"Email sent to {to}")
            return True
            
        except smtplib.SMTPException as e:
            logger.error(f"SMaiosmtplibTP error: {e}")
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