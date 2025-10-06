#!/usr/bin/env python3
"""
Deploy currency server to ECS only (skip Lambda issues)
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
    print("🚀 Deploying Currency MCP Server (ECS Only)")
    
    # Use CloudFormation directly to add currency server
    template = {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Description": "Add Currency MCP Server to existing infrastructure",
        "Parameters": {
            "ClusterName": {
                "Type": "String",
                "Default": "MCP-Server-MCPCluster399F09A9-5IC7REEeuGUi"
            },
            "VpcId": {
                "Type": "String", 
                "Default": "vpc-028ca3fccc2d82f52"
            },
            "PrivateSubnet1": {
                "Type": "String",
                "Default": "subnet-042f67a847ae8c71b"
            },
            "PrivateSubnet2": {
                "Type": "String", 
                "Default": "subnet-07a7a8ed0ca043f03"
            },
            "LoadBalancerArn": {
                "Type": "String",
                "Default": "arn:aws:elasticloadbalancing:us-east-1:039920874011:loadbalancer/app/MCP-Se-Appli-8ufFzwXfhUDS/e6accb8269ee4a75"
            },
            "ListenerArn": {
                "Type": "String", 
                "Default": "arn:aws:elasticloadbalancing:us-east-1:039920874011:listener/app/MCP-Se-Appli-8ufFzwXfhUDS/e6accb8269ee4a75/c727f12a09a34cf6"
            }
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
                    "ExecutionRoleArn": {"Fn::GetAtt": ["CurrencyExecutionRole", "Arn"]},
                    "TaskRoleArn": {"Fn::GetAtt": ["CurrencyTaskRole", "Arn"]},
                    "ContainerDefinitions": [{
                        "Name": "currency-server",
                        "Image": "039920874011.dkr.ecr.us-east-1.amazonaws.com/currency-mcp:latest",
                        "PortMappings": [{"ContainerPort": 8080}],
                        "Environment": [
                            {"Name": "PORT", "Value": "8080"},
                            {"Name": "BASE_PATH", "Value": "/currency-nodejs"},
                            {"Name": "AWS_REGION", "Value": "us-east-1"},
                            {"Name": "COGNITO_USER_POOL_ID", "Value": "us-east-1_4ygzD9mcV"},
                            {"Name": "COGNITO_CLIENT_ID", "Value": "2n1lel48549hho97cvcdbra0ae"}
                        ],
                        "LogConfiguration": {
                            "LogDriver": "awslogs",
                            "Options": {
                                "awslogs-group": {"Ref": "CurrencyLogGroup"},
                                "awslogs-region": "us-east-1",
                                "awslogs-stream-prefix": "currency"
                            }
                        },
                        "HealthCheck": {
                            "Command": ["CMD-SHELL", "curl -f http://localhost:8080/currency-nodejs/ || exit 1"],
                            "Interval": 30,
                            "Timeout": 5,
                            "Retries": 3
                        }
                    }]
                }
            },
            "CurrencyLogGroup": {
                "Type": "AWS::Logs::LogGroup",
                "Properties": {
                    "LogGroupName": "/ecs/currency-mcp-server",
                    "RetentionInDays": 7
                }
            },
            "CurrencyExecutionRole": {
                "Type": "AWS::IAM::Role",
                "Properties": {
                    "AssumeRolePolicyDocument": {
                        "Version": "2012-10-17",
                        "Statement": [{
                            "Effect": "Allow",
                            "Principal": {"Service": "ecs-tasks.amazonaws.com"},
                            "Action": "sts:AssumeRole"
                        }]
                    },
                    "ManagedPolicyArns": [
                        "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
                    ]
                }
            },
            "CurrencyTaskRole": {
                "Type": "AWS::IAM::Role", 
                "Properties": {
                    "AssumeRolePolicyDocument": {
                        "Version": "2012-10-17",
                        "Statement": [{
                            "Effect": "Allow",
                            "Principal": {"Service": "ecs-tasks.amazonaws.com"},
                            "Action": "sts:AssumeRole"
                        }]
                    }
                }
            },
            "CurrencySecurityGroup": {
                "Type": "AWS::EC2::SecurityGroup",
                "Properties": {
                    "GroupDescription": "Security group for currency MCP server",
                    "VpcId": {"Ref": "VpcId"},
                    "SecurityGroupIngress": [{
                        "IpProtocol": "tcp",
                        "FromPort": 8080,
                        "ToPort": 8080,
                        "SourceSecurityGroupId": "sg-0b121219e1a505160"
                    }]
                }
            },
            "CurrencyTargetGroup": {
                "Type": "AWS::ElasticLoadBalancingV2::TargetGroup",
                "Properties": {
                    "Name": "currency-mcp-targets",
                    "Port": 8080,
                    "Protocol": "HTTP",
                    "VpcId": {"Ref": "VpcId"},
                    "TargetType": "ip",
                    "HealthCheckPath": "/currency-nodejs/",
                    "HealthCheckProtocol": "HTTP",
                    "HealthCheckIntervalSeconds": 30,
                    "HealthyThresholdCount": 2,
                    "UnhealthyThresholdCount": 5
                }
            },
            "CurrencyService": {
                "Type": "AWS::ECS::Service",
                "Properties": {
                    "ServiceName": "currency-mcp-service",
                    "Cluster": {"Ref": "ClusterName"},
                    "TaskDefinition": {"Ref": "CurrencyTaskDefinition"},
                    "DesiredCount": 1,
                    "LaunchType": "FARGATE",
                    "NetworkConfiguration": {
                        "AwsvpcConfiguration": {
                            "Subnets": [{"Ref": "PrivateSubnet1"}, {"Ref": "PrivateSubnet2"}],
                            "SecurityGroups": [{"Ref": "CurrencySecurityGroup"}]
                        }
                    },
                    "LoadBalancers": [{
                        "TargetGroupArn": {"Ref": "CurrencyTargetGroup"},
                        "ContainerName": "currency-server",
                        "ContainerPort": 8080
                    }]
                }
            },
            "CurrencyListenerRule": {
                "Type": "AWS::ElasticLoadBalancingV2::ListenerRule",
                "Properties": {
                    "ListenerArn": {"Ref": "ListenerArn"},
                    "Priority": 23,
                    "Conditions": [{
                        "Field": "path-pattern",
                        "Values": ["/currency-nodejs/*"]
                    }],
                    "Actions": [{
                        "Type": "forward",
                        "TargetGroupArn": {"Ref": "CurrencyTargetGroup"}
                    }]
                }
            }
        },
        "Outputs": {
            "CurrencyServiceArn": {
                "Value": {"Ref": "CurrencyService"},
                "Description": "Currency MCP Service ARN"
            },
            "CurrencyEndpoint": {
                "Value": "https://d3v422fv5soy13.cloudfront.net/currency-nodejs/mcp",
                "Description": "Currency MCP Server Endpoint"
            }
        }
    }
    
    # Write template to file
    with open('/tmp/currency-server.json', 'w') as f:
        json.dump(template, f, indent=2)
    
    print("📝 Created CloudFormation template")
    
    # First, build and push the Docker image
    print("🐳 Building and pushing Docker image...")
    
    # Create ECR repository
    run_command("aws ecr create-repository --repository-name currency-mcp --region us-east-1 || true", "Creating ECR repository")
    
    # Get ECR login
    login_cmd = subprocess.run("aws ecr get-login-password --region us-east-1", shell=True, capture_output=True, text=True)
    if login_cmd.returncode == 0:
        subprocess.run(f"echo {login_cmd.stdout.strip()} | docker login --username AWS --password-stdin 039920874011.dkr.ecr.us-east-1.amazonaws.com", shell=True)
    
    # Build and push image
    os.chdir("/workspaces/mcpserverdeployment-solution/currency-mcp-server")
    run_command("docker build -t currency-mcp .", "Building Docker image")
    run_command("docker tag currency-mcp:latest 039920874011.dkr.ecr.us-east-1.amazonaws.com/currency-mcp:latest", "Tagging image")
    run_command("docker push 039920874011.dkr.ecr.us-east-1.amazonaws.com/currency-mcp:latest", "Pushing image to ECR")
    
    # Deploy CloudFormation stack
    result = run_command("aws cloudformation deploy --template-file /tmp/currency-server.json --stack-name Currency-MCP-Server --capabilities CAPABILITY_IAM --region us-east-1", "Deploying currency server stack")
    
    if result is not None:
        print("🎉 Currency server deployed successfully!")
        print("🔗 Currency server URL: https://d3v422fv5soy13.cloudfront.net/currency-nodejs/mcp")
        return True
    else:
        print("❌ Deployment failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
