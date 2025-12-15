"""
google_calendar_api.py - Google Calendar Integration
Single source of truth for appointments
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

# Try to import Google API libraries
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    import pickle
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False
    logger.warning("⚠️ Google API libraries not available")

SCOPES = ['https://www.googleapis.com/auth/calendar']


class GoogleCalendarAPI:
    """Google Calendar API wrapper for appointment management"""
    
    def __init__(self):
        self.service = None
        self.initialized = False
        self.credentials_file = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
        self.token_file = os.getenv("CALENDAR_TOKEN_FILE", "calendar_token.json")
    
    def initialize(self) -> bool:
        """Initialize Google Calendar API"""
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
                    logger.info("✅ Loaded calendar token from JSON")
                except Exception:
                    try:
                        # Fall back to pickle format
                        with open(self.token_file, 'rb') as token:
                            creds = pickle.load(token)
                        logger.info("✅ Loaded calendar token from pickle")
                    except Exception as e:
                        logger.warning(f"⚠️ Could not load calendar token: {e}")
                        creds = None
            
            # Refresh if expired
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    logger.info("✅ Calendar token refreshed")
                except Exception as e:
                    logger.warning(f"⚠️ Could not refresh calendar token: {e}")
                    creds = None
            
            if not creds or not creds.valid:
                logger.warning("⚠️ Calendar: No valid credentials")
                return False
            
            self.service = build('calendar', 'v3', credentials=creds)
            self.initialized = True
            logger.info("✅ Google Calendar API initialized")
            return True
        
        except Exception as e:
            logger.error(f"❌ Calendar init failed: {e}")
            return False
    
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
        if not self.initialized:
            return {'success': False, 'error': 'Calendar not initialized'}
        
        try:
            # Parse datetime
            if 'T' in appointment_datetime:
                start_dt = datetime.fromisoformat(appointment_datetime.replace('Z', ''))
            else:
                start_dt = datetime.strptime(appointment_datetime, '%Y-%m-%d %H:%M')
            
            end_dt = start_dt + timedelta(minutes=duration_minutes)
            
            event = {
                'summary': f"[{appointment_type.upper()}] {patient_name}",
                'description': f"Patient: {patient_name}\nEmail: {patient_email}\nPhone: {patient_phone}\nReason: {reason}",
                'start': {
                    'dateTime': start_dt.isoformat(),
                    'timeZone': 'Africa/Tunis',
                },
                'end': {
                    'dateTime': end_dt.isoformat(),
                    'timeZone': 'Africa/Tunis',
                },
                'attendees': [{'email': patient_email}] if patient_email else [],
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},
                        {'method': 'popup', 'minutes': 30},
                    ],
                },
            }
            
            result = self.service.events().insert(calendarId='primary', body=event).execute()
            
            return {
                'success': True,
                'id': result['id'],
                'patient_name': patient_name,
                'patient_email': patient_email,
                'appointment_date': appointment_datetime,
                'duration_minutes': duration_minutes,
                'appointment_type': appointment_type,
                'status': 'scheduled',
                'html_link': result.get('htmlLink', ''),
                'created_at': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"❌ Create appointment failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def list_appointments(
        self,
        start_date: str = None,
        end_date: str = None,
        max_results: int = 50
    ) -> Dict[str, Any]:
        """List appointments from Google Calendar"""
        if not self.initialized:
            return {'success': False, 'error': 'Calendar not initialized', 'appointments': []}
        
        try:
            if start_date:
                time_min = datetime.strptime(start_date, '%Y-%m-%d').isoformat() + 'Z'
            else:
                time_min = datetime.utcnow().isoformat() + 'Z'
            
            if end_date:
                time_max = (datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)).isoformat() + 'Z'
            else:
                time_max = (datetime.utcnow() + timedelta(days=30)).isoformat() + 'Z'
            
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            appointments = []
            
            for event in events:
                apt = self._parse_event(event)
                if apt:
                    appointments.append(apt)
            
            return {'success': True, 'appointments': appointments}
        
        except Exception as e:
            logger.error(f"❌ List appointments failed: {e}")
            return {'success': False, 'error': str(e), 'appointments': []}
    
    def get_appointment(self, event_id: str) -> Dict[str, Any]:
        """Get single appointment by ID"""
        if not self.initialized:
            return {'success': False, 'error': 'Calendar not initialized'}
        
        try:
            event = self.service.events().get(calendarId='primary', eventId=event_id).execute()
            apt = self._parse_event(event)
            return {'success': True, 'appointment': apt}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def update_appointment(self, event_id: str, **kwargs) -> Dict[str, Any]:
        """Update appointment"""
        if not self.initialized:
            return {'success': False, 'error': 'Calendar not initialized'}
        
        try:
            event = self.service.events().get(calendarId='primary', eventId=event_id).execute()
            
            if kwargs.get('patient_name'):
                apt_type = kwargs.get('appointment_type', 'consultation')
                event['summary'] = f"[{apt_type.upper()}] {kwargs['patient_name']}"
            
            if kwargs.get('appointment_datetime'):
                dt = kwargs['appointment_datetime']
                if 'T' in dt:
                    start_dt = datetime.fromisoformat(dt.replace('Z', ''))
                else:
                    start_dt = datetime.strptime(dt, '%Y-%m-%d %H:%M')
                
                duration = kwargs.get('duration_minutes', 30)
                end_dt = start_dt + timedelta(minutes=duration)
                
                event['start'] = {'dateTime': start_dt.isoformat(), 'timeZone': 'Africa/Tunis'}
                event['end'] = {'dateTime': end_dt.isoformat(), 'timeZone': 'Africa/Tunis'}
            
            result = self.service.events().update(
                calendarId='primary', eventId=event_id, body=event
            ).execute()
            
            return {'success': True, 'appointment': self._parse_event(result)}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def delete_appointment(self, event_id: str) -> Dict[str, Any]:
        """Delete appointment"""
        if not self.initialized:
            return {'success': False, 'error': 'Calendar not initialized'}
        
        try:
            self.service.events().delete(calendarId='primary', eventId=event_id).execute()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def cancel_appointment(self, event_id: str) -> Dict[str, Any]:
        """Cancel appointment (mark as cancelled)"""
        if not self.initialized:
            return {'success': False, 'error': 'Calendar not initialized'}
        
        try:
            event = self.service.events().get(calendarId='primary', eventId=event_id).execute()
            event['summary'] = f"[CANCELLED] {event.get('summary', '')}"
            event['status'] = 'cancelled'
            
            result = self.service.events().update(
                calendarId='primary', eventId=event_id, body=event
            ).execute()
            
            return {'success': True, 'appointment': self._parse_event(result)}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def check_availability(self, date: str, time: str) -> Dict[str, Any]:
        """Check if time slot is available"""
        if not self.initialized:
            return {'success': False, 'error': 'Calendar not initialized', 'available': False}
        
        try:
            dt = datetime.strptime(f"{date} {time}", '%Y-%m-%d %H:%M')
            time_min = dt.isoformat() + 'Z'
            time_max = (dt + timedelta(minutes=30)).isoformat() + 'Z'
            
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True
            ).execute()
            
            events = events_result.get('items', [])
            available = len(events) == 0
            
            return {'success': True, 'available': available, 'conflicts': len(events)}
        
        except Exception as e:
            return {'success': False, 'error': str(e), 'available': False}
    
    def _parse_event(self, event: Dict) -> Dict[str, Any]:
        """Parse Google Calendar event to appointment format"""
        try:
            start = event.get('start', {})
            start_dt = start.get('dateTime', start.get('date', ''))
            
            end = event.get('end', {})
            end_dt = end.get('dateTime', end.get('date', ''))
            
            # Calculate duration
            duration = 30
            if start_dt and end_dt and 'T' in start_dt:
                start_time = datetime.fromisoformat(start_dt.replace('Z', '').split('+')[0])
                end_time = datetime.fromisoformat(end_dt.replace('Z', '').split('+')[0])
                duration = int((end_time - start_time).total_seconds() / 60)
            
            # Parse description for patient info
            description = event.get('description', '')
            patient_name = ''
            patient_email = ''
            patient_phone = ''
            
            for line in description.split('\n'):
                if line.startswith('Patient:'):
                    patient_name = line.replace('Patient:', '').strip()
                elif line.startswith('Email:'):
                    patient_email = line.replace('Email:', '').strip()
                elif line.startswith('Phone:'):
                    patient_phone = line.replace('Phone:', '').strip()
            
            # Get appointment type from summary
            summary = event.get('summary', '')
            appointment_type = 'consultation'
            if '[' in summary and ']' in summary:
                apt_type = summary.split('[')[1].split(']')[0].lower()
                if apt_type not in ['cancelled']:
                    appointment_type = apt_type
                if not patient_name:
                    patient_name = summary.split(']')[-1].strip()
            
            status = 'scheduled'
            if event.get('status') == 'cancelled' or 'CANCELLED' in summary:
                status = 'cancelled'
            
            return {
                'id': event['id'],
                'doctor_id': 'primary',
                'patient_name': patient_name or summary,
                'patient_email': patient_email,
                'patient_phone': patient_phone,
                'appointment_date': start_dt,
                'duration_minutes': duration,
                'appointment_type': appointment_type,
                'reason': '',
                'status': status,
                'html_link': event.get('htmlLink', ''),
                'created_at': event.get('created', '')
            }
        except Exception as e:
            logger.error(f"Parse event error: {e}")
            return None


# Singleton instance
_calendar_api = None

def get_calendar_api() -> GoogleCalendarAPI:
    global _calendar_api
    if _calendar_api is None:
        _calendar_api = GoogleCalendarAPI()
        _calendar_api.initialize()
    return _calendar_api
