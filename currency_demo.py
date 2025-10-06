#!/usr/bin/env python3
import requests
import json

def test_currency_conversions():
    url = "https://d3v422fv5soy13.cloudfront.net/currency-nodejs/mcp"
    
    # Sample test amounts
    test_amounts = [50, 100, 250, 500, 1000, 2500]
    
    print("💱 Currency MCP Server Demo")
    print("=" * 40)
    
    for amount in test_amounts:
        payload = {
            "jsonrpc": "2.0",
            "id": amount,
            "method": "tools/call", 
            "params": {
                "name": "convert_usd_to_inr",
                "arguments": {"amount": amount}
            }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=5)
            if response.status_code == 200:
                result = response.json()
                conversion = result['result']['content'][0]['text']
                print(f"✅ {conversion}")
            else:
                print(f"❌ Error for ${amount}: {response.status_code}")
        except Exception as e:
            print(f"❌ Failed ${amount}: {e}")
    
    print("\n🎉 Currency MCP Server Demo Complete!")

if __name__ == "__main__":
    test_currency_conversions()
