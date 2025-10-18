#!/usr/bin/env python3
"""
Repair and extract watch history from Plex database files
Handles WAL files and database corruption
"""

import sqlite3
import json
import sys
import os
import shutil
from datetime import datetime
from typing import List, Dict, Any

def repair_database(db_path: str) -> str:
    """Repair a potentially corrupted database"""
    print(f"🔧 Repairing database: {db_path}")
    
    # Create a backup
    backup_path = f"{db_path}.backup"
    shutil.copy2(db_path, backup_path)
    print(f"📁 Created backup: {backup_path}")
    
    # Try to repair using SQLite's integrity check and VACUUM
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check integrity
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        if result[0] != "ok":
            print(f"⚠️ Database integrity issues found: {result[0]}")
        
        # Try to recover
        cursor.execute("PRAGMA recover")
        print("🔄 Attempted database recovery")
        
        conn.close()
        return db_path
        
    except Exception as e:
        print(f"❌ Repair failed: {e}")
        return None

def extract_watch_history_robust(db_path: str) -> List[Dict[str, Any]]:
    """Extract watch history with robust error handling"""
    print(f"📊 Extracting from: {db_path}")
    
    # Try multiple connection methods
    connection_methods = [
        ("Direct connection", lambda: sqlite3.connect(db_path)),
        ("Read-only connection", lambda: sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)),
        ("With WAL mode", lambda: sqlite3.connect(db_path, isolation_level=None))
    ]
    
    for method_name, connect_func in connection_methods:
        try:
            print(f"🔄 Trying {method_name}...")
            conn = connect_func()
            cursor = conn.cursor()
            
            # Test basic connectivity
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
            tables = cursor.fetchall()
            if not tables:
                conn.close()
                continue
                
            print(f"✅ {method_name} successful!")
            
            # Get watch history with multiple query strategies
            queries = [
                # Primary query - comprehensive
                """
                SELECT 
                    m.title,
                    m.year,
                    m.summary,
                    m.duration,
                    m.rating,
                    m.studio,
                    m.content_rating,
                    m.originally_available_at,
                    m.added_at,
                    m.updated_at,
                    m.view_count,
                    m.last_viewed_at,
                    m.view_offset,
                    m.viewed_at,
                    m.guid,
                    m.media_type,
                    m.library_section_id
                FROM metadata_items m
                WHERE m.view_count > 0 
                AND m.media_type IN (1, 2)
                ORDER BY m.last_viewed_at DESC
                """,
                
                # Fallback query - simpler
                """
                SELECT 
                    title,
                    year,
                    summary,
                    duration,
                    rating,
                    studio,
                    content_rating,
                    originally_available_at,
                    added_at,
                    updated_at,
                    view_count,
                    last_viewed_at,
                    view_offset,
                    viewed_at,
                    guid,
                    media_type,
                    library_section_id
                FROM metadata_items
                WHERE view_count > 0
                ORDER BY last_viewed_at DESC
                """,
                
                # Minimal query - just the basics
                """
                SELECT 
                    title,
                    year,
                    view_count,
                    last_viewed_at,
                    media_type,
                    guid
                FROM metadata_items
                WHERE view_count > 0
                ORDER BY last_viewed_at DESC
                """
            ]
            
            for i, query in enumerate(queries):
                try:
                    print(f"🔄 Trying query {i+1}/3...")
                    cursor.execute(query)
                    results = cursor.fetchall()
                    
                    if results:
                        print(f"✅ Query {i+1} successful! Found {len(results)} items")
                        watch_history = process_results(results, i)
                        conn.close()
                        return watch_history
                        
                except Exception as e:
                    print(f"⚠️ Query {i+1} failed: {e}")
                    continue
            
            conn.close()
            
        except Exception as e:
            print(f"❌ {method_name} failed: {e}")
            continue
    
    print("❌ All connection methods failed")
    return []

