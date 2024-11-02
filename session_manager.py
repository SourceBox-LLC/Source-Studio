import os
import time
import shutil
import logging
from datetime import datetime

class SessionManager:
    def __init__(self, base_dir="static", expiration_hours=24):
        self.base_dir = base_dir
        self.expiration_seconds = expiration_hours * 3600
        self._init_directories()
        
    def _init_directories(self):
        """Initialize the base directory structure"""
        os.makedirs(self.base_dir, exist_ok=True)
        os.makedirs(os.path.join(self.base_dir, "user_files"), exist_ok=True)
        
    def get_session_dir(self, session_id):
        """Get or create session directory"""
        session_dir = os.path.join(self.base_dir, "user_files", session_id)
        os.makedirs(session_dir, exist_ok=True)
        return session_dir
        
    def cleanup_expired_sessions(self):
        """Remove expired session directories"""
        current_time = time.time()
        user_files_dir = os.path.join(self.base_dir, "user_files")
        
        for session_id in os.listdir(user_files_dir):
            session_dir = os.path.join(user_files_dir, session_id)
            if os.path.isdir(session_dir):
                # Check directory age
                dir_age = current_time - os.path.getctime(session_dir)
                if dir_age > self.expiration_seconds:
                    try:
                        shutil.rmtree(session_dir)
                        logging.info(f"Cleaned up expired session: {session_id}")
                    except Exception as e:
                        logging.error(f"Error cleaning up session {session_id}: {e}") 