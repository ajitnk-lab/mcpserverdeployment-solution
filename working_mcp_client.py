#!/usr/bin/env python3
"""
Working MCP client with direct token authentication
Handles Server-Sent Events (SSE) responses from StreamableHTTP MCP servers
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

class SimpleMCPClient:
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
            if response.text.startswith('event:'):
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

def test_mcp_server():
    """Test the MCP weather server"""
    
    # Parse command line arguments
    state = "WA"  # default
    if len(sys.argv) > 1:
        state = sys.argv[1].upper()
    
    # Configuration from environment variables
    server_url = os.getenv('MCP_SERVER_URL', 'https://your-endpoint/mcp')
    
    # Username/Password
    user_pool_id = os.getenv('COGNITO_USER_POOL_ID')
    client_id = os.getenv('OAUTH_CLIENT_ID')
    client_secret = os.getenv('OAUTH_CLIENT_SECRET')
    username = os.getenv('COGNITO_USERNAME')
    password = os.getenv('COGNITO_PASSWORD')
    
    print(f"🚀 Working MCP Client (Direct Auth + SSE)")
    print(f"Server URL: {server_url}")
    print(f"State: {state}")
    
    access_token = None
    if user_pool_id and client_id and client_secret and username and password:
        print("🔑 Using username/password authentication...")
        access_token = authenticate_user(user_pool_id, client_id, client_secret, username, password)
    
    if not access_token:
        print("❌ Failed to get access token. Check your configuration.")
        return
    
    print("✅ Got access token")
    
    # Create MCP client
    client = SimpleMCPClient(server_url, access_token)
    
    # Test MCP calls
    print("\n📋 Testing MCP server...")
    
    # 1. Initialize
    print("1. Initializing...")
    result = client.call_mcp("initialize", {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "simple-mcp-client", "version": "1.0.0"}
    })
    print(f"   ✅ Initialization successful!")
    print(f"   Server: {result['result']['serverInfo']['name']} v{result['result']['serverInfo']['version']}")
    
    if 'error' in result:
        print("❌ Initialization failed, stopping tests")
        return
    
    # 2. List tools
    print("\n2. Listing tools...")
    result = client.call_mcp("tools/list")
    
    if 'result' in result and 'tools' in result['result']:
        tools = result['result']['tools']
        print(f"   ✅ Found {len(tools)} tools:")
        for tool in tools:
            print(f"      - {tool['name']}: {tool.get('description', 'No description')}")
        
        # 3. Call weather tools with correct parameters
        print(f"\n3. Testing weather tools...")
        
        # Test get_alerts (requires state parameter)
        print(f"   Testing get_alerts for {state} state...")
        result = client.call_mcp("tools/call", {
            "name": "get_alerts",
            "arguments": {"state": state}
        })
        
        if 'result' in result:
            print(f"   ✅ Weather alerts retrieved successfully!")
            alert_text = result['result']['content'][0]['text'][:150]
            print(f"      Sample: {alert_text}...")
        else:
            print(f"   ❌ Error: {result}")
        
        # Test get_forecast (requires latitude and longitude)
        print("   Testing get_forecast for Seattle coordinates...")
        result = client.call_mcp("tools/call", {
            "name": "get_forecast", 
            "arguments": {"latitude": 47.6062, "longitude": -122.3321}
        })
        
        if 'result' in result:
            print(f"   ✅ Weather forecast retrieved successfully!")
            forecast_text = result['result']['content'][0]['text'][:150]
            print(f"      Sample: {forecast_text}...")
        else:
            print(f"   ❌ Error: {result}")
    else:
        print(f"   ❌ Error listing tools: {result}")
    
    print("\n🎉 MCP client test completed successfully!")

if __name__ == "__main__":
    test_mcp_server()
