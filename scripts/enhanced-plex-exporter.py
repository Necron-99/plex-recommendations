#!/usr/bin/env python3
"""
Enhanced Plex data exporter that tries multiple methods to get comprehensive watch history
"""

import requests
import json
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Configuration
PLEX_SERVER = "your-plex-server:32400"
PLEX_TOKEN = "your_plex_token_here"

def get_all_library_sections():
    """Get all library sections to check for more data"""
    try:
        url = f"http://{PLEX_SERVER}/library/sections"
        headers = {"X-Plex-Token": PLEX_TOKEN}
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            sections = []
            for section in root.findall("Directory"):
                sections.append({
                    "id": section.get("key"),
                    "title": section.get("title"),
                    "type": section.get("type")
                })
            return sections
        return []
    except Exception as e:
        print(f"⚠️ Error getting library sections: {e}")
        return []

def get_recently_added(section_id: str, limit: int = 100):
    """Get recently added items from a library section"""
    try:
        url = f"http://{PLEX_SERVER}/library/sections/{section_id}/recentlyAdded"
        headers = {"X-Plex-Token": PLEX_TOKEN}
        params = {"X-Plex-Container-Start": "0", "X-Plex-Container-Size": str(limit)}
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            items = []
            for video in root.findall("Video"):
                items.append({
                    "title": video.get("title", ""),
                    "year": video.get("year", ""),
                    "type": video.get("type", ""),
                    "addedAt": video.get("addedAt", ""),
                    "viewCount": video.get("viewCount", "0"),
                    "lastViewedAt": video.get("lastViewedAt", ""),
                    "rating": video.get("rating", ""),
                    "duration": video.get("duration", ""),
                    "summary": video.get("summary", "")
                })
            return items
        return []
    except Exception as e:
        print(f"⚠️ Error getting recently added from section {section_id}: {e}")
        return []

def get_all_items_from_section(section_id: str):
    """Get all items from a library section (this might be slow for large libraries)"""
    try:
        url = f"http://{PLEX_SERVER}/library/sections/{section_id}/all"
        headers = {"X-Plex-Token": PLEX_TOKEN}
        params = {"X-Plex-Container-Start": "0", "X-Plex-Container-Size": "1000"}
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        if response.status_code == 200:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            items = []
            for video in root.findall("Video"):
                if int(video.get("viewCount", "0")) > 0:  # Only items that have been watched
                    items.append({
                        "title": video.get("title", ""),
                        "year": video.get("year", ""),
                        "type": video.get("type", ""),
                        "addedAt": video.get("addedAt", ""),
                        "viewCount": video.get("viewCount", "0"),
                        "lastViewedAt": video.get("lastViewedAt", ""),
                        "rating": video.get("rating", ""),
                        "duration": video.get("duration", ""),
                        "summary": video.get("summary", ""),
                        "studio": video.get("studio", ""),
                        "contentRating": video.get("contentRating", "")
                    })
            return items
        return []
    except Exception as e:
        print(f"⚠️ Error getting all items from section {section_id}: {e}")
        return []

def main():
    print("🎬 Enhanced Plex Data Exporter")
    print("=" * 50)
    
    # Get library sections
    print("📚 Getting library sections...")
    sections = get_all_library_sections()
    print(f"✅ Found {len(sections)} library sections")
    
    all_watched_items = []
    
    for section in sections:
        section_id = section["id"]
        section_title = section["title"]
        section_type = section["type"]
        
        print(f"\n📂 Processing section: {section_title} ({section_type})")
        
        # Get recently added items
        print(f"   📥 Getting recently added items...")
        recent_items = get_recently_added(section_id, 200)
        watched_recent = [item for item in recent_items if int(item.get("viewCount", "0")) > 0]
        print(f"   ✅ Found {len(watched_recent)} recently watched items")
        
        # Get all items (if section is not too large)
        if section_type in ["movie", "show"] and len(recent_items) < 500:
            print(f"   📥 Getting all watched items...")
            all_items = get_all_items_from_section(section_id)
            print(f"   ✅ Found {len(all_items)} total watched items")
            
            # Combine and deduplicate
            all_section_items = watched_recent + all_items
            seen_titles = set()
            unique_items = []
            for item in all_section_items:
                title_key = f"{item['title']}_{item['year']}"
                if title_key not in seen_titles:
                    seen_titles.add(title_key)
                    unique_items.append(item)
            
            all_watched_items.extend(unique_items)
            print(f"   📊 Total unique watched items: {len(unique_items)}")
        else:
            all_watched_items.extend(watched_recent)
            print(f"   📊 Using recently watched items: {len(watched_recent)}")
    
    # Analyze results
    movies = [item for item in all_watched_items if item["type"] == "movie"]
    episodes = [item for item in all_watched_items if item["type"] == "episode"]
    
    print(f"\n📊 Final Results:")
    print(f"   Total watched items: {len(all_watched_items)}")
    print(f"   Movies: {len(movies)}")
    print(f"   TV Episodes: {len(episodes)}")
    
    # Show some examples
    print(f"\n🎬 Sample Movies:")
    for movie in movies[:10]:
        view_count = movie.get("viewCount", "0")
        last_viewed = movie.get("lastViewedAt", "")
        if last_viewed:
            try:
                last_viewed_date = datetime.fromtimestamp(int(last_viewed)).strftime("%Y-%m-%d")
            except:
                last_viewed_date = "Unknown"
        else:
            last_viewed_date = "Unknown"
        print(f"   - {movie['title']} ({movie['year']}) - Viewed {view_count} times, Last: {last_viewed_date}")
    
    # Save to file
    output_file = f"enhanced-plex-history-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(all_watched_items, f, indent=2)
    
    print(f"\n💾 Enhanced watch history saved to: {output_file}")
    print(f"📁 File size: {len(json.dumps(all_watched_items))} bytes")
    
    return all_watched_items

if __name__ == "__main__":
    main()
