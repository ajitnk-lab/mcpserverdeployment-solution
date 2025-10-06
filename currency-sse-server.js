const express = require('express');
const app = express();
const PORT = process.env.PORT || 8080;
const BASE_PATH = process.env.BASE_PATH || '';

app.use(express.json());

// Health check
app.get(`${BASE_PATH}/`, (req, res) => {
  res.json({ status: 'healthy', service: 'currency-mcp-server' });
});

// SSE MCP endpoint
app.post(`${BASE_PATH}/mcp`, async (req, res) => {
  // Set SSE headers
  res.writeHead(200, {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Access-Control-Allow-Origin': '*'
  });

  const { method, params } = req.body;
  let response;
  
  if (method === 'tools/list') {
    response = {
      jsonrpc: '2.0',
      id: req.body.id,
      result: {
        tools: [{
          name: 'convert_usd_to_inr',
          description: 'Convert USD to INR',
          inputSchema: {
            type: 'object',
            properties: { amount: { type: 'number' } },
            required: ['amount']
          }
        }]
      }
    };
  } else if (method === 'tools/call' && params?.name === 'convert_usd_to_inr') {
    const amount = params.arguments?.amount || 100;
    try {
      const apiResponse = await fetch('https://api.exchangerate-api.com/v4/latest/USD');
      const data = await apiResponse.json();
      const rate = data.rates.INR;
      const converted = amount * rate;
      
      response = {
        jsonrpc: '2.0',
        id: req.body.id,
        result: {
          content: [{
            type: 'text',
            text: `$${amount} USD = ₹${converted.toFixed(2)} INR (Rate: ${rate})`
          }]
        }
      };
    } catch (error) {
      response = {
        jsonrpc: '2.0',
        id: req.body.id,
        error: { code: -1, message: error.message }
      };
    }
  } else {
    response = {
      jsonrpc: '2.0',
      id: req.body.id,
      error: { code: -32601, message: 'Method not found' }
    };
  }
  
  // Send as SSE
  res.write(`data: ${JSON.stringify(response)}\n\n`);
  res.end();
});

app.listen(PORT, () => {
  console.log(`Currency SSE server running on port ${PORT}`);
});
