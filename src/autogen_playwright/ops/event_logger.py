"""
Event logging system for AutoGen 0.4 that captures events and stores them for analysis.
"""
import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Define EventPayload as a type alias
EventPayload = Dict[str, Any]

logger = logging.getLogger(__name__)

class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles non-serializable objects."""
    def default(self, obj):
        # Handle objects with __dict__ attribute
        if hasattr(obj, '__dict__'):
            return {k: v for k, v in obj.__dict__.items() 
                   if not k.startswith('_') and not callable(v)}
        # Handle objects with to_dict method
        elif hasattr(obj, 'to_dict'):
            return obj.to_dict()
        # Handle objects with model_dump method (Pydantic v2)
        elif hasattr(obj, 'model_dump'):
            return obj.model_dump()
        # Handle objects with dict method (Pydantic v1)
        elif hasattr(obj, 'dict') and callable(obj.dict):
            return obj.dict()
        # Handle other types
        try:
            return str(obj)
        except:
            return f"<non-serializable: {type(obj).__name__}>"

def serialize_payload(payload: Dict[str, Any]) -> str:
    """Serialize a payload to JSON, handling non-serializable objects."""
    try:
        return json.dumps(payload, cls=CustomJSONEncoder)
    except Exception as e:
        logger.error(f"Error serializing payload: {e}")
        # Fallback: convert to string representation
        return json.dumps({"error": "Could not serialize payload", 
                          "payload_str": str(payload)})

class SQLiteEventLogger:
    """
    Event logger that logs AutoGen events to a SQLite database.
    
    This class captures events and stores them in a SQLite database
    for later analysis. It's particularly useful for tracking token usage,
    conversation flow, and performance metrics.
    """
    
    def __init__(self, db_path: Union[str, Path] = "runtime_logs/autogen_logs.db"):
        """
        Initialize the SQLite event logger.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        self._ensure_db_exists()
        
    def _ensure_db_exists(self):
        """Ensure the database and required tables exist."""
        # Create directory if it doesn't exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create database and tables if they don't exist
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Create events table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL,
            event_type TEXT,
            session_id TEXT,
            agent_id TEXT,
            payload TEXT
        )
        ''')
        
        # Create LLM calls table specifically for token tracking
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS llm_calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL,
            session_id TEXT,
            agent_id TEXT,
            model TEXT,
            prompt_tokens INTEGER,
            completion_tokens INTEGER,
            total_tokens INTEGER,
            request TEXT,
            response TEXT
        )
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info(f"Initialized SQLite event logger with database at {self.db_path}")
    
    def log_event(self, event_type: str, event_payload: Dict[str, Any]):
        """
        Log an event to the database.
        
        Args:
            event_type: The type of event
            event_payload: The event payload
        """
        try:
            # Extract session_id and agent_id if available
            session_id = event_payload.get("session_id", None)
            agent_id = event_payload.get("agent_id", None)
            
            # Log all events to the events table
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT INTO events (timestamp, event_type, session_id, agent_id, payload) VALUES (?, ?, ?, ?, ?)",
                (
                    time.time(),
                    event_type,
                    session_id,
                    agent_id,
                    serialize_payload(event_payload)
                )
            )
            
            # Special handling for LLM calls to track token usage
            if event_type == "LLMCall":
                # Extract token usage information
                prompt_tokens = event_payload.get("prompt_tokens", 0)
                completion_tokens = event_payload.get("completion_tokens", 0)
                total_tokens = prompt_tokens + completion_tokens
                
                # Extract model information
                model = None
                if "response" in event_payload and isinstance(event_payload["response"], dict):
                    model = event_payload["response"].get("model", None)
                
                # Extract request and response
                request = serialize_payload(event_payload.get("messages", []))
                response = serialize_payload(event_payload.get("response", {}))
                
                cursor.execute(
                    """
                    INSERT INTO llm_calls 
                    (timestamp, session_id, agent_id, model, prompt_tokens, completion_tokens, total_tokens, request, response) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        time.time(),
                        session_id,
                        agent_id,
                        model,
                        prompt_tokens,
                        completion_tokens,
                        total_tokens,
                        request,
                        response
                    )
                )
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error logging event: {str(e)}")
    
    async def on_event(self, event_type: str, event_payload: EventPayload):
        """
        Handle an AutoGen event by logging it to the database.
        
        Args:
            event_type: The type of event
            event_payload: The event payload
        """
        self.log_event(event_type, event_payload)
    
    def get_session_stats(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get token usage statistics for a session or all sessions.
        
        Args:
            session_id: Optional session ID to filter by
        
        Returns:
            Dictionary containing token usage statistics
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        query = "SELECT SUM(prompt_tokens), SUM(completion_tokens), SUM(total_tokens), COUNT(*) FROM llm_calls"
        params = []
        
        if session_id:
            query += " WHERE session_id = ?"
            params.append(session_id)
        
        cursor.execute(query, params)
        result = cursor.fetchone()
        
        if not result or result[0] is None:
            stats = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "request_count": 0,
                "prompt_cost": 0,
                "completion_cost": 0,
                "total_cost": 0
            }
        else:
            prompt_tokens, completion_tokens, total_tokens, request_count = result
            
            # Calculate costs (using OpenAI's pricing for GPT-4)
            prompt_cost = prompt_tokens * 0.03 / 1000  # $0.03 per 1k tokens
            completion_cost = completion_tokens * 0.06 / 1000  # $0.06 per 1k tokens
            
            stats = {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "request_count": request_count,
                "prompt_cost": round(prompt_cost, 4),
                "completion_cost": round(completion_cost, 4),
                "total_cost": round(prompt_cost + completion_cost, 4)
            }
        
        if session_id:
            stats["session_id"] = session_id
        
        conn.close()
        return stats
    
    def get_conversation_flow(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get the conversation flow for a specific session.
        
        Args:
            session_id: Session ID to analyze
        
        Returns:
            List of dictionaries containing conversation messages
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # This enables column access by name
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM events WHERE session_id = ? ORDER BY timestamp",
            (session_id,)
        )
        
        events = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # Process events to extract conversation flow
        messages = []
        for event in events:
            if event["event_type"] in ["MessageReceived", "MessageSent"]:
                try:
                    payload = json.loads(event["payload"])
                    if "content" in payload:
                        messages.append({
                            "timestamp": event["timestamp"],
                            "agent_id": event["agent_id"],
                            "type": event["event_type"],
                            "content": payload["content"]
                        })
                except (json.JSONDecodeError, KeyError):
                    pass
        
        return messages
    
    def print_session_summary(self, session_id: Optional[str] = None):
        """
        Print a summary of the session statistics.
        
        Args:
            session_id: Optional session ID to filter by
        """
        stats = self.get_session_stats(session_id)
        
        print("\n" + "=" * 50)
        print(f"SESSION SUMMARY: {session_id if session_id else 'All Sessions'}")
        print("=" * 50)
        print(f"Total Requests:      {stats['request_count']}")
        print(f"Prompt Tokens:       {stats['prompt_tokens']}")
        print(f"Completion Tokens:   {stats['completion_tokens']}")
        print(f"Total Tokens:        {stats['total_tokens']}")
        print("-" * 50)
        print(f"Prompt Cost:         ${stats['prompt_cost']}")
        print(f"Completion Cost:     ${stats['completion_cost']}")
        print(f"Total Cost:          ${stats['total_cost']}")
        print("=" * 50) 