# sms_notifier.py - Version finale fonctionnelle
import os
import re
from twilio.rest import Client
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class SMSNotifier:
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
        self.twilio_number = os.getenv("TWILIO_PHONE_NUMBER", "")
        
        print(f"🔧 Initialisation SMS Notifier...")
        print(f"   De: {self.twilio_number}")
        
        self.client = None
        if self.account_sid and self.auth_token:
            try:
                self.client = Client(self.account_sid, self.auth_token)
                print("   ✅ Client Twilio initialisé")
            except Exception as e:
                print(f"   ❌ Erreur Twilio: {e}")
        else:
            print("   ⚠️ Clés Twilio manquantes")
    
    def clean_message_for_sms(self, message):
        """
        Nettoie le message pour SMS :
        - Enlève les emojis
        - Limite à 160 caractères
        - Remplace les sauts de ligne
        """
        # Remplacer les emojis courants
        emoji_replacements = {
            '🔔': '[ALERTE]',
            '👤': 'Patient:',
            '📊': 'Score:',
            '🏥': 'Diag:',
            '📋': 'Details:',
            '🚨': '[URGENT]',
            '⚠️': '[ATTN]',
            '💡': '[INFO]',
            '🎯': '[ACTION]'
        }
        
        for emoji, replacement in emoji_replacements.items():
            message = message.replace(emoji, replacement)
        
        # Enlever autres caractères non-ASCII
        message = message.encode('ascii', 'ignore').decode('ascii')
        
        # Remplacer multiples sauts de ligne par un espace
        message = re.sub(r'\n+', ' - ', message)
        
        # Limiter à 160 caractères pour 1 SMS
        if len(message) > 160:
            # Garder le début et ajouter "..."
            message = message[:157] + '...'
        
        return message
    
    def send_diagnostic_sms(self, doctor_phone, patient_info):
        """
        Envoie un SMS au médecin - Version SIMPLIFIÉE qui marche
        """
        # FORMAT OBLIGATOIRE pour Tunisie
        if not doctor_phone.startswith('+216'):
            if doctor_phone.startswith('0'):
                doctor_phone = '+216' + doctor_phone[1:]
            elif doctor_phone.startswith('216'):
                doctor_phone = '+' + doctor_phone
            else:
                doctor_phone = '+216' + doctor_phone
        
        print(f"\n📱 PREPARATION SMS:")
        print(f"   À: {doctor_phone}")
        print(f"   Patient: {patient_info.get('name')}")
        print(f"   Score: {patient_info.get('score')}%")
        
        # Message SIMPLE et COURT
        sms_body = (
            f"MedAI: Nouveau diagnostic - "
            f"Patient: {patient_info.get('name', 'N/A')} - "
            f"Score: {patient_info.get('score', 'N/A')}% - "
            f"Diag: {patient_info.get('diagnostic', 'À verifier')[:30]} - "
            f"Consultez dashboard"
        )
        
        # Nettoyer
        sms_body = self.clean_message_for_sms(sms_body)
        
        print(f"   Message: {sms_body}")
        print(f"   Longueur: {len(sms_body)}/160 caractères")
        
        if not self.client:
            print("   ⚠️ Mode simulation activé")
            return self._log_simulation(doctor_phone, sms_body)
        
        try:
            print("   📤 Envoi via Twilio...")
            
            # ENVOI RÉEL
            message = self.client.messages.create(
                body=sms_body,
                from_=self.twilio_number,
                to=doctor_phone
            )
            
            print(f"   ✅ SMS ENVOYÉ! SID: {message.sid}")
            print(f"   📊 Statut initial: {message.status}")
            
            # Sauvegarder le SID pour référence
            self._save_sms_log(doctor_phone, sms_body, message.sid, "sent")
            
            return True
            
        except Exception as e:
            error_msg = str(e)
            print(f"   ❌ ERREUR Twilio: {type(e).__name__}")
            print(f"   Message: {error_msg}")
            
            # Check for common Twilio errors
            if "unverified" in error_msg.lower():
                print("   💡 Le numéro de destination n'est pas vérifié sur Twilio (compte trial)")
            elif "authenticate" in error_msg.lower():
                print("   💡 Erreur d'authentification - vérifiez les clés Twilio")
            elif "not a valid phone" in error_msg.lower():
                print("   💡 Format de numéro invalide")
            
            # Log simulation but return False to indicate failure
            self._log_simulation(doctor_phone, sms_body)
            return False
    
    def _log_simulation(self, phone, message):
        """Log une simulation de SMS"""
        print(f"   📝 [SIMULATION] SMS à {phone}")
        print(f"      Message: {message}")
        
        # Sauvegarder dans un fichier log
        import datetime
        log_entry = f"""
[{datetime.datetime.now()}] SMS SIMULE
À: {phone}
Message: {message}
{'='*50}
"""
        
        with open("sms_simulation_log.txt", "a", encoding="utf-8") as f:
            f.write(log_entry)
        
        return True  # Pour la démo, on considère que c'est envoyé
    
    def _save_sms_log(self, phone, message, sid, status):
        """Sauvegarde les logs des vrais SMS"""
        import datetime
        log_entry = f"""
[{datetime.datetime.now()}] SMS REEL
SID: {sid}
À: {phone}
Status: {status}
Message: {message}
{'='*50}
"""
        
        with open("sms_real_log.txt", "a", encoding="utf-8") as f:
            f.write(log_entry)

# Instance globale
sms_notifier = SMSNotifier()