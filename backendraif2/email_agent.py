"""
Agent d'envoi d'emails
Envoie les rapports médicaux aux médecins
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict
from config import config


class EmailAgent:
    """Agent pour envoyer les rapports médicaux par email"""
    
    def __init__(self):
        self.smtp_server = config.SMTP_SERVER
        self.smtp_port = config.SMTP_PORT
        self.sender_email = config.SENDER_EMAIL
        self.sender_password = config.SENDER_PASSWORD
        self.sender_name = "Dr. Raif - Assistant Médical IA"
        
        print("✅ EmailAgent initialisé")
        print(f"   Serveur SMTP: {self.smtp_server}:{self.smtp_port}")
    
    def send_medical_report(
        self,
        doctor_email: str,
        patient_name: str,
        report_html: str,
        report_text: str,
        session_id: str,
        urgency_level: str = "Modéré"
    ) -> Dict:
        """Envoie un rapport médical par email"""
        print(f"📧 Envoi du rapport médical à {doctor_email}...")
        
        try:
            msg = self._create_email_message(
                doctor_email, patient_name, report_html, report_text, session_id, urgency_level
            )
            result = self._send_via_smtp(msg, doctor_email)
            
            if result["success"]:
                print(f"✅ Email envoyé avec succès à {doctor_email}")
            else:
                print(f"❌ Échec envoi email: {result['message']}")
            
            return result
            
        except Exception as e:
            error_msg = f"Erreur envoi email: {str(e)}"
            print(f"❌ {error_msg}")
            return {"success": False, "message": error_msg}
    
    def _create_email_message(
        self,
        doctor_email: str,
        patient_name: str,
        report_html: str,
        report_text: str,
        session_id: str,
        urgency_level: str
    ) -> MIMEMultipart:
        """Crée le message email"""
        urgency_emoji = "🚨" if "critique" in urgency_level.lower() else \
                       "⚠️" if "élevé" in urgency_level.lower() else "ℹ️"
        
        subject = f"{urgency_emoji} Rapport Médical IA - {patient_name} - Urgence: {urgency_level}"
        
        msg = MIMEMultipart('alternative')
        msg['From'] = f"{self.sender_name} <{self.sender_email}>"
        msg['To'] = doctor_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(report_text, 'plain', 'utf-8'))
        msg.attach(MIMEText(report_html, 'html', 'utf-8'))
        
        return msg
    
    def _send_via_smtp(self, msg: MIMEMultipart, recipient_email: str) -> Dict:
        """Envoie l'email via SMTP"""
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            return {"success": True, "message": f"Email envoyé à {recipient_email}"}
            
        except smtplib.SMTPAuthenticationError:
            return {"success": False, "message": "Erreur d'authentification SMTP"}
        except smtplib.SMTPRecipientsRefused:
            return {"success": False, "message": f"Destinataire refusé: {recipient_email}"}
        except smtplib.SMTPException as e:
            return {"success": False, "message": f"Erreur SMTP: {str(e)}"}
        except Exception as e:
            return {"success": False, "message": f"Erreur: {str(e)}"}


# Instance globale
email_agent = EmailAgent()
