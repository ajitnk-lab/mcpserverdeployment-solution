#!/usr/bin/env python3
"""
Minimal currency server deployment script
Adds currency server to existing MCP infrastructure
"""

import json
import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a command and return the result"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        print(f"✅ {description} completed")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return None

def main():
    print("🚀 Deploying Currency MCP Server")
    
    # Check if we have the original CDK project
    cdk_project_path = "/home/codespace/.git_repo_research/aws-solutions-library-samples_guidance-for-deploying-model-context-protocol-servers-on-aws/repository/source/cdk/ecs-and-lambda"
    
    if not os.path.exists(cdk_project_path):
        print("❌ CDK project not found. Please ensure the repository is indexed.")
        return False
    
    print(f"📁 Using CDK project at: {cdk_project_path}")
    
    # Copy currency server to the CDK project
    currency_src = "/workspaces/mcpserverdeployment-solution/currency-mcp-server"
    currency_dst = f"{cdk_project_path}/servers/currency-mcp-server"
    
    run_command(f"cp -r {currency_src} {currency_dst}", "Copying currency server")
    
    # Create the updated CDK stack file
    stack_file = f"{cdk_project_path}/lib/stacks/mcp-server-stack.ts"
    
    # Read the existing stack
    with open(stack_file, 'r') as f:
        stack_content = f.read()
    
    # Add currency server after the weather servers
    currency_server_code = '''
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
'''
    
    # Add routing rule
    routing_rule = '''
    // Add routing rule for currency server
    listener.addAction("CurrencyNodeJsRoute", {
      priority: 23,
      conditions: [elbv2.ListenerCondition.pathPatterns(["/currency-nodejs/*"])],
      action: elbv2.ListenerAction.forward([currencyNodeJsServer.targetGroup]),
    });
'''
    
    # Insert currency server after weather lambda server
    lambda_server_end = "    );"
    weather_lambda_end_pos = stack_content.find(lambda_server_end, stack_content.find("WeatherNodeJsLambdaServer"))
    if weather_lambda_end_pos != -1:
        insert_pos = weather_lambda_end_pos + len(lambda_server_end)
        stack_content = stack_content[:insert_pos] + currency_server_code + stack_content[insert_pos:]
    
    # Insert routing rule after weather lambda route
    lambda_route_end = '    });'
    weather_lambda_route_end_pos = stack_content.find(lambda_route_end, stack_content.find("WeatherNodeJsLambdaRoute"))
    if weather_lambda_route_end_pos != -1:
        insert_pos = weather_lambda_route_end_pos + len(lambda_route_end)
        stack_content = stack_content[:insert_pos] + routing_rule + stack_content[insert_pos:]
    
    # Write the updated stack
    with open(stack_file, 'w') as f:
        f.write(stack_content)
    
    print("✅ Updated CDK stack with currency server")
    
    # Change to CDK directory and deploy
    os.chdir(cdk_project_path)
    
    # Install dependencies
    run_command("npm install", "Installing CDK dependencies")
    
    # Build the project
    run_command("npm run build", "Building CDK project")
    
    # Deploy the stack
    result = run_command("cdk deploy MCP-Server --require-approval never", "Deploying currency server")
    
    if result:
        print("🎉 Currency server deployed successfully!")
        print("🔗 Currency server URL: https://d3v422fv5soy13.cloudfront.net/currency-nodejs/mcp")
        return True
    else:
        print("❌ Deployment failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
