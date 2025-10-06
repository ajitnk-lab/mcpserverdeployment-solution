// Add this to the existing mcp-server-stack.ts after the weather servers

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
