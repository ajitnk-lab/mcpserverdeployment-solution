#!/usr/bin/env python3
"""
Deploy updated currency server with proper MCP protocol support
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
    print("🚀 Deploying Updated Currency MCP Server")
    
    # Simple CloudFormation template for currency server
    template = {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Description": "Currency MCP Server with proper MCP protocol support",
        "Parameters": {
            "VpcId": {"Type": "String", "Default": "vpc-028ca3fccc2d82f52"},
            "PrivateSubnet1": {"Type": "String", "Default": "subnet-042f67a847ae8c71b"},
            "PrivateSubnet2": {"Type": "String", "Default": "subnet-07a7a8ed0ca043f03"},
            "ClusterName": {"Type": "String", "Default": "MCP-Server-MCPCluster399F09A9-5IC7REEeuGUi"},
            "LoadBalancerArn": {"Type": "String", "Default": "arn:aws:elasticloadbalancing:us-east-1:039920874011:loadbalancer/app/MCP-Se-Appli-8ufFzwXfhUDS/e6accb8269ee4a75"},
            "ListenerArn": {"Type": "String", "Default": "arn:aws:elasticloadbalancing:us-east-1:039920874011:listener/app/MCP-Se-Appli-8ufFzwXfhUDS/e6accb8269ee4a75/c727f12a09a34cf6"}
        },
        "Resources": {
            "CurrencyTaskDefinition": {
                "Type": "AWS::ECS::TaskDefinition",
                "Properties": {
                    "Family": "currency-mcp-server",
                    "NetworkMode": "awsvpc",
                    "RequiresCompatibilities": ["FARGATE"],
                    "Cpu": "256",
                    "Memory": "512",
                    "ExecutionRoleArn": "arn:aws:iam::039920874011:role/ecsTaskExecutionRole",
                    "ContainerDefinitions": [{
                        "Name": "currency-mcp-server",
                        "Image": "039920874011.dkr.ecr.us-east-1.amazonaws.com/currency-mcp-server:latest",
                        "PortMappings": [{"ContainerPort": 8080, "Protocol": "tcp"}],
                        "Environment": [
                            {"Name": "BASE_PATH", "Value": "/currency-nodejs"},
                            {"Name": "AWS_REGION", "Value": "us-east-1"},
                            {"Name": "COGNITO_USER_POOL_ID", "Value": "us-east-1_4ygzD9mcV"}
                        ],
                        "LogConfiguration": {
                            "LogDriver": "awslogs",
                            "Options": {
                                "awslogs-group": "/ecs/currency-mcp-server",
                                "awslogs-region": "us-east-1",
                                "awslogs-stream-prefix": "ecs"
                            }
                        }
                    }]
                }
            },
            "CurrencyService": {
                "Type": "AWS::ECS::Service",
                "Properties": {
                    "ServiceName": "currency-mcp-server",
                    "Cluster": {"Ref": "ClusterName"},
                    "TaskDefinition": {"Ref": "CurrencyTaskDefinition"},
                    "DesiredCount": 1,
                    "LaunchType": "FARGATE",
                    "NetworkConfiguration": {
                        "AwsvpcConfiguration": {
                            "SecurityGroups": ["sg-0b8b8b8b8b8b8b8b8"],
                            "Subnets": [{"Ref": "PrivateSubnet1"}, {"Ref": "PrivateSubnet2"}]
                        }
                    },
                    "LoadBalancers": [{
                        "ContainerName": "currency-mcp-server",
                        "ContainerPort": 8080,
                        "TargetGroupArn": {"Ref": "CurrencyTargetGroup"}
                    }]
                }
            },
            "CurrencyTargetGroup": {
                "Type": "AWS::ElasticLoadBalancingV2::TargetGroup",
                "Properties": {
                    "Name": "currency-mcp-tg",
                    "Port": 8080,
                    "Protocol": "HTTP",
                    "VpcId": {"Ref": "VpcId"},
                    "TargetType": "ip",
                    "HealthCheckPath": "/currency-nodejs/",
                    "HealthCheckProtocol": "HTTP"
                }
            },
            "CurrencyListenerRule": {
                "Type": "AWS::ElasticLoadBalancingV2::ListenerRule",
                "Properties": {
                    "ListenerArn": {"Ref": "ListenerArn"},
                    "Priority": 200,
                    "Conditions": [{"Field": "path-pattern", "Values": ["/currency-nodejs/*"]}],
                    "Actions": [{"Type": "forward", "TargetGroupArn": {"Ref": "CurrencyTargetGroup"}}]
                }
            }
        }
    }
    
    # Write template to file
    with open('currency-server-template.json', 'w') as f:
        json.dump(template, f, indent=2)
    
    print("📝 Created CloudFormation template")
    
    # Deploy the stack
    deploy_cmd = f"""aws cloudformation deploy \
        --template-file currency-server-template.json \
        --stack-name Currency-MCP-Server-Updated \
        --capabilities CAPABILITY_IAM \
        --region us-east-1"""
    
    result = run_command(deploy_cmd, "Deploying currency server stack")
    if result is None:
        print("❌ Deployment failed")
        return False
    
    print("✅ Currency MCP Server deployed successfully!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