def process_results(results: List, query_type: int) -> List[Dict[str, Any]]:
    """Process query results based on query type"""
    watch_history = []
    processed_items = set()
    
    for row in results:
        if query_type == 0:  # Comprehensive query
            item_id = row[14]  # guid
            if item_id in processed_items:
                continue
            processed_items.add(item_id)
            
            last_viewed = None
            if row[11]:  # last_viewed_at
                try:
                    last_viewed = datetime.fromtimestamp(row[11]).isoformat()
                except:
                    pass
            
            added_at = None
            if row[8]:  # added_at
                try:
                    added_at = datetime.fromtimestamp(row[8]).isoformat()
                except:
                    pass
            
            item_data = {
                "title": row[0] or "",
                "year": row[1] or None,
                "summary": row[2] or "",
                "duration": row[3] or None,
                "rating": row[4] or None,
                "studio": row[5] or "",
                "content_rating": row[6] or "",
                "originally_available_at": row[7] or "",
                "added_at": added_at,
                "view_count": row[10] or 0,
                "last_viewed_at": last_viewed,
                "view_offset": row[12] or 0,
                "viewed_at": row[13] or None,
                "guid": row[14] or "",
                "media_type": "movie" if row[15] == 1 else "episode",
                "library_section_id": row[16] or None
            }
            
        elif query_type == 1:  # Simpler query
            item_id = row[14]  # guid
            if item_id in processed_items:
                continue
            processed_items.add(item_id)
            
            last_viewed = None
            if row[11]:
                try:
                    last_viewed = datetime.fromtimestamp(row[11]).isoformat()
                except:
                    pass
            
            item_data = {
                "title": row[0] or "",
                "year": row[1] or None,
                "summary": row[2] or "",
                "duration": row[3] or None,
                "rating": row[4] or None,
                "studio": row[5] or "",
                "content_rating": row[6] or "",
                "originally_available_at": row[7] or "",
                "added_at": None,
                "view_count": row[10] or 0,
                "last_viewed_at": last_viewed,
                "view_offset": row[12] or 0,
                "viewed_at": row[13] or None,
                "guid": row[14] or "",
                "media_type": "movie" if row[15] == 1 else "episode",
                "library_section_id": row[16] or None
            }
            
        else:  # Minimal query
            item_id = row[5]  # guid
            if item_id in processed_items:
                continue
            processed_items.add(item_id)
            
            last_viewed = None
            if row[3]:
                try:
                    last_viewed = datetime.fromtimestamp(row[3]).isoformat()
                except:
                    pass
            
            item_data = {
                "title": row[0] or "",
                "year": row[1] or None,
                "summary": "",
                "duration": None,
                "rating": None,
                "studio": "",
                "content_rating": "",
                "originally_available_at": "",
                "added_at": None,
                "view_count": row[2] or 0,
                "last_viewed_at": last_viewed,
                "view_offset": 0,
                "viewed_at": None,
                "guid": row[5] or "",
                "media_type": "movie" if row[4] == 1 else "episode",
                "library_section_id": None
            }
        
        watch_history.append(item_data)
    
    return watch_history

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 repair-and-extract-plex-db.py <path-to-plex-database.db>")
        print("Example: python3 repair-and-extract-plex-db.py com.plexapp.plugins.library.db")
        sys.exit(1)
    
    db_path = sys.argv[1]
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        sys.exit(1)
    
    print("🎬 Plex Database Repair & History Extractor")
    print("=" * 50)
    
    # Try to repair the database first
    repaired_path = repair_database(db_path)
    if not repaired_path:
        print("❌ Database repair failed")
        sys.exit(1)
    
    # Extract watch history
    watch_history = extract_watch_history_robust(repaired_path)
    
    if not watch_history:
        print("❌ No watch history found in database")
        sys.exit(1)
    
    # Analyze the data
    movies = [item for item in watch_history if item["media_type"] == "movie"]
    episodes = [item for item in watch_history if item["media_type"] == "episode"]
    
    print(f"\n📊 Analysis Results:")
    print(f"   Total items: {len(watch_history)}")
    print(f"   Movies: {len(movies)}")
    print(f"   TV Episodes: {len(episodes)}")
    
    # Show some examples
    print(f"\n🎬 Recent Movies:")
    for movie in movies[:10]:
        print(f"   - {movie['title']} ({movie['year']}) - Viewed {movie['view_count']} times")
    
    print(f"\n📺 Recent TV Episodes:")
    for episode in episodes[:10]:
        print(f"   - {episode['title']} - Viewed {episode['view_count']} times")
    
    # Save to JSON file
    output_file = f"recovered-plex-history-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(watch_history, f, indent=2, default=str)
    
    print(f"\n💾 Watch history saved to: {output_file}")
    print(f"📁 File size: {len(json.dumps(watch_history, default=str))} bytes")
    
    return watch_history

if __name__ == "__main__":
    main()
