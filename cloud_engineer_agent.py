from strands import Agent
from strands.tools.mcp import MCPClient
from strands.models import BedrockModel
from mcp import StdioServerParameters, stdio_client
from strands_tools import editor, file_read, file_write, shell, python_repl, http_request, image_reader, generate_image, speak, calculator, current_time, load_tool, swarm
from tools.use_aws_sts import use_aws_sts
import threading
import logging
import os
import atexit
from typing import Dict, Optional, Any, List
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, ConnectTimeoutError, ReadTimeoutError

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define common cloud engineering tasks
PREDEFINED_TASKS = {
    "ec2_status": "List all EC2 instances and their status",
    "s3_buckets": "List all S3 buckets and their creation dates",
    "cloudwatch_alarms": "Check for any CloudWatch alarms in ALARM state",
    "iam_users": "List all IAM users and their last activity",
    "security_groups": "Analyze security groups for potential vulnerabilities",
    "cost_optimization": "Identify resources that could be optimized for cost",
    "lambda_functions": "List all Lambda functions and their runtime",
    "rds_instances": "Check status of all RDS instances",
    "vpc_analysis": "Analyze VPC configuration and suggest improvements",
    "ebs_volumes": "Find unattached EBS volumes that could be removed",
    "generate_diagram": "Generate AWS architecture diagrams based on user description"
}

# Common environment variables for all MCP clients
def get_aws_env_vars() -> Dict[str, str]:
    """Get AWS environment variables with validation and logging."""
    required_vars = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"]
    env_vars = {
        "AWS_ACCESS_KEY_ID": os.environ.get("AWS_ACCESS_KEY_ID"),
        "AWS_SECRET_ACCESS_KEY": os.environ.get("AWS_SECRET_ACCESS_KEY"),
        "AWS_REGION": os.environ.get("AWS_REGION", "us-east-1"),
    }
    
    # Log AWS configuration status
    logger.info("AWS Configuration:")
    for var in required_vars:
        if env_vars.get(var):
            logger.info(f"  {var}: {'*' * 8} (set)")
        else:
            logger.warning(f"  {var}: NOT SET")
    
    logger.info(f"  AWS_REGION: {env_vars['AWS_REGION']}")
    
    # Only include non-None values in the returned dict
    return {k: v for k, v in env_vars.items() if v is not None}

# Initialize AWS environment variables
aws_env_vars = get_aws_env_vars()

def init_mcp_client(name: str, command: str, args: Optional[list] = None, env: Optional[dict] = None) -> Optional[MCPClient]:
    """Initialize an MCP client with timeout and retry logic"""
    try:
        logger.info(f"Initializing {name} MCP client...")
        client = MCPClient(lambda: stdio_client(
            StdioServerParameters(
                command=command,
                args=args or [],
                env=env or {}
            )
        ))
        client.start()
        logger.info(f"{name} MCP client initialized successfully")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize {name} MCP client: {e}")
        return None

# Initialize MCP clients with error handling
mcp_clients = {}

def initialize_mcp_clients() -> Dict[str, Any]:
    """Initialize all MCP clients with proper error handling."""
    clients = {}
    
    try:
        # AWS Documentation MCP client
        clients["docs"] = init_mcp_client(
            "AWS Documentation",
            "uvx",
            ["awslabs.aws-documentation-mcp-server@latest"]
        )
        
        # AWS Diagram MCP client
        clients["diagram"] = init_mcp_client(
            "AWS Diagram",
            "uvx",
            ["awslabs.aws-diagram-mcp-server@latest"]
        )
        
        # AWS Core MCP client
        clients["core"] = init_mcp_client(
            "AWS Core",
            "uvx",
            ["awslabs.core-mcp-server@latest"]
        )
        
        # AWS Cost MCP client
        clients["cost"] = init_mcp_client(
            "AWS Cost",
            "uvx",
            ["awslabs.cost-analysis-mcp-server@latest"],
            aws_env_vars
        )
        
        # AWS CloudFormation MCP client
        clients["cfn"] = init_mcp_client(
            "AWS CloudFormation",
            "uvx",
            ["awslabs.cfn-mcp-server@latest"],
            aws_env_vars
        )
        
        # Note: Lambda MCP client removed as requested
        
    except Exception as e:
        logger.error(f"Error initializing MCP clients: {e}")
    
    return clients

