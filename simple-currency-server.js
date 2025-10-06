const express = require('express');
const app = express();
const PORT = process.env.PORT || 8080;
const BASE_PATH = process.env.BASE_PATH || '';

app.use(express.json());

// Health check
app.get(`${BASE_PATH}/`, (req, res) => {
  res.json({ status: 'healthy', service: 'currency-mcp-server' });
});

// Simple MCP endpoint
app.post(`${BASE_PATH}/mcp`, async (req, res) => {
  const { method, params } = req.body;
  
  if (method === 'tools/list') {
    return res.json({
      jsonrpc: '2.0',
      id: req.body.id,
      result: {
        tools: [
          {
            name: 'convert_usd_to_inr',
            description: 'Convert USD to INR',
            inputSchema: {
              type: 'object',
              properties: { amount: { type: 'number' } },
              required: ['amount']
            }
          }
        ]
      }
    });
  }
  
  if (method === 'tools/call' && params?.name === 'convert_usd_to_inr') {
    const amount = params.arguments?.amount || 100;
    try {
      const response = await fetch('https://api.exchangerate-api.com/v4/latest/USD');
      const data = await response.json();
      const rate = data.rates.INR;
      const converted = amount * rate;
      
      return res.json({
        jsonrpc: '2.0',
        id: req.body.id,
        result: {
          content: [{
            type: 'text',
            text: `$${amount} USD = ₹${converted.toFixed(2)} INR (Rate: ${rate})`
          }]
        }
      });
    } catch (error) {
      return res.status(500).json({
        jsonrpc: '2.0',
        id: req.body.id,
        error: { code: -1, message: error.message }
      });
    }
  }
  
  res.status(400).json({
    jsonrpc: '2.0',
    id: req.body.id,
    error: { code: -32601, message: 'Method not found' }
  });
});

app.listen(PORT, () => {
  console.log(`Currency server running on port ${PORT}`);
});
