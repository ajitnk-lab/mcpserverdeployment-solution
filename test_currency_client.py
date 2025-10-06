#!/usr/bin/env python3
import requests
import json
import sys

def test_currency_server():
    # Test the currency server directly
    url = "https://d3v422fv5soy13.cloudfront.net/currency-nodejs/mcp"
    
    # Test tools/list
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {}
    }
    
    print("🔄 Testing currency server...")
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Currency server is responding!")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Server returned {response.status_code}: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection failed: {e}")
        
    # Test conversion
    payload = {
        "jsonrpc": "2.0", 
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "convert_usd_to_inr",
            "arguments": {"amount": 100}
        }
    }
    
    print("\n🔄 Testing currency conversion...")
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("✅ Currency conversion working!")
            print(f"Result: {response.json()}")
        else:
            print(f"❌ Conversion failed: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Conversion request failed: {e}")

if __name__ == "__main__":
    test_currency_server()