# Initialize MCP clients at module load time
mcp_clients = initialize_mcp_clients()

def get_tools() -> list:
    """Get all available tools from MCP clients with error handling."""
    try:
        logger.info("Initializing tools...")
        
        # Initialize core tools
        tools = [
             # AWS tool with STS support
            editor, 
            file_read, 
            file_write, 
            shell, 
            python_repl, 
            http_request, 
            image_reader, 
            generate_image, 
            speak, 
            calculator, 
            current_time, 
            load_tool, 
            swarm
        ]
        
        logger.info(f"Initialized {len(tools)} core tools")
        
        # Verify AWS tool is available
        if use_aws_sts:
            logger.info("AWS tool 'use_aws_sts' is available")
        else:
            logger.warning("AWS tool 'use_aws_sts' is not available!")
        
        # Add tools from MCP clients if they're available
        for client_name, client in mcp_clients.items():
            if client:
                try:
                    logger.info(f"Getting tools from {client_name} MCP client...")
                    client_tools = client.list_tools_sync()
                    if isinstance(client_tools, list):
                        logger.info(f"Adding {len(client_tools)} tools from {client_name}")
                        tools.extend(client_tools)
                    else:
                        logger.warning(f"Unexpected tools format from {client_name} MCP client")
                except Exception as e:
                    logger.warning(f"Failed to get tools from {client_name} MCP client: {e}")
        
        # Ensure all tools have a name attribute
        logger.info("Processing tool names...")
        for tool in tools:
            if not hasattr(tool, 'name'):
                tool.name = str(tool).split(' ')[0].strip('<>')
            logger.debug(f"Tool available: {tool.name}")
        
        logger.info(f"Total tools loaded: {len(tools)}")
        return tools
        
    except Exception as e:
        logger.error(f"Error initializing tools: {e}", exc_info=True)
        raise

# Available Bedrock models with their IDs and display names
AVAILABLE_MODELS = {
    "claude-3.7": {
        "id": "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        "display_name": "Claude 3.7 (Recommended)",
    },
    "claude-3.5-sonnet": {
        "id": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        "display_name": "Claude 3.5 Sonnet (Recommended)",
    },
    "claude-3-sonnet": {
        "id": "us.anthropic.claude-3-sonnet-20240229-v1:0",
        "display_name": "Claude 3 Sonnet (Recommended)",
    },
    "claude-3-haiku": {
        "id": "anthropic.claude-3-haiku-20240307-v1:0",
        "display_name": "Claude 3 Haiku (Fast & Cost-Effective)",
    },
    "claude-3-opus": {
        "id": "anthropic.claude-3-opus-20240229-v1:0",
        "display_name": "Claude 3 Opus (Most Capable)",
    },
    "Amazon-Titan-Premier": {
        "id": "us.amazon.titan-premier-v1:0",
        "display_name": "Amazon Titan Premier (Recommended)",
    },
    "Amazon-Nova-Pro": {
        "id": "us.amazon.nova-pro-v1:0",
        "display_name": "Amazon Nova Pro (Recommended)",
    },
    "Amazon-Nova-Premier": {
        "id": "us.amazon.nova-premier-v1:0",
        "display_name": "Amazon Nova Premier (Fast & Cost-Effective)",
    },
}

# Default model
DEFAULT_MODEL = "Amazon-Nova-Premier"

def get_model(model_name: Optional[str] = None) -> BedrockModel:
    """Get a Bedrock model by name or return the default model.
    
    Args:
        model_name: Name of the model to use. If None, uses the default model.
        
    Returns:
        An initialized BedrockModel instance.
    """
    from botocore.config import Config
    import time
    import random
    
    model_key = model_name or DEFAULT_MODEL
    model_config = AVAILABLE_MODELS.get(model_key, AVAILABLE_MODELS[DEFAULT_MODEL])
    
    logger.info(f"Using model: {model_config['display_name']} ({model_key})")
    
    # Configure retries and timeouts
    config = Config(
        region_name=os.environ.get("AWS_REGION", "us-east-1"),
        retries={
            'max_attempts': 5,  # Increased from default 3
            'mode': 'adaptive',  # Uses exponential backoff
        },
        connect_timeout=30,  # 30 seconds connection timeout
        read_timeout=300,    # 300 seconds (5 minutes) read timeout
    )
    
    # Add jitter to avoid thundering herd problem
    time.sleep(random.uniform(0, 1))
    
    return BedrockModel(
        model_id=model_config["id"],
        region_name=os.environ.get("AWS_REGION", "us-east-1"),
        temperature=0.1,
        config=config
    )

