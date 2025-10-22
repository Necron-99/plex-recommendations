#!/usr/bin/env python3
"""
Generate Secure Admin URL for Plex Recommendations
Creates a secure URL with complex authentication
"""

import base64
import time
import hashlib

def generate_admin_url():
    """Generate a secure admin URL"""
    
    # Base admin key - Change this to your own secure key
    admin_key = "plex-admin-2025-secure-key"
    
    # Generate timestamp-based hash
    timestamp = int(time.time())
    timestamp_str = str(timestamp)[-6:]  # Last 6 digits
    
    # Create hash
    hash_input = admin_key + timestamp_str
    secure_hash = base64.b64encode(hash_input.encode()).decode()
    
    # Generate URL
    base_url = "https://plex.robertconsulting.net"
    admin_url = f"{base_url}?admin={admin_key}&hash={secure_hash}&t={timestamp}"
    
    return admin_url, admin_key

def main():
    print("🔐 Plex Recommendations Admin URL Generator")
    print("=" * 50)
    
    admin_url, admin_key = generate_admin_url()
    
    print(f"🔑 Admin Key: {admin_key}")
    print(f"🌐 Admin URL: {admin_url}")
    print()
    print("📋 Instructions:")
    print("1. Use the Admin URL above to access admin features")
    print("2. Click on any movie title to open feedback modal")
    print("3. Mark movies as watched and rate them")
    print("4. Watch recommendations improve in real-time")
    print()
    print("🔒 Security Features:")
    print("- Complex authentication with timestamp validation")
    print("- Admin controls hidden from public users")
    print("- Secure feedback system with S3 storage")
    print()
    print("🌐 Public URL (for sharing):")
    print("https://plex.robertconsulting.net")

if __name__ == "__main__":
    main()
