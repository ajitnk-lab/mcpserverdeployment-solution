#!/usr/bin/env python3
import subprocess
import json

def run_cmd(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)

# Build and push currency server image
print("🐳 Building currency server...")
subprocess.run("cd currency-mcp-server && docker build -t currency-mcp .", shell=True)

# Create ECR repo and push
subprocess.run("aws ecr create-repository --repository-name currency-mcp --region us-east-1 || true", shell=True)
login = run_cmd("aws ecr get-login-password --region us-east-1")
subprocess.run(f"echo {login.stdout.strip()} | docker login --username AWS --password-stdin 039920874011.dkr.ecr.us-east-1.amazonaws.com", shell=True)
subprocess.run("docker tag currency-mcp:latest 039920874011.dkr.ecr.us-east-1.amazonaws.com/currency-mcp:latest", shell=True)
subprocess.run("docker push 039920874011.dkr.ecr.us-east-1.amazonaws.com/currency-mcp:latest", shell=True)

# Minimal CloudFormation template
template = {
    "Resources": {
        "CurrencyTask": {
            "Type": "AWS::ECS::TaskDefinition",
            "Properties": {
                "Family": "currency-mcp",
                "NetworkMode": "awsvpc",
                "RequiresCompatibilities": ["FARGATE"],
                "Cpu": "256", "Memory": "512",
                "ExecutionRoleArn": "arn:aws:iam::039920874011:role/MCP-Server-WeatherNodeJsServerWeatherNodeJsTaskExec-sqdpXA4oNtqg",
                "TaskRoleArn": "arn:aws:iam::039920874011:role/MCP-Server-WeatherNodeJsServerWeatherNodeJsTaskTask-zyX8nDBFZJ2g",
                "ContainerDefinitions": [{
                    "Name": "currency",
                    "Image": "039920874011.dkr.ecr.us-east-1.amazonaws.com/currency-mcp:latest",
                    "PortMappings": [{"ContainerPort": 8080}],
                    "Environment": [
                        {"Name": "PORT", "Value": "8080"},
                        {"Name": "BASE_PATH", "Value": "/currency-nodejs"},
                        {"Name": "COGNITO_USER_POOL_ID", "Value": "us-east-1_4ygzD9mcV"},
                        {"Name": "COGNITO_CLIENT_ID", "Value": "2n1lel48549hho97cvcdbra0ae"}
                    ],
                    "LogConfiguration": {
                        "LogDriver": "awslogs",
                        "Options": {
                            "awslogs-group": "/ecs/currency-mcp",
                            "awslogs-region": "us-east-1",
                            "awslogs-stream-prefix": "currency"
                        }
                    }
                }]
            }
        },
        "CurrencyLogs": {
            "Type": "AWS::Logs::LogGroup",
            "Properties": {"LogGroupName": "/ecs/currency-mcp", "RetentionInDays": 7}
        },
        "CurrencySG": {
            "Type": "AWS::EC2::SecurityGroup",
            "Properties": {
                "GroupDescription": "Currency MCP",
                "VpcId": "vpc-028ca3fccc2d82f52",
                "SecurityGroupIngress": [{
                    "IpProtocol": "tcp", "FromPort": 8080, "ToPort": 8080,
                    "SourceSecurityGroupId": "sg-0b121219e1a505160"
                }]
            }
        },
        "CurrencyTG": {
            "Type": "AWS::ElasticLoadBalancingV2::TargetGroup",
            "Properties": {
                "Name": "currency-mcp", "Port": 8080, "Protocol": "HTTP",
                "VpcId": "vpc-028ca3fccc2d82f52", "TargetType": "ip",
                "HealthCheckPath": "/currency-nodejs/"
            }
        },
        "CurrencyService": {
            "Type": "AWS::ECS::Service",
            "Properties": {
                "Cluster": "MCP-Server-MCPCluster399F09A9-5IC7REEeuGUi",
                "TaskDefinition": {"Ref": "CurrencyTask"},
                "DesiredCount": 1, "LaunchType": "FARGATE",
                "NetworkConfiguration": {
                    "AwsvpcConfiguration": {
                        "Subnets": ["subnet-042f67a847ae8c71b", "subnet-07a7a8ed0ca043f03"],
                        "SecurityGroups": [{"Ref": "CurrencySG"}]
                    }
                },
                "LoadBalancers": [{
                    "TargetGroupArn": {"Ref": "CurrencyTG"},
                    "ContainerName": "currency", "ContainerPort": 8080
                }]
            }
        },
        "CurrencyRule": {
            "Type": "AWS::ElasticLoadBalancingV2::ListenerRule",
            "Properties": {
                "ListenerArn": "arn:aws:elasticloadbalancing:us-east-1:039920874011:listener/app/MCP-Se-Appli-8ufFzwXfhUDS/e6accb8269ee4a75/c727f12a09a34cf6",
                "Priority": 23,
                "Conditions": [{"Field": "path-pattern", "Values": ["/currency-nodejs/*"]}],
                "Actions": [{"Type": "forward", "TargetGroupArn": {"Ref": "CurrencyTG"}}]
            }
        }
    }
}

with open('/tmp/currency.json', 'w') as f:
    json.dump(template, f)

print("🚀 Deploying currency server...")
result = subprocess.run("aws cloudformation deploy --template-file /tmp/currency.json --stack-name Currency-MCP --capabilities CAPABILITY_IAM", shell=True)

if result.returncode == 0:
    print("✅ Currency server deployed!")
    print("🔗 URL: https://d3v422fv5soy13.cloudfront.net/currency-nodejs/mcp")
else:
    print("❌ Deployment failed")