# Initialize the default model
bedrock_model = get_model()

# System prompt for the agent
system_prompt = """
You are an expert AWS Cloud Engineer assistant. Your job is to help with AWS infrastructure 
management, optimization, security, and best practices. You can:
- Answer questions about AWS services
- Help troubleshoot AWS issues
- Provide AWS best practices
- Assist with AWS CLI commands
- Help with AWS CloudFormation templates
- Optimize AWS costs
- Implement security best practices

Very Important:
- get the account number from user and region from user if not specified use us-east-1
- for the bedrock access use the default credentials.
- use Strands-Agent-Assume-Role for assume role purposes.

When asked to create diagrams, use the AWS diagram MCP tools to generate visual representations
of architecture based on the user's description. Be creative and thorough in translating text
descriptions into complete architecture diagrams.

Always provide clear, actionable advice with specific AWS CLI commands or console steps when applicable.
Focus on security best practices and cost optimization in your recommendations.

IMPORTANT: Never include <thinking> tags or expose your internal thought process in responses.
"""

# Dictionary to store agent instances
agent_instances = {}

def get_agent(model_name: Optional[str] = None) -> Agent:
    """Get or create an agent with the specified model.
    
    Args:
        model_name: Name of the model to use. If None, uses the default model.
        
    Returns:
        An initialized Agent instance with the specified model.
    """
    global agent_instances
    
    model_key = model_name or DEFAULT_MODEL
    
    if model_key not in agent_instances:
        try:
            # Get the model
            model = get_model(model_key)
            
            # Create agent with tools and model
            agent_instances[model_key] = Agent(
                tools=get_tools(),
                model=model,
                system_prompt=system_prompt
            )
            logger.info(f"Created new agent instance for model: {model_key}")
            
        except Exception as e:
            error_msg = f"Failed to create agent for model {model_key}: {e}"
            logger.error(error_msg, exc_info=True)
            # Fall back to default model if the selected one fails
            if model_key != DEFAULT_MODEL:
                logger.info(f"Falling back to default model: {DEFAULT_MODEL}")
                return get_agent(DEFAULT_MODEL)
            raise
    
    return agent_instances[model_key]

# Initialize the default agent
agent = get_agent()

def cleanup():
    """Clean up MCP clients on application exit"""
    global mcp_clients
    logger.info("Cleaning up MCP clients...")
    
    for name, client in list(mcp_clients.items()):
        if client:
            try:
                client.stop()
                logger.info(f"Stopped {name} MCP client")
            except Exception as e:
                logger.error(f"Error stopping {name} MCP client: {e}")
    
    mcp_clients = {}
    logger.info("MCP clients cleanup completed")

# Register cleanup handler
atexit.register(cleanup)

# Function to execute a predefined task
def execute_predefined_task(task_key: str) -> str:
    """Execute a predefined cloud engineering task"""
    if task_key not in PREDEFINED_TASKS:
        return f"Error: Task '{task_key}' not found in predefined tasks."
    
    task_description = PREDEFINED_TASKS[task_key]
    return execute_custom_task(task_description)

# Function to execute a custom task
def execute_custom_task(task_description: str, model_name: Optional[str] = None, max_retries: int = 3) -> str:
    """Execute a custom cloud engineering task based on description with retry logic
    
    Args:
        task_description: The task description to execute
        model_name: Optional model name to use for this task. If None, uses the default model.
        max_retries: Maximum number of retry attempts for transient failures
        
    Returns:
        The result of the task execution
    """
    import time
    import random
    from botocore.exceptions import (
        ReadTimeoutError, ConnectTimeoutError,
        ConnectionError as BotoConnectionError,
        ClientError
    )
    
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Executing task with model '{model_name or DEFAULT_MODEL}' (Attempt {attempt + 1}/{max_retries}): {task_description}")
            
            # Get or create the agent with the specified model
            task_agent = get_agent(model_name)

            task_agent.tool.load_tool(
                name="use_aws_sts",  # The name to register the tool under
                path="./tools/use_aws_sts.py"  # Path to the Python file containing the tool
            )   
            
            # Add jitter to avoid thundering herd problem
            if attempt > 0:
                backoff = (2 ** attempt) + random.uniform(0, 1)
                logger.info(f"Retrying in {backoff:.2f} seconds...")
                time.sleep(backoff)
            
            # Execute the task using the agent
            result = task_agent(task_description)
            
            # Handle different response formats
            if hasattr(result, 'message'):
                result = result.message
            elif hasattr(result, 'content'):
                result = result.content
                
            logger.info("Task completed successfully")
            return str(result)
            
        except (ReadTimeoutError, ConnectTimeoutError, BotoConnectionError) as e:
            last_exception = e
            logger.warning(f"Attempt {attempt + 1} failed with timeout/connection error: {str(e)}")
            if attempt == max_retries - 1:
                logger.error(f"All {max_retries} attempts failed with timeout/connection errors")
                return f"Error: Request timed out after {max_retries} attempts. Please try again later or check your network connection."
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_msg = f"AWS Client Error ({error_code}): {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg
            
        except Exception as e:
            last_exception = e
            logger.error(f"Unexpected error on attempt {attempt + 1}: {str(e)}", exc_info=True)
            if attempt == max_retries - 1:
                return f"Error: {str(last_exception)}"
    
    return f"Error: Failed after {max_retries} attempts. Last error: {str(last_exception)}"

# Function to get predefined tasks
def get_predefined_tasks() -> Dict[str, str]:
    """Return the dictionary of predefined tasks"""
    return PREDEFINED_TASKS


def list_available_models() -> None:
    """List all available models with their display names."""
    print("\nAvailable models:")
    print("-" * 50)
    for model_key, model_info in AVAILABLE_MODELS.items():
        default_indicator = " (default)" if model_key == DEFAULT_MODEL else ""
        print(f"{model_key}: {model_info['display_name']}{default_indicator}")
    print()

if __name__ == "__main__":
    import argparse
    
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="AWS Cloud Engineering Agent")
    parser.add_argument("--model", type=str, help="Model to use for the task")
    parser.add_argument("--list-models", action="store_true", help="List available models and exit")
    parser.add_argument("task", nargs="?", help="Task to execute (or leave empty for interactive mode)")
    
    args = parser.parse_args()
    
    if args.list_models:
        list_available_models()
        sys.exit(0)
    
    if args.task:
        # Execute a single task with the specified model
        result = execute_custom_task(args.task, args.model)
        print(result)
    else:
        # Interactive mode
        print("AWS Cloud Engineering Agent (Interactive Mode)")
        print("Type 'exit' or 'quit' to end the session")
        print("Type 'list-models' to see available models")
        print("Type 'change-model <model_name>' to switch models")
        print("-" * 50)
        
        current_model = args.model or DEFAULT_MODEL
        
        while True:
            try:
                # Get user input
                user_input = input(f"\n[{current_model}]> ").strip()
                
                # Check for exit commands
                if user_input.lower() in ('exit', 'quit'):
                    print("Exiting...")
                    break
                    
                # Check for model listing
                if user_input.lower() == 'list-models':
                    list_available_models()
                    continue
                    
                # Check for model change
                if user_input.lower().startswith('change-model '):
                    new_model = user_input.split(' ', 1)[1].strip()
                    if new_model in AVAILABLE_MODELS:
                        current_model = new_model
                        print(f"Changed model to: {AVAILABLE_MODELS[new_model]['display_name']} ({new_model})")
                    else:
                        print(f"Error: Unknown model '{new_model}'. Use 'list-models' to see available models.")
                    continue
                
                # Execute the task with the current model
                if user_input:  # Only process non-empty input
                    result = execute_custom_task(user_input, current_model)
                    print("\n" + "-" * 50)
                    print(result)
                    print("-" * 50)
                
            except KeyboardInterrupt:
                print("\nUse 'exit' or 'quit' to end the session")
            except Exception as e:
                print(f"Error: {str(e)}")