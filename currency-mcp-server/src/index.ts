import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  InitializeRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import express from 'express';
import { authenticateToken } from './oauth-cognito.js';

const app = express();
const PORT = process.env.PORT || 8080;
const BASE_PATH = process.env.BASE_PATH || '';

app.use(express.json());

// Create a single MCP server instance
const server = new Server(
  {
    name: 'currency-converter',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Initialize handler
server.setRequestHandler(InitializeRequestSchema, async (request) => {
  return {
    protocolVersion: '2024-11-05',
    capabilities: {
      tools: {},
    },
    serverInfo: {
      name: 'currency-converter',
      version: '1.0.0',
    },
  };
});

// List tools handler
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: 'convert_usd_to_inr',
        description: 'Convert USD amount to INR using current exchange rate',
        inputSchema: {
          type: 'object',
          properties: {
            amount: {
              type: 'number',
              description: 'USD amount to convert',
            },
          },
          required: ['amount'],
        },
      },
      {
        name: 'get_current_rate',
        description: 'Get current USD to INR exchange rate',
        inputSchema: {
          type: 'object',
          properties: {},
        },
      },
    ],
  };
});

// Call tool handler
server.setRequestHandler(CallToolRequestSchema, async (request: any) => {
  const { name, arguments: args } = request.params;

  if (name === 'convert_usd_to_inr') {
    const amount = args?.amount || 100;
    try {
      const response = await fetch('https://api.exchangerate-api.com/v4/latest/USD');
      const data = await response.json();
      const rate = data.rates.INR;
      const converted = amount * rate;
      
      return {
        content: [
          {
            type: 'text',
            text: `$${amount} USD = ₹${converted.toFixed(2)} INR (Rate: ${rate})`,
          },
        ],
      };
    } catch (error) {
      return {
        content: [
          {
            type: 'text',
            text: `Error fetching exchange rate: ${error instanceof Error ? error.message : String(error)}`,
          },
        ],
        isError: true,
      };
    }
  }

  if (name === 'get_current_rate') {
    try {
      const response = await fetch('https://api.exchangerate-api.com/v4/latest/USD');
      const data = await response.json();
      const rate = data.rates.INR;
      
      return {
        content: [
          {
            type: 'text',
            text: `Current USD to INR rate: ${rate}`,
          },
        ],
      };
    } catch (error) {
      return {
        content: [
          {
            type: 'text',
            text: `Error fetching exchange rate: ${error instanceof Error ? error.message : String(error)}`,
          },
        ],
        isError: true,
      };
    }
  }

  throw new Error(`Unknown tool: ${name}`);
});

// Health check endpoint
app.get(`${BASE_PATH}/`, (req, res) => {
  res.json({ status: 'healthy', service: 'currency-mcp-server' });
});

// MCP endpoint - handle JSON-RPC requests properly
app.post(`${BASE_PATH}/mcp`, authenticateToken, async (req, res) => {
  try {
    // Set SSE headers for streaming response
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');
    res.setHeader('Access-Control-Allow-Origin', '*');

    const { method, params, id } = req.body;

    let result;
    
    // Handle different MCP methods
    if (method === 'initialize') {
      result = {
        protocolVersion: '2024-11-05',
        capabilities: {
          tools: {},
        },
        serverInfo: {
          name: 'currency-converter',
          version: '1.0.0',
        },
      };
    } else if (method === 'tools/list') {
      result = {
        tools: [
          {
            name: 'convert_usd_to_inr',
            description: 'Convert USD amount to INR using current exchange rate',
            inputSchema: {
              type: 'object',
              properties: {
                amount: {
                  type: 'number',
                  description: 'USD amount to convert',
                },
              },
              required: ['amount'],
            },
          },
          {
            name: 'get_current_rate',
            description: 'Get current USD to INR exchange rate',
            inputSchema: {
              type: 'object',
              properties: {},
            },
          },
        ],
      };
    } else if (method === 'tools/call') {
      const { name, arguments: args } = params;

      if (name === 'convert_usd_to_inr') {
        const amount = args?.amount || 100;
        try {
          const response = await fetch('https://api.exchangerate-api.com/v4/latest/USD');
          const data = await response.json();
          const rate = data.rates.INR;
          const converted = amount * rate;
          
          result = {
            content: [
              {
                type: 'text',
                text: `$${amount} USD = ₹${converted.toFixed(2)} INR (Rate: ${rate})`,
              },
            ],
          };
        } catch (error) {
          result = {
            content: [
              {
                type: 'text',
                text: `Error fetching exchange rate: ${error instanceof Error ? error.message : String(error)}`,
              },
            ],
            isError: true,
          };
        }
      } else if (name === 'get_current_rate') {
        try {
          const response = await fetch('https://api.exchangerate-api.com/v4/latest/USD');
          const data = await response.json();
          const rate = data.rates.INR;
          
          result = {
            content: [
              {
                type: 'text',
                text: `Current USD to INR rate: ${rate}`,
              },
            ],
          };
        } catch (error) {
          result = {
            content: [
              {
                type: 'text',
                text: `Error fetching exchange rate: ${error instanceof Error ? error.message : String(error)}`,
              },
            ],
            isError: true,
          };
        }
      } else {
        throw new Error(`Unknown tool: ${name}`);
      }
    } else {
      throw new Error(`Unknown method: ${method}`);
    }

    // Send response in SSE format
    const response = {
      jsonrpc: '2.0',
      id: id,
      result: result,
    };

    res.write(`data: ${JSON.stringify(response)}\n\n`);
    res.end();

  } catch (error) {
    const errorResponse = {
      jsonrpc: '2.0',
      id: req.body.id || null,
      error: {
        code: -32601,
        message: error instanceof Error ? error.message : String(error),
      },
    };

    res.write(`data: ${JSON.stringify(errorResponse)}\n\n`);
    res.end();
  }
});

app.listen(PORT, () => {
  console.log(`Currency MCP server running on port ${PORT}`);
});
