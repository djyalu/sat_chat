#!/usr/bin/env python3
"""Simple health check for Render deployment"""

import requests
import time
import sys

def check_health(url, max_attempts=10):
    """Check if the service is healthy"""
    print(f"🔍 Checking health of {url}")
    
    for attempt in range(1, max_attempts + 1):
        print(f"\n📡 Attempt {attempt}/{max_attempts}...")
        
        try:
            response = requests.get(f"{url}/health", timeout=10)
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ Service is healthy!")
                print(f"   Response: {response.json()}")
                return True
            elif response.status_code == 502:
                print(f"   ⚠️ 502 Bad Gateway - Service not ready yet")
            else:
                print(f"   ❌ Unexpected status: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Error: {e}")
        
        if attempt < max_attempts:
            print(f"   ⏳ Waiting 30 seconds before retry...")
            time.sleep(30)
    
    print("\n❌ Service health check failed after all attempts")
    return False

if __name__ == "__main__":
    # Check local first
    print("=== Local Service Check ===")
    if check_health("http://localhost:8002", max_attempts=1):
        print("✅ Local service is running")
    else:
        print("⚠️ Local service not running")
    
    # Check Render deployment
    print("\n=== Render Deployment Check ===")
    render_url = "https://sat-chat.onrender.com"
    
    if check_health(render_url, max_attempts=3):
        print(f"\n🎉 Render deployment is working!")
        print(f"📊 Dashboard: {render_url}/multi_analysis.html")
    else:
        print(f"\n❌ Render deployment issues detected")
        print("\n📋 Troubleshooting steps:")
        print("1. Check Render dashboard: https://dashboard.render.com")
        print("2. Verify environment variables are set")
        print("3. Check build logs for errors")
        print("4. Ensure GitHub webhook is configured")
        print("5. Try manual deploy: https://render.com/deploy?repo=https://github.com/djyalu/sat_chat")