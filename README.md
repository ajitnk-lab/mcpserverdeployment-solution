# MCP Server Deployment Solution

## 🚀 **Browser-Free MCP Client**

This solution provides a working MCP (Model Context Protocol) client that connects to AWS-deployed MCP servers **without requiring browser OAuth authentication**.

### ✅ **Key Features**
- **No Browser Required**: Direct API authentication with AWS Cognito
- **Command Line Parameters**: Pass state codes for weather alerts
- **Real Weather Data**: Live National Weather Service integration
- **SSE Support**: Handles StreamableHTTP transport responses
- **Secure**: JWT token authentication

## 📁 **Files**

### **Required:**
- `working_mcp_client.py` - Complete MCP client (standalone)

### **Optional (can be deleted):**
- `simple-auth-client-python/` - Original browser-based OAuth client

## 🔧 **Setup**

### **Environment Variables:**
```bash
export MCP_SERVER_URL="https://d3v422fv5soy13.cloudfront.net/weather-nodejs/mcp"
export COGNITO_USER_POOL_ID="us-east-1_4ygzD9mcV"
export OAUTH_CLIENT_ID="2n1lel48549hho97cvcdbra0ae"
export OAUTH_CLIENT_SECRET="1u5o9pcu17m55om48atcqlr2ko14pct0qa0eh122gaqcnoacijqj"
export COGNITO_USERNAME="mcptest"
export COGNITO_PASSWORD="TestPass123!"
```

## 🎯 **Usage**

### **Basic Usage:**
```bash
python working_mcp_client.py
```

### **With State Parameter:**
```bash
python working_mcp_client.py CA    # California weather alerts
python working_mcp_client.py TX    # Texas weather alerts  
python working_mcp_client.py FL    # Florida weather alerts
python working_mcp_client.py NY    # New York weather alerts
```

## 🏗️ **How It Works**

### **1. Authentication Flow**
- Direct username/password authentication with AWS Cognito
- No browser OAuth callback required
- Returns JWT access token for MCP server authorization

### **2. MCP Protocol Communication**
- JSON-RPC 2.0 over HTTPS
- StreamableHTTP transport with Server-Sent Events (SSE)
- Bearer token authentication

### **3. Weather Tools**
- `get_alerts`: Weather alerts by US state code
- `get_forecast`: Weather forecast by latitude/longitude coordinates

## 🔄 **Execution Flow**

1. **Parse command line** → Get state parameter (default: WA)
2. **Load environment** → AWS/MCP configuration
3. **Authenticate with Cognito** → Get access token (no browser)
4. **Initialize MCP session** → Handshake with server
5. **List available tools** → Discover capabilities
6. **Call weather tools** → Get real weather data
7. **Parse SSE responses** → Handle StreamableHTTP format
8. **Display results** → Show weather alerts/forecast

## 🌟 **Solution Benefits**

- ✅ **Bypasses browser OAuth callback issues**
- ✅ **Works in headless environments**
- ✅ **Simple standalone Python script**
- ✅ **No complex dependencies or SDK required**
- ✅ **Direct API authentication**
- ✅ **Real-time weather data integration**

## 🧹 **Cleanup**

Remove unnecessary files:
```bash
rm -rf simple-auth-client-python/
```

The `working_mcp_client.py` file is all you need for a complete MCP client solution!
