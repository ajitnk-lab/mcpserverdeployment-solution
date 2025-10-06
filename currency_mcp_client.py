#!/usr/bin/env python3
"""
Currency MCP Client - Test USD to INR converter
"""
import requests
import json
import os
import boto3
import hmac
import hashlib
import base64
import sys
from botocore.exceptions import ClientError

class CurrencyMCPClient:
    def __init__(self, server_url, access_token):
        self.server_url = server_url
        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/event-stream'
        }
    
    def parse_sse_response(self, text):
        """Parse Server-Sent Events response"""
        lines = text.strip().split('\n')
        data = None
        
        for line in lines:
            if line.startswith('data: '):
                data = line[6:]  # Remove 'data: ' prefix
                break
        
        if data:
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                return {"error": f"Invalid JSON in SSE data: {data}"}
        
        return {"error": "No data found in SSE response"}
    
    def call_mcp(self, method, params=None):
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or {}
        }
        
        try:
            response = requests.post(self.server_url, 
                headers=self.headers, 
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            # Check if response is SSE format
            if response.text.startswith('data:') or response.text.startswith('event:'):
                return self.parse_sse_response(response.text)
            else:
                return response.json()
                
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

def calculate_secret_hash(username, client_id, client_secret):
    """Calculate SECRET_HASH for Cognito"""
    message = username + client_id
    dig = hmac.new(
        client_secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).digest()
    return base64.b64encode(dig).decode()

def authenticate_user(user_pool_id, client_id, client_secret, username, password):
    """Authenticate user with username/password"""
    try:
        client = boto3.client('cognito-idp')
        
        # Calculate SECRET_HASH
        secret_hash = calculate_secret_hash(username, client_id, client_secret)
        
        response = client.admin_initiate_auth(
            UserPoolId=user_pool_id,
            ClientId=client_id,
            AuthFlow='ADMIN_NO_SRP_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password,
                'SECRET_HASH': secret_hash
            }
        )
        return response['AuthenticationResult']['AccessToken']
    except ClientError as e:
        print(f"❌ Authentication failed: {e}")
        return None

def test_currency_server():
    """Test the Currency MCP server"""
    
    # Parse command line arguments
    amount = 100.0  # default
    if len(sys.argv) > 1:
        try:
            amount = float(sys.argv[1])
        except ValueError:
            print("❌ Invalid amount. Using default $100")
            amount = 100.0
    
    # Configuration from environment variables
    server_url = os.getenv('CURRENCY_SERVER_URL', 'https://your-endpoint/currency-nodejs/mcp')
    
    # Username/Password
    user_pool_id = os.getenv('COGNITO_USER_POOL_ID')
    client_id = os.getenv('OAUTH_CLIENT_ID')
    client_secret = os.getenv('OAUTH_CLIENT_SECRET')
    username = os.getenv('COGNITO_USERNAME')
    password = os.getenv('COGNITO_PASSWORD')
    
    print(f"💱 Currency MCP Client (USD to INR)")
    print(f"Server URL: {server_url}")
    print(f"Amount: ${amount}")
    
    access_token = None
    if user_pool_id and client_id and client_secret and username and password:
        print("🔑 Using username/password authentication...")
        access_token = authenticate_user(user_pool_id, client_id, client_secret, username, password)
    
    if not access_token:
        print("❌ Failed to get access token. Check your configuration.")
        return
    
    print("✅ Got access token")
    
    # Create MCP client
    client = CurrencyMCPClient(server_url, access_token)
    
    # Test MCP calls
    print("\n📋 Testing Currency MCP server...")
    
    # 1. Initialize
    print("1. Initializing...")
    result = client.call_mcp("initialize", {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "currency-mcp-client", "version": "1.0.0"}
    })
    
    if 'result' in result:
        print(f"   ✅ Initialization successful!")
        print(f"   Server: {result['result']['serverInfo']['name']} v{result['result']['serverInfo']['version']}")
    else:
        print(f"   ❌ Initialization failed: {result}")
        return
    
    # 2. List tools
    print("\n2. Listing tools...")
    result = client.call_mcp("tools/list")
    
    if 'result' in result and 'tools' in result['result']:
        tools = result['result']['tools']
        print(f"   ✅ Found {len(tools)} tools:")
        for tool in tools:
            print(f"      - {tool['name']}: {tool.get('description', 'No description')}")
        
        # 3. Get current exchange rate
        print(f"\n3. Getting current USD to INR rate...")
        result = client.call_mcp("tools/call", {
            "name": "get_current_rate",
            "arguments": {}
        })
        
        if 'result' in result:
            print(f"   ✅ Current rate:")
            for content in result['result']['content']:
                if content['type'] == 'text':
                    print(f"      {content['text']}")
        else:
            print(f"   ❌ Error: {result}")
        
        # 4. Convert USD to INR
        print(f"\n4. Converting ${amount} USD to INR...")
        result = client.call_mcp("tools/call", {
            "name": "convert_usd_to_inr",
            "arguments": {"amount": amount}
        })
        
        if 'result' in result:
            print(f"   ✅ Conversion result:")
            for content in result['result']['content']:
                if content['type'] == 'text':
                    print(f"      {content['text']}")
        else:
            print(f"   ❌ Error: {result}")
    else:
        print(f"   ❌ Error listing tools: {result}")
    
    print("\n🎉 Currency MCP client test completed!")

if __name__ == "__main__":
    test_currency_server()
