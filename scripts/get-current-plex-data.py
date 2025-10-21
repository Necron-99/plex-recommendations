#!/usr/bin/env python3
"""
Quick script to get current Plex data for blending
"""

import requests
import json
from datetime import datetime, timedelta

# Configuration
PLEX_SERVER = "192.168.0.109:32400"
PLEX_TOKEN = "iUAXXUBe9Hno42-aHy5E"

def get_current_plex_data():
    """Get current watch history from Plex server"""
    print("📡 Getting current Plex data from 192.168.0.109...")
    
    try:
        # Test connection
        url = f"http://{PLEX_SERVER}/status/sessions"
        headers = {"X-Plex-Token": PLEX_TOKEN}
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"❌ Plex server returned status {response.status_code}")
            return None
        
        print("✅ Connected to Plex server")
        
        # Get library sections
        url = f"http://{PLEX_SERVER}/library/sections"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print("❌ Could not get library sections")
            return None
        
        import xml.etree.ElementTree as ET
        root = ET.fromstring(response.content)
        
        all_movies = []
        
        for section in root.findall("Directory"):
            section_id = section.get("key")
            section_title = section.get("title")
            section_type = section.get("type")
            
            if section_type == "movie":
                print(f"📂 Processing movie section: {section_title}")
                
                # Get all movies from this section
                url = f"http://{PLEX_SERVER}/library/sections/{section_id}/all"
                params = {"X-Plex-Container-Start": "0", "X-Plex-Container-Size": "1000"}
                
                response = requests.get(url, headers=headers, params=params, timeout=30)
                
                if response.status_code == 200:
                    section_root = ET.fromstring(response.content)
                    
                    for video in section_root.findall("Video"):
                        view_count = int(video.get("viewCount", "0"))
                        
                        if view_count > 0:  # Only movies that have been watched
                            movie = {
                                "title": video.get("title", ""),
                                "year": video.get("year", ""),
                                "rating": video.get("rating", "0"),
                                "duration": video.get("duration", "0"),
                                "summary": video.get("summary", ""),
                                "studio": video.get("studio", ""),
                                "contentRating": video.get("contentRating", ""),
                                "viewCount": str(view_count),
                                "lastViewedAt": video.get("lastViewedAt", ""),
                                "type": "movie",
                                "source": "current_plex_server",
                                "server": "192.168.0.109"
                            }
                            
                            # Convert timestamp
                            if movie["lastViewedAt"]:
                                try:
                                    timestamp = int(movie["lastViewedAt"])
                                    movie["viewedAt"] = datetime.fromtimestamp(timestamp).isoformat()
                                except:
                                    movie["viewedAt"] = movie["lastViewedAt"]
                            
                            all_movies.append(movie)
        
        print(f"✅ Found {len(all_movies)} watched movies from current server")
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"current-plex-data-{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(all_movies, f, indent=2)
        
        print(f"💾 Current Plex data saved to: {filename}")
        return filename
        
    except Exception as e:
        print(f"❌ Error getting current Plex data: {e}")
        return None

if __name__ == "__main__":
    get_current_plex_data()
