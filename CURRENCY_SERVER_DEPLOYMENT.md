# Currency MCP Server Deployment Guide

## 🎯 **Objective**
Deploy a USD to INR currency converter MCP server to ECS alongside the existing weather servers.

## 📊 **Current Architecture**
- **2 Weather MCP Servers**: ECS Fargate + Lambda
- **1 New Currency MCP Server**: ECS Fargate (to be added)

## 📁 **Files Created**

### **Currency Server Code:**
- `currency-mcp-server/src/index.ts` - Main server implementation
- `currency-mcp-server/src/oauth-cognito.ts` - Cognito authentication
- `currency-mcp-server/package.json` - Dependencies
- `currency-mcp-server/tsconfig.json` - TypeScript configuration
- `currency-mcp-server/Dockerfile` - Container configuration

### **Client Code:**
- `currency_mcp_client.py` - Test client for currency server

### **CDK Configuration:**
- `mcp-server-stack-with-currency.ts` - CDK code to add currency server

## 🚀 **Deployment Steps**

### **1. Copy Currency Server to CDK Project**
```bash
# Navigate to your CDK project
cd source/cdk/ecs-and-lambda/servers/

# Copy currency server
cp -r /path/to/currency-mcp-server ./

# Verify structure
ls -la currency-mcp-server/
```

### **2. Update CDK Stack**
Add this code to `lib/stacks/mcp-server-stack.ts` after the weather servers:

```typescript
// ****************************************************************
// Currency Converter MCP Server built on ECS Fargate
// ****************************************************************

// Deploy the Currency converter server
const currencyNodeJsServer = new McpFargateServerConstruct(
  this,
  "CurrencyNodeJsServer",
  {
    platform: {
      vpc: props.vpc,
      cluster: this.cluster,
    },
    serverName: "CurrencyNodeJs",
    serverPath: path.join(
      __dirname,
      "../../servers/currency-mcp-server"
    ),
    healthCheckPath: "/currency-nodejs/",
    environment: {
      PORT: "8080",
      BASE_PATH: "/currency-nodejs",
      AWS_REGION: this.region,
      COGNITO_USER_POOL_ID: userPoolIdParam.stringValue,
      COGNITO_CLIENT_ID: userPoolClientIdParam.stringValue,
    },
    albSecurityGroup: this.albSecurityGroup,
    urlParameterName: paramName,
  }
);

// Add routing rule for currency server
listener.addAction("CurrencyNodeJsRoute", {
  priority: 23,
  conditions: [elbv2.ListenerCondition.pathPatterns(["/currency-nodejs/*"])],
  action: elbv2.ListenerAction.forward([currencyNodeJsServer.targetGroup]),
});
```

### **3. Deploy to AWS**
```bash
# Deploy the updated stack
cdk deploy MCP-Server

# Wait for deployment to complete (~10-15 minutes)
```

### **4. Test Currency Server**
```bash
# Set environment variables
export CURRENCY_SERVER_URL="https://d3v422fv5soy13.cloudfront.net/currency-nodejs/mcp"
export COGNITO_USER_POOL_ID="us-east-1_4ygzD9mcV"
export OAUTH_CLIENT_ID="2n1lel48549hho97cvcdbra0ae"
export OAUTH_CLIENT_SECRET="1u5o9pcu17m55om48atcqlr2ko14pct0qa0eh122gaqcnoacijqj"
export COGNITO_USERNAME="mcptest"
export COGNITO_PASSWORD="TestPass123!"

# Test currency conversion
python currency_mcp_client.py 100    # Convert $100 USD to INR
python currency_mcp_client.py 50     # Convert $50 USD to INR
```

## 🔧 **Currency Server Features**

### **Tools Provided:**
1. **`convert_usd_to_inr`**
   - **Input**: `amount` (number) - USD amount to convert
   - **Output**: Converted INR amount with current exchange rate

2. **`get_current_rate`**
   - **Input**: None
   - **Output**: Current USD to INR exchange rate

### **API Integration:**
- **Exchange Rate API**: Uses `api.exchangerate-api.com` for real-time rates
- **Authentication**: Same Cognito setup as weather servers
- **Transport**: StreamableHTTP with SSE responses

## 📊 **Final Architecture**

After deployment, you'll have **3 MCP Servers**:

1. **Weather ECS**: `https://endpoint/weather-nodejs/mcp`
2. **Weather Lambda**: `https://endpoint/weather-nodejs-lambda/mcp`  
3. **Currency ECS**: `https://endpoint/currency-nodejs/mcp` *(new)*

## 🎯 **Usage Examples**

```bash
# Weather alerts
python working_mcp_client.py CA

# Currency conversion
python currency_mcp_client.py 100
```

**Your currency MCP server is ready for deployment to ECS!** 💱
