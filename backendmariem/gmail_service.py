"""
gmail_service.py - Gmail Integration for sending emails
"""
import os
import base64
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    import pickle
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False

SCOPES = ['https://www.googleapis.com/auth/gmail.send']


class GmailService:
    """Gmail service for sending emails"""
    
    def __init__(self):
        self.service = None
        self.initialized = False
        self.credentials_file = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
        self.token_file = os.getenv("GMAIL_TOKEN_FILE", "token.json")
    
    def initialize(self) -> bool:
        """Initialize Gmail API"""
        if not GOOGLE_API_AVAILABLE:
            logger.warning("⚠️ Google API not available")
            return False
        
        try:
            creds = None
            
            # Load existing token (try JSON first, then pickle)
            if os.path.exists(self.token_file):
                try:
                    # Try JSON format first
                    creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
                    logger.info("✅ Loaded Gmail token from JSON")
                except Exception:
                    try:
                        # Fall back to pickle format
                        with open(self.token_file, 'rb') as token:
                            creds = pickle.load(token)
                        logger.info("✅ Loaded Gmail token from pickle")
                    except Exception as e:
                        logger.warning(f"⚠️ Could not load Gmail token: {e}")
                        creds = None
            
            # Refresh if expired
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    logger.info("✅ Gmail token refreshed")
                except Exception as e:
                    logger.warning(f"⚠️ Could not refresh Gmail token: {e}")
                    creds = None
            
            if not creds or not creds.valid:
                logger.warning("⚠️ Gmail: No valid credentials")
                return False
            
            self.service = build('gmail', 'v1', credentials=creds)
            self.initialized = True
            logger.info("✅ Gmail service initialized")
            return True
        
        except Exception as e:
            logger.error(f"❌ Gmail init failed: {e}")
            return False
    
    def send_email(self, to: str, subject: str, body: str) -> Dict[str, Any]:
        """Send a simple email"""
        if not self.initialized:
            return {'success': False, 'error': 'Gmail not initialized'}
        
        try:
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject
            
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            result = self.service.users().messages().send(
                userId='me',
                body={'raw': raw}
            ).execute()
            
            logger.info(f"✅ Email sent to {to}")
            return {'success': True, 'message_id': result['id']}
        
        except Exception as e:
            logger.error(f"❌ Send email failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_email_with_pdf(
        self,
        to: str,
        subject: str,
        body: str,
        pdf_data: bytes,
        pdf_name: str = "document.pdf"
    ) -> Dict[str, Any]:
        """Send email with PDF attachment"""
        if not self.initialized:
            return {'success': False, 'error': 'Gmail not initialized'}
        
        try:
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject
            
            # Add body
            message.attach(MIMEText(body, 'plain'))
            
            # Add PDF attachment
            pdf_attachment = MIMEApplication(pdf_data, _subtype='pdf')
            pdf_attachment.add_header('Content-Disposition', 'attachment', filename=pdf_name)
            message.attach(pdf_attachment)
            
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            result = self.service.users().messages().send(
                userId='me',
                body={'raw': raw}
            ).execute()
            
            logger.info(f"✅ Email with PDF sent to {to}")
            return {'success': True, 'message_id': result['id']}
        
        except Exception as e:
            logger.error(f"❌ Send email with PDF failed: {e}")
            return {'success': False, 'error': str(e)}


# Singleton
_gmail_service = None

def get_gmail_service() -> GmailService:
    global _gmail_service
    if _gmail_service is None:
        _gmail_service = GmailService()
        _gmail_service.initialize()
    return _gmail_service
