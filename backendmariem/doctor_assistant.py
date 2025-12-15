"""
doctor_assistant.py - AI Doctor Assistant with Groq LLM
Handles document processing, email, and appointments
"""
import os
import json
import logging
import uuid
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from the same directory as this file
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

logger = logging.getLogger(__name__)

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

from mcp_tools import get_mcp_tools
from explainable_ai import get_xai


class DoctorSession:
    """Manages doctor's session with memory and context"""
    
    def __init__(self, doctor_id: int, doctor_name: str = "Doctor"):
        self.session_id = str(uuid.uuid4())[:8]
        self.doctor_id = doctor_id
        self.doctor_name = doctor_name
        self.created_at = datetime.now()
        self.conversation_history = []
        self.uploaded_documents = {}
        self.current_document_content = ""
        self.current_document_name = ""
        self.appointments = []
        self.pending_email = None
    
    def add_message(self, role: str, content: str):
        self.conversation_history.append({
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })
    
    def add_document(self, filename: str, content: str):
        self.uploaded_documents[filename] = {
            'content': content,
            'uploaded_at': datetime.now().isoformat(),
            'length': len(content)
        }
        self.current_document_content = content
        self.current_document_name = filename
    
    def add_appointment(self, appointment: Dict):
        self.appointments.append(appointment)
    
    def get_recent_history(self, limit: int = 10) -> str:
        recent = self.conversation_history[-limit:]
        history = []
        for msg in recent:
            role_label = "DOCTOR" if msg['role'] == 'doctor' else "ASSISTANT"
            history.append(f"{role_label}: {msg['content'][:300]}")
        return "\n".join(history)


