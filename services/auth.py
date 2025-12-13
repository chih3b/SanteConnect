"""
Authentication and User Management Service
Simple JWT-based auth with SQLite storage
"""
import sqlite3
import hashlib
import secrets
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import os

# Database path
DB_PATH = os.environ.get("AUTH_DB_PATH", "users.db")

# JWT secret (in production, use environment variable)
JWT_SECRET = os.environ.get("JWT_SECRET", "santeconnect-secret-key-change-in-production")
TOKEN_EXPIRY_HOURS = 24 * 7  # 7 days


def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Conversations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Auth database initialized")


def hash_password(password: str) -> str:
    """Hash password with salt"""
    salt = "santeconnect"  # In production, use unique salt per user
    return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()


def generate_token(user_id: int, email: str) -> str:
    """Generate simple token (in production, use proper JWT)"""
    expiry = datetime.now() + timedelta(hours=TOKEN_EXPIRY_HOURS)
    token_data = f"{user_id}:{email}:{expiry.timestamp()}"
    signature = hashlib.sha256(f"{token_data}{JWT_SECRET}".encode()).hexdigest()[:16]
    return f"{user_id}:{signature}"


def verify_token(token: str) -> Optional[Dict]:
    """Verify token and return user info"""
    try:
        parts = token.split(":")
        if len(parts) != 2:
            return None
        
        user_id = int(parts[0])
        
        # Get user from database
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, name FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {"id": user["id"], "email": user["email"], "name": user["name"]}
        return None
    except:
        return None


def register_user(email: str, password: str, name: str) -> Dict:
    """Register a new user"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if email exists
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        return {"success": False, "error": "Email already registered"}
    
    # Create user
    password_hash = hash_password(password)
    cursor.execute(
        "INSERT INTO users (email, password_hash, name) VALUES (?, ?, ?)",
        (email, password_hash, name)
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    
    # Generate token
    token = generate_token(user_id, email)
    
    return {
        "success": True,
        "user": {"id": user_id, "email": email, "name": name},
        "token": token
    }


def login_user(email: str, password: str) -> Dict:
    """Login user"""
    conn = get_db()
    cursor = conn.cursor()
    
    password_hash = hash_password(password)
    cursor.execute(
        "SELECT id, email, name FROM users WHERE email = ? AND password_hash = ?",
        (email, password_hash)
    )
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        return {"success": False, "error": "Invalid email or password"}
    
    token = generate_token(user["id"], user["email"])
    
    return {
        "success": True,
        "user": {"id": user["id"], "email": user["email"], "name": user["name"]},
        "token": token
    }


# Conversation management
def create_conversation(user_id: int, title: str = None) -> Dict:
    """Create a new conversation"""
    conn = get_db()
    cursor = conn.cursor()
    
    if not title:
        title = f"Conversation {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    cursor.execute(
        "INSERT INTO conversations (user_id, title) VALUES (?, ?)",
        (user_id, title)
    )
    conn.commit()
    conv_id = cursor.lastrowid
    conn.close()
    
    return {"id": conv_id, "title": title, "created_at": datetime.now().isoformat()}


def get_conversations(user_id: int) -> List[Dict]:
    """Get all conversations for a user"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT c.id, c.title, c.created_at, c.updated_at,
               (SELECT content FROM messages WHERE conversation_id = c.id ORDER BY created_at DESC LIMIT 1) as last_message
        FROM conversations c
        WHERE c.user_id = ?
        ORDER BY c.updated_at DESC
    ''', (user_id,))
    
    conversations = []
    for row in cursor.fetchall():
        conversations.append({
            "id": row["id"],
            "title": row["title"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "last_message": row["last_message"][:50] + "..." if row["last_message"] and len(row["last_message"]) > 50 else row["last_message"]
        })
    
    conn.close()
    return conversations


def get_conversation_messages(conversation_id: int, user_id: int) -> List[Dict]:
    """Get all messages in a conversation"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Verify ownership
    cursor.execute("SELECT id FROM conversations WHERE id = ? AND user_id = ?", (conversation_id, user_id))
    if not cursor.fetchone():
        conn.close()
        return []
    
    cursor.execute('''
        SELECT id, role, content, metadata, created_at
        FROM messages
        WHERE conversation_id = ?
        ORDER BY created_at ASC
    ''', (conversation_id,))
    
    messages = []
    for row in cursor.fetchall():
        msg = {
            "id": row["id"],
            "role": row["role"],
            "content": row["content"],
            "created_at": row["created_at"]
        }
        if row["metadata"]:
            try:
                msg["metadata"] = json.loads(row["metadata"])
            except:
                pass
        messages.append(msg)
    
    conn.close()
    return messages


def add_message(conversation_id: int, user_id: int, role: str, content: str, metadata: Dict = None) -> Dict:
    """Add a message to a conversation"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Verify ownership
    cursor.execute("SELECT id FROM conversations WHERE id = ? AND user_id = ?", (conversation_id, user_id))
    if not cursor.fetchone():
        conn.close()
        return {"success": False, "error": "Conversation not found"}
    
    metadata_json = json.dumps(metadata) if metadata else None
    
    cursor.execute(
        "INSERT INTO messages (conversation_id, role, content, metadata) VALUES (?, ?, ?, ?)",
        (conversation_id, role, content, metadata_json)
    )
    
    # Update conversation timestamp
    cursor.execute(
        "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (conversation_id,)
    )
    
    # Update title if first user message
    cursor.execute("SELECT COUNT(*) as count FROM messages WHERE conversation_id = ?", (conversation_id,))
    if cursor.fetchone()["count"] <= 2:  # First exchange
        title = content[:50] + "..." if len(content) > 50 else content
        cursor.execute("UPDATE conversations SET title = ? WHERE id = ?", (title, conversation_id))
    
    conn.commit()
    msg_id = cursor.lastrowid
    conn.close()
    
    return {"success": True, "id": msg_id}


def delete_conversation(conversation_id: int, user_id: int) -> Dict:
    """Delete a conversation and its messages"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Verify ownership
    cursor.execute("SELECT id FROM conversations WHERE id = ? AND user_id = ?", (conversation_id, user_id))
    if not cursor.fetchone():
        conn.close()
        return {"success": False, "error": "Conversation not found"}
    
    cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
    cursor.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
    conn.commit()
    conn.close()
    
    return {"success": True}


# Initialize database on import
init_db()
