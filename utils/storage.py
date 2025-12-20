"""
SQLite-based Storage for Differential Analysis
Stores URL hashes to minimize LLM API calls by detecting actual changes.
"""

import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass


@dataclass
class ChangeRecord:
    """Represents a detected change record."""
    id: int
    url: str
    content_hash: str
    content_preview: str
    detected_at: datetime
    analysis_result: Optional[str] = None


class HashStorage:
    """
    SQLite-based storage for URL content hashes.
    Implements differential analysis to avoid redundant LLM calls.
    """
    
    def __init__(self, db_path: str = "./data/competitor_monitor.db"):
        """Initialize storage with database path."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self) -> None:
        """Create database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Table for current state (latest hash per URL)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS url_hashes (
                    url TEXT PRIMARY KEY,
                    content_hash TEXT NOT NULL,
                    last_content TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table for change history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS change_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    content_preview TEXT,
                    analysis_result TEXT,
                    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    @staticmethod
    def compute_hash(content: str) -> str:
        """
        Compute SHA-256 hash of content.
        Normalizes whitespace before hashing for consistent comparisons.
        """
        # Normalize whitespace to avoid false positives from formatting changes
        normalized = " ".join(content.split())
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()
    
    def get_last_hash(self, url: str) -> Optional[str]:
        """Get the last known hash for a URL."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT content_hash FROM url_hashes WHERE url = ?",
                (url,)
            )
            row = cursor.fetchone()
            return row[0] if row else None
    
    def get_last_content(self, url: str) -> Optional[str]:
        """Get the last known content for a URL."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT last_content FROM url_hashes WHERE url = ?",
                (url,)
            )
            row = cursor.fetchone()
            return row[0] if row else None
    
    def update_hash(
        self, 
        url: str, 
        content_hash: str, 
        content: str,
        analysis_result: Optional[str] = None
    ) -> bool:
        """
        Update the hash for a URL.
        Returns True if this was a new/changed hash, False if unchanged.
        """
        old_hash = self.get_last_hash(url)
        is_new = old_hash != content_hash
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Upsert current state
            cursor.execute("""
                INSERT INTO url_hashes (url, content_hash, last_content, last_updated)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(url) DO UPDATE SET
                    content_hash = excluded.content_hash,
                    last_content = excluded.last_content,
                    last_updated = CURRENT_TIMESTAMP
            """, (url, content_hash, content))
            
            # Record in history if changed
            if is_new:
                preview = content[:500] if content else ""
                cursor.execute("""
                    INSERT INTO change_history (url, content_hash, content_preview, analysis_result)
                    VALUES (?, ?, ?, ?)
                """, (url, content_hash, preview, analysis_result))
            
            conn.commit()
        
        return is_new
    
    def has_changed(self, url: str, new_content: str) -> bool:
        """
        Check if content has changed for a URL.
        This is the main method for differential analysis.
        """
        new_hash = self.compute_hash(new_content)
        old_hash = self.get_last_hash(url)
        return new_hash != old_hash
    
    def get_change_history(self, url: str, limit: int = 10) -> List[ChangeRecord]:
        """Get recent change history for a URL."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, url, content_hash, content_preview, detected_at, analysis_result
                FROM change_history
                WHERE url = ?
                ORDER BY detected_at DESC
                LIMIT ?
            """, (url, limit))
            
            records = []
            for row in cursor.fetchall():
                records.append(ChangeRecord(
                    id=row[0],
                    url=row[1],
                    content_hash=row[2],
                    content_preview=row[3],
                    detected_at=datetime.fromisoformat(row[4]) if row[4] else datetime.now(),
                    analysis_result=row[5]
                ))
            return records
    
    def get_all_monitored_urls(self) -> List[Dict[str, Any]]:
        """Get all monitored URLs with their last update times."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT url, content_hash, last_updated
                FROM url_hashes
                ORDER BY last_updated DESC
            """)
            
            return [
                {"url": row[0], "hash": row[1], "last_updated": row[2]}
                for row in cursor.fetchall()
            ]
    
    def save_analysis_result(self, url: str, analysis_result: str) -> None:
        """Save analysis result for the latest change."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE change_history
                SET analysis_result = ?
                WHERE url = ? AND id = (
                    SELECT id FROM change_history 
                    WHERE url = ? 
                    ORDER BY detected_at DESC 
                    LIMIT 1
                )
            """, (analysis_result, url, url))
            conn.commit()


# Global storage instance
storage = HashStorage()
