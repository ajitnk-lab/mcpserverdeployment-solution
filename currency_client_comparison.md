# Currency Client Files Comparison

## 📁 **Available Currency Clients**

### 1. **`test_currency_client.py`** - Simple JSON-RPC Client
- **Protocol**: Pure JSON-RPC 2.0
- **Authentication**: None (will fail on deployed server)
- **Response Format**: Expects JSON response
- **Use Case**: Basic testing, local development
- **Size**: ~50 lines

```bash
python test_currency_client.py
```

### 2. **`currency_mcp_client.py`** - Full MCP Client  
- **Protocol**: MCP over HTTP with SSE
- **Authentication**: AWS Cognito (username/password)
- **Response Format**: Handles SSE (`data: {...}`) format
- **Use Case**: Production client for deployed servers
- **Size**: ~200 lines

```bash
python currency_mcp_client.py 50
```

## 🔄 **Key Differences**

| Feature | test_currency_client.py | currency_mcp_client.py |
|---------|------------------------|------------------------|
| **Auth** | ❌ None | ✅ Cognito JWT |
| **SSE** | ❌ JSON only | ✅ Parses SSE |
| **MCP Protocol** | ❌ Basic JSON-RPC | ✅ Full MCP |
| **Error Handling** | ❌ Basic | ✅ Comprehensive |
| **Works with Deployed Server** | ❌ No (needs auth) | ✅ Yes |

## 💡 **Usage**

- **Development/Testing**: Use `test_currency_client.py` for local servers without auth
- **Production**: Use `currency_mcp_client.py` for deployed AWS servers with authentication
