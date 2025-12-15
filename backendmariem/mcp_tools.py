"""
mcp_tools.py - MCP Tools for Doctor Assistant
Document processing, email, calendar, and PDF generation
"""
import os
import io
import base64
import logging
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Import services
from ocr_tool import MedicalOCRTool
from google_calendar_api import get_calendar_api
from gmail_service import get_gmail_service

# Initialize OCR
try:
    ocr_tool = MedicalOCRTool()
    OCR_AVAILABLE = True
except Exception as e:
    OCR_AVAILABLE = False
    logger.warning(f"⚠️ OCR not available: {e}")

# PDF Generation
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("⚠️ ReportLab not available")


class MCPTools:
    """MCP Tools collection for doctor assistant"""
    
    def __init__(self):
        self.calendar_api = get_calendar_api()
        self.gmail_service = get_gmail_service()
    
    # ==================== OCR TOOLS ====================
    
    def extract_document_text(self, file_path: str) -> Dict[str, Any]:
        """Extract text from medical document using OCR"""
        if not OCR_AVAILABLE:
            return {'success': False, 'error': 'OCR not available'}
        
        file_path = os.path.abspath(file_path)
        if not os.path.exists(file_path):
            return {'success': False, 'error': 'File not found', 'filename': os.path.basename(file_path)}
        
        return ocr_tool.process_document(file_path)
    
    # ==================== EMAIL TOOLS ====================
    
    def send_email(
        self,
        recipient_email: str,
        subject: str,
        message: str,
        detailed_content: Optional[str] = None,
        attach_pdf: bool = False
    ) -> Dict[str, Any]:
        """Send email to patient"""
        if not self.gmail_service.initialized:
            return {'success': False, 'error': 'Gmail not available'}
        
        try:
            if detailed_content and (attach_pdf or len(detailed_content) > 2000):
                if REPORTLAB_AVAILABLE:
                    pdf_bytes = self._generate_pdf(subject, detailed_content)
                    return self.gmail_service.send_email_with_pdf(
                        to=recipient_email,
                        subject=subject,
                        body=message,
                        pdf_data=pdf_bytes,
                        pdf_name=f"{subject.replace(' ', '_')}.pdf"
                    )
                else:
                    full_message = f"{message}\n\n{detailed_content}"
                    return self.gmail_service.send_email(recipient_email, subject, full_message)
            else:
                return self.gmail_service.send_email(recipient_email, subject, message)
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _generate_pdf(self, title: str, content: str) -> bytes:
        """Generate PDF content"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            textColor=colors.HexColor("#1E40AF"),
            alignment=TA_CENTER,
            spaceAfter=20
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontSize=11,
            alignment=TA_JUSTIFY,
            spaceAfter=12
        )
        
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph(content, body_style))
        
        doc.build(story)
        return buffer.getvalue()
    
    # ==================== CALENDAR TOOLS ====================
    
    def create_appointment(
        self,
        patient_name: str,
        patient_email: str,
        appointment_datetime: str,
        duration_minutes: int = 30,
        appointment_type: str = "consultation",
        reason: str = "",
        patient_phone: str = ""
    ) -> Dict[str, Any]:
        """Create appointment in Google Calendar"""
        return self.calendar_api.create_appointment(
            patient_name=patient_name,
            patient_email=patient_email,
            appointment_datetime=appointment_datetime,
            duration_minutes=duration_minutes,
            appointment_type=appointment_type,
            reason=reason,
            patient_phone=patient_phone
        )
    
    def list_appointments(
        self,
        start_date: str = None,
        end_date: str = None,
        max_results: int = 50
    ) -> Dict[str, Any]:
        """List appointments from Google Calendar"""
        return self.calendar_api.list_appointments(start_date, end_date, max_results)
    
    def get_appointment(self, appointment_id: str) -> Dict[str, Any]:
        """Get single appointment"""
        return self.calendar_api.get_appointment(appointment_id)
    
    def update_appointment(self, appointment_id: str, **kwargs) -> Dict[str, Any]:
        """Update appointment"""
        return self.calendar_api.update_appointment(appointment_id, **kwargs)
    
    def delete_appointment(self, appointment_id: str) -> Dict[str, Any]:
        """Delete appointment"""
        return self.calendar_api.delete_appointment(appointment_id)
    
    def cancel_appointment(self, appointment_id: str) -> Dict[str, Any]:
        """Cancel appointment"""
        return self.calendar_api.cancel_appointment(appointment_id)
    
    def check_availability(self, date: str, time: str) -> Dict[str, Any]:
        """Check time slot availability"""
        return self.calendar_api.check_availability(date, time)
    
    # ==================== PDF TOOLS ====================
    
    def generate_report(
        self,
        title: str,
        content: str,
        patient_name: str = None
    ) -> Dict[str, Any]:
        """Generate PDF report"""
        if not REPORTLAB_AVAILABLE:
            return {'success': False, 'error': 'PDF generation not available'}
        
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            story = []
            
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor("#1E40AF"),
                alignment=TA_CENTER,
                spaceAfter=20
            )
            
            body_style = ParagraphStyle(
                'CustomBody',
                parent=styles['BodyText'],
                fontSize=12,
                alignment=TA_JUSTIFY,
                spaceAfter=12
            )
            
            if patient_name:
                story.append(Paragraph(f"Patient: {patient_name}", title_style))
                story.append(Spacer(1, 0.2*inch))
            
            story.append(Paragraph(title, title_style))
            story.append(Spacer(1, 0.3*inch))
            story.append(Paragraph(content, body_style))
            story.append(Spacer(1, 0.5*inch))
            
            footer_style = ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.grey,
                alignment=TA_CENTER
            )
            story.append(Paragraph(
                f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                footer_style
            ))
            
            doc.build(story)
            pdf_bytes = buffer.getvalue()
            pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
            
            return {
                'success': True,
                'pdf_data': pdf_base64,
                'size_bytes': len(pdf_bytes)
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # ==================== STATUS ====================
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all services"""
        return {
            'server': 'running',
            'ocr_available': OCR_AVAILABLE,
            'gmail_available': self.gmail_service.initialized,
            'calendar_available': self.calendar_api.initialized,
            'pdf_available': REPORTLAB_AVAILABLE,
            'timestamp': datetime.now().isoformat()
        }


# Singleton
_mcp_tools = None

def get_mcp_tools() -> MCPTools:
    global _mcp_tools
    if _mcp_tools is None:
        _mcp_tools = MCPTools()
    return _mcp_tools
