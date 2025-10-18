#!/usr/bin/env python3
"""
Extract watch history from recovered Plex database files
"""

import sqlite3
import json
import sys
from datetime import datetime
from typing import List, Dict, Any

def extract_watch_history(db_path: str) -> List[Dict[str, Any]]:
    """Extract watch history from Plex database"""
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"📊 Connected to Plex database: {db_path}")
        
        # Query to get watch history with metadata
        query = """
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
            m.library_section_id,
            g.name as genre,
            d.name as director,
            a.name as actor
        FROM metadata_items m
        LEFT JOIN taggings tg ON m.id = tg.metadata_item_id
        LEFT JOIN tags g ON tg.tag_id = g.id AND g.tag_type = 1  -- genres
        LEFT JOIN taggings td ON m.id = td.metadata_item_id  
        LEFT JOIN tags d ON td.tag_id = d.id AND d.tag_type = 4  -- directors
        LEFT JOIN taggings ta ON m.id = ta.metadata_item_id
        LEFT JOIN tags a ON ta.tag_id = a.id AND a.tag_type = 6  -- actors
        WHERE m.view_count > 0 
        AND m.media_type IN (1, 2)  -- 1=movie, 2=episode
        ORDER BY m.last_viewed_at DESC
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        print(f"✅ Found {len(results)} items with watch history")
        
        # Process results
        watch_history = []
        processed_items = set()  # To avoid duplicates
        
        for row in results:
            item_id = row[14]  # guid
            if item_id in processed_items:
                continue
            processed_items.add(item_id)
            
            # Convert timestamps
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
                "library_section_id": row[16] or None,
                "genre": row[17] or "",
                "director": row[18] or "",
                "actor": row[19] or ""
            }
            
            watch_history.append(item_data)
        
        conn.close()
        return watch_history
        
    except Exception as e:
        print(f"❌ Error extracting watch history: {e}")
        return []

def get_genres_for_item(cursor, item_id: int) -> List[str]:
    """Get all genres for a specific item"""
    try:
        cursor.execute("""
            SELECT t.name 
            FROM taggings tg
            JOIN tags t ON tg.tag_id = t.id
            WHERE tg.metadata_item_id = ? AND t.tag_type = 1
        """, (item_id,))
        return [row[0] for row in cursor.fetchall()]
    except:
        return []

def get_directors_for_item(cursor, item_id: int) -> List[str]:
    """Get all directors for a specific item"""
    try:
        cursor.execute("""
            SELECT t.name 
            FROM taggings tg
            JOIN tags t ON tg.tag_id = t.id
            WHERE tg.metadata_item_id = ? AND t.tag_type = 4
        """, (item_id,))
        return [row[0] for row in cursor.fetchall()]
    except:
        return []

def get_actors_for_item(cursor, item_id: int) -> List[str]:
    """Get all actors for a specific item"""
    try:
        cursor.execute("""
            SELECT t.name 
            FROM taggings tg
            JOIN tags t ON tg.tag_id = t.id
            WHERE tg.metadata_item_id = ? AND t.tag_type = 6
        """, (item_id,))
        return [row[0] for row in cursor.fetchall()]
    except:
        return []

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 extract-plex-db-history.py <path-to-plex-database.db>")
        print("Example: python3 extract-plex-db-history.py com.plexapp.plugins.library.db")
        sys.exit(1)
    
    db_path = sys.argv[1]
    
    print("🎬 Plex Database History Extractor")
    print("=" * 50)
    
    # Extract watch history
    watch_history = extract_watch_history(db_path)
    
    if not watch_history:
        print("❌ No watch history found in database")
        sys.exit(1)
    
    # Analyze the data
    movies = [item for item in watch_history if item["media_type"] == "movie"]
    episodes = [item for item in watch_history if item["media_type"] == "episode"]
    
    print(f"📊 Analysis Results:")
    print(f"   Total items: {len(watch_history)}")
    print(f"   Movies: {len(movies)}")
    print(f"   TV Episodes: {len(episodes)}")
    
    # Show some examples
    print(f"\n🎬 Recent Movies:")
    for movie in movies[:5]:
        print(f"   - {movie['title']} ({movie['year']}) - Viewed {movie['view_count']} times")
    
    print(f"\n📺 Recent TV Episodes:")
    for episode in episodes[:5]:
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