class DoctorAssistant:
    """AI Doctor Assistant with Groq LLM"""
    
    def __init__(self, groq_api_key: str, doctor_id: int, doctor_name: str = "Doctor"):
        if not GROQ_AVAILABLE:
            raise ImportError("Groq library not installed")
        
        self.groq_client = Groq(api_key=groq_api_key)
        self.model = "llama-3.3-70b-versatile"  # Best for tool calls
        self.mcp_tools = get_mcp_tools()
        self.session = DoctorSession(doctor_id, doctor_name)
        self.xai = get_xai()
        
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "extract_document_text",
                    "description": "Extract text from uploaded medical document using OCR.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string"}
                        },
                        "required": ["file_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "send_email",
                    "description": "Prepare email draft for doctor's review before sending.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "recipient_email": {"type": "string"},
                            "subject": {"type": "string"},
                            "message": {"type": "string"}
                        },
                        "required": ["recipient_email", "message"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "manage_appointment",
                    "description": "Check schedule or add appointment. For adding: ONLY use this tool when doctor provides ALL required info (patient_name, date, time). If any info is missing, ASK the doctor first - do NOT use this tool with missing data.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "action": {"type": "string", "enum": ["check", "add"]},
                            "date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                            "time": {"type": "string", "description": "Time in HH:MM format (24h)"},
                            "patient_name": {"type": "string", "description": "Patient's full name - REQUIRED for add action"},
                            "duration": {"type": "integer", "description": "Duration in minutes, default 30"}
                        },
                        "required": ["action"]
                    }
                }
            }
        ]
        
        logger.info(f"✅ Doctor Assistant initialized for {doctor_name}")
    
    async def confirm_send_email(self) -> str:
        """Send pending email after confirmation"""
        if not self.session.pending_email:
            return "❌ No pending email to send"
        
        email = self.session.pending_email
        result = self.mcp_tools.send_email(
            recipient_email=email['recipient'],
            subject=email['subject'],
            message=email['message'],
            detailed_content=email.get('detailed_content', ''),
            attach_pdf=email.get('attach_pdf', False)
        )
        
        self.session.pending_email = None
        
        if result.get('success'):
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            return f"""✅ Email successfully sent to {email['recipient']}

📧 **Delivery Confirmation**
• **Status:** Delivered
• **Recipient:** {email['recipient']}
• **Subject:** {email['subject']}
• **Timestamp:** {timestamp}"""
        else:
            return f"❌ Failed to send email: {result.get('error')}"
    
    async def cancel_email(self) -> str:
        """Cancel pending email"""
        if self.session.pending_email:
            recipient = self.session.pending_email['recipient']
            self.session.pending_email = None
            return f"❌ Email to {recipient} cancelled"
        return "No pending email to cancel"
    
    async def process_query(self, query: str, uploaded_file: str = None) -> Dict[str, Any]:
        """Process doctor's query with XAI tracing"""
        logger.info(f"👨‍⚕️ Doctor: {query}")
        self.session.add_message("doctor", query)
        
        trace_id = self.xai.start_trace(query)
        
        # Check for email confirmation
        query_lower = query.lower().strip()
        if query_lower in ['send', 'confirm', 'send it', 'send email', 'yes send', 'approve']:
            self.xai.add_reasoning_step("Email Confirmation", "Doctor confirmed email sending.", 1.0)
            result = await self.confirm_send_email()
            self.xai.finalize_trace(result)
            return {"response": result, "xai_trace": self.xai.get_trace_dict()}
        elif query_lower in ['cancel', 'cancel email', 'no', 'discard', "don't send"]:
            self.xai.add_reasoning_step("Email Cancellation", "Doctor cancelled email.", 1.0)
            result = await self.cancel_email()
            self.xai.finalize_trace(result)
            return {"response": result, "xai_trace": self.xai.get_trace_dict()}
        
        # Handle file upload
        if uploaded_file:
            self.xai.add_reasoning_step("Document Upload", f"Processing: {uploaded_file}", 0.95)
            await self._process_file(uploaded_file)
        
        context = self._build_context()
        
        user_message = f"""You are an expert medical AI assistant helping a doctor.

{context}

Doctor's query: {query}

RULES:
- extract_document_text: ONLY for NEW file uploads
- send_email: ONLY when doctor explicitly asks to send/compose an email
- manage_appointment: ONLY for schedule/appointment requests
- For questions about uploaded documents: Answer directly
- For medical questions: Answer directly
- Be concise and helpful

IMPORTANT FOR APPOINTMENTS:
- When checking schedule, use action="check" with the date
- Convert "today" to {datetime.now().strftime('%Y-%m-%d')}
- Convert "tomorrow" to {(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')}
- For "this week", use action="check" with date="this week"

CRITICAL FOR ADDING APPOINTMENTS:
- If doctor says "add appointment" without providing patient name, date, or time:
  DO NOT use the manage_appointment tool!
  Instead, ASK: "I'd be happy to add an appointment. Could you please provide:
  1. Patient's name
  2. Date (e.g., tomorrow, December 20th)
  3. Time (e.g., 10am, 2:30pm)
  4. Duration (optional, default is 30 minutes)"
- ONLY use manage_appointment with action="add" when ALL required info is provided

When composing emails to patients:
- Use warm, empathetic language
- Address patient by name
- Explain medical information clearly
- Provide next steps
- Be supportive and reassuring
"""
        
        messages = [{"role": "user", "content": user_message}]
        
        try:
            response = self.groq_client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools,
                tool_choice="auto",
                max_tokens=2000
            )
            
            message = response.choices[0].message
            
            # Check if tool calls exist (handle both finish_reason and tool_calls attribute)
            has_tool_calls = (
                response.choices[0].finish_reason == "tool_calls" or 
                (hasattr(message, 'tool_calls') and message.tool_calls)
            )
            
            if has_tool_calls and message.tool_calls:
                tool_calls = message.tool_calls
                tool_results = []
                
                self.xai.add_reasoning_step(
                    "LLM Tool Decision",
                    f"LLM determined {len(tool_calls)} tool(s) needed.",
                    0.9
                )
                
                for tool_call in tool_calls:
                    tool_name = tool_call.function.name
                    raw_args = tool_call.function.arguments
                    
                    try:
                        tool_args = json.loads(raw_args)
                    except json.JSONDecodeError:
                        # Try to fix common JSON issues
                        try:
                            fixed_args = raw_args.replace("\\'", "'").replace('\\"', '"')
                            tool_args = json.loads(fixed_args)
                        except:
                            logger.error(f"❌ Failed to parse tool args: {raw_args}")
                            tool_results.append("❌ Error parsing tool arguments. Please try rephrasing.")
                            continue
                    
                    self.xai.add_tool_decision(
                        tool_name=tool_name,
                        selected=True,
                        reasoning=f"Selected {tool_name} for query.",
                        confidence=0.85,
                        input_factors=list(tool_args.keys())
                    )
                    
                    result = await self._execute_tool(tool_name, tool_args)
                    tool_results.append(result)
                
                final_response = "\n".join(tool_results)
            else:
                final_response = message.content or "I couldn't generate a response. Please try again."
                self.xai.add_reasoning_step(
                    "Direct Response",
                    "LLM answered directly without tools.",
                    0.85
                )
            
            self.session.add_message("assistant", final_response)
            self.xai.finalize_trace(final_response)
            
            return {
                "response": final_response,
                "xai_trace": self.xai.get_trace_dict()
            }
        
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            self.xai.add_reasoning_step("Error", str(e), 0.0)
            self.xai.finalize_trace(str(e))
            return {
                "response": f"❌ Error: {str(e)}",
                "xai_trace": self.xai.get_trace_dict()
            }
    
    def _build_context(self) -> str:
        context_parts = []
        
        if self.session.current_document_content:
            max_chars = 8000
            content = self.session.current_document_content
            if len(content) > max_chars:
                content = content[:max_chars] + "\n\n[Document truncated]"
            
            context_parts.append(f"""
UPLOADED DOCUMENT: {self.session.current_document_name}
Content:
{content}
""")
        
        if self.session.appointments:
            recent = self.session.appointments[-5:]
            appts_str = "\n".join([
                f"- {a.get('date')} {a.get('time')}: {a.get('patient_name', 'Patient')}"
                for a in recent
            ])
            context_parts.append(f"RECENT APPOINTMENTS:\n{appts_str}")
        
        history = self.session.get_recent_history(3)
        if history:
            context_parts.append(f"RECENT CONVERSATION:\n{history}")
        
        return "\n".join(context_parts)
    
    async def _process_file(self, file_path: str):
        result = self.mcp_tools.extract_document_text(file_path)
        if result.get('success'):
            content = result.get('text', '')
            filename = result.get('filename', '')
            self.session.add_document(filename, content)
            logger.info(f"✅ Document processed: {filename}")
    
    async def _execute_tool(self, tool_name: str, tool_args: Dict) -> str:
        try:
            if tool_name == "extract_document_text":
                result = self.mcp_tools.extract_document_text(tool_args.get('file_path', ''))
                if result.get('success'):
                    self.session.add_document(result.get('filename', ''), result.get('text', ''))
                    return f"✅ Document extracted: {result.get('filename')} ({result.get('length')} chars)"
                return f"❌ Failed: {result.get('error')}"
            
            elif tool_name == "send_email":
                recipient = tool_args.get('recipient_email', '')
                subject = tool_args.get('subject', 'Medical Information')
                message = tool_args.get('message', '').replace("\\'", "'").replace('\\"', '"')
                
                self.session.pending_email = {
                    'recipient': recipient,
                    'subject': subject,
                    'message': message,
                    'detailed_content': tool_args.get('detailed_content', ''),
                    'attach_pdf': tool_args.get('attach_pdf', False)
                }
                
                return f"""📧 **Email Preview - Awaiting Your Approval**

**To:** {recipient}
**Subject:** {subject}

**Message:**
{message}

---
Reply with:
- "send" or "confirm" to send
- "cancel" to discard"""
            
            elif tool_name == "manage_appointment":
                action = tool_args.get('action')
                
                if action == "check":
                    date = tool_args.get('date', '')
                    
                    # Handle "this week"
                    if date and 'week' in date.lower():
                        today = datetime.now()
                        start_of_week = today - timedelta(days=today.weekday())
                        end_of_week = start_of_week + timedelta(days=6)
                        
                        result = self.mcp_tools.list_appointments(
                            start_date=start_of_week.strftime('%Y-%m-%d'),
                            end_date=end_of_week.strftime('%Y-%m-%d')
                        )
                        
                        if result.get('success') and result.get('appointments'):
                            appts = result['appointments']
                            appts_str = "\n".join([
                                f"- {a['appointment_date'][:10]} at {a['appointment_date'][11:16]}: {a['patient_name']}"
                                for a in appts
                            ])
                            return f"📅 Schedule for this week:\n{appts_str}"
                        return "📅 No appointments this week."
                    
                    # Single day check
                    date = self._convert_date(date)
                    result = self.mcp_tools.list_appointments(start_date=date, end_date=date)
                    
                    if result.get('success') and result.get('appointments'):
                        appts = result['appointments']
                        appts_str = "\n".join([
                            f"- {a['appointment_date'][11:16]}: {a['patient_name']}"
                            for a in appts
                        ])
                        return f"📅 Schedule for {date}:\n{appts_str}"
                    return f"📅 No appointments on {date}."
                
                elif action == "add":
                    date = self._convert_date(tool_args.get('date', ''))
                    time = self._convert_time(tool_args.get('time', ''))
                    patient_name = tool_args.get('patient_name', 'Patient')
                    duration = tool_args.get('duration', 30)
                    
                    if isinstance(duration, str):
                        duration = int(''.join(filter(str.isdigit, duration))) or 30
                    
                    appointment_datetime = f"{date}T{time}:00"
                    
                    result = self.mcp_tools.create_appointment(
                        patient_name=patient_name,
                        patient_email='',
                        appointment_datetime=appointment_datetime,
                        duration_minutes=duration,
                        appointment_type='consultation'
                    )
                    
                    if result.get('success'):
                        self.session.add_appointment({
                            'date': date,
                            'time': time,
                            'patient_name': patient_name,
                            'duration': duration
                        })
                        return f"✅ Appointment added: {patient_name} on {date} at {time} ({duration} min)"
                    return f"⚠️ Failed to add appointment: {result.get('error')}"
            
            return f"❌ Unknown tool: {tool_name}"
        
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def _convert_date(self, date_str: str) -> str:
        """Convert relative dates to YYYY-MM-DD"""
        if not date_str:
            return datetime.now().strftime('%Y-%m-%d')
        
        if date_str[0].isdigit():
            return date_str
        
        today = datetime.now()
        date_lower = date_str.lower()
        
        if 'tomorrow' in date_lower:
            return (today + timedelta(days=1)).strftime('%Y-%m-%d')
        elif 'today' in date_lower:
            return today.strftime('%Y-%m-%d')
        elif 'next week' in date_lower:
            return (today + timedelta(days=7)).strftime('%Y-%m-%d')
        
        return today.strftime('%Y-%m-%d')
    
    def _convert_time(self, time_str: str) -> str:
        """Convert time to HH:MM format"""
        if not time_str:
            return "09:00"
        
        if ':' in time_str:
            return time_str[:5]
        
        time_lower = time_str.lower().strip()
        match = re.match(r'(\d+)\s*(am|pm)?', time_lower)
        if match:
            hour = int(match.group(1))
            period = match.group(2)
            if period == 'pm' and hour != 12:
                hour += 12
            elif period == 'am' and hour == 12:
                hour = 0
            return f"{hour:02d}:00"
        
        return "09:00"


# Store assistant instances per doctor
_assistants: Dict[int, DoctorAssistant] = {}

def get_doctor_assistant(doctor_id: int, doctor_name: str = "Doctor") -> DoctorAssistant:
    """Get or create assistant for a doctor"""
    global _assistants
    
    if doctor_id not in _assistants:
        groq_api_key = os.getenv("GROQ_API_KEY", "")
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY not configured")
        
        _assistants[doctor_id] = DoctorAssistant(groq_api_key, doctor_id, doctor_name)
    
    return _assistants[doctor_id]
