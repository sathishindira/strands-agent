# CloudSage Strands-Agent

This project demonstrates CloudSage, a powerful AWS cloud engineering agent built with the [Strands Agents SDK](https://strandsagents.com/0.1.x/), showcasing how easily you can create sophisticated AI agents with a model-first approach. CloudSage can perform various cloud engineering tasks on AWS accounts, such as resource monitoring, security analysis, cost optimization, and more.

## Features

CloudSage Strands-Agent provides the following capabilities:
- **AWS Resource Management**: Monitor, analyze, and manage AWS resources across multiple services
- **Security Analysis**: Identify security vulnerabilities and recommend best practices
- **Cost Optimization**: Find cost-saving opportunities and recommend resource optimizations
- **Infrastructure Diagramming**: Generate AWS architecture diagrams from text descriptions
- **AWS Documentation Search**: Find relevant AWS documentation for any service or feature
- **Direct AWS API Access**: Execute AWS CLI commands through the agent interface

### Predefined Tasks
- EC2 instance status monitoring
- S3 bucket analysis and management
- CloudWatch alarm status checking
- IAM user activity tracking
- Security group vulnerability analysis
- Cost optimization recommendations
- Lambda function management
- RDS instance monitoring
- VPC configuration analysis
- EBS volume optimization
- AWS architecture diagram generation

### Technical Features
- **Strands Agents SDK Integration**: Leverages the Strands framework for agent capabilities with its model-first approach
- **AWS Bedrock Integration**: Uses Amazon Nova Premier model (`us.amazon.nova-premier-v1`) for AI capabilities
- **MCP Tools Integration**: Incorporates AWS Documentation and AWS Diagram MCP tools
- **AWS CLI Integration**: Direct access to AWS API through the `use_aws` tool
- **Streamlit UI**: User-friendly interface for interacting with the agent
- **Containerized Deployment**: Docker-based deployment for portability

## Local Development

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- AWS CLI configured with appropriate permissions
- AWS Bedrock access with permissions for Amazon Nova Premier model

### Option 1: Using Docker Compose (Recommended)

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd cloudeng-strands-agent
   ```

2. Create a `.env` file in the project root with your AWS credentials:
   ```env
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   AWS_REGION=your_preferred_region
   ```

3. Build and start the application using Docker Compose:
   ```bash
   docker-compose up --build
   ```

4. Access the Streamlit UI at http://localhost:8501

### Option 2: Direct Python Execution

1. Clone the repository and navigate to the project directory:
   ```bash
   git clone <repository-url>
   cd cloudeng-strands-agent
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up your AWS credentials (if not already configured):
   ```bash
   aws configure
   ```

5. Run the Streamlit application:
   ```bash
   streamlit run app.py
   ```

6. Access the application at http://localhost:8501

## Environment Variables

The following environment variables are used:

- `AWS_REGION`: AWS region for API calls (must be a region where Amazon Nova Premier is available)
- `AWS_ACCESS_KEY_ID`: AWS access key
- `AWS_SECRET_ACCESS_KEY`: AWS secret key

## Security Considerations

- Always keep your AWS credentials secure and never commit them to version control
- Use IAM roles with least privilege principle
- Bedrock permissions should be scoped to necessary model invocation actions
- All AWS API communications use HTTPS
- Sensitive information should not be stored in the application

## Strands Agents SDK

This project leverages the [Strands Agents SDK](https://strandsagents.com/0.1.x/), a powerful framework for building AI agents with a model-first approach. Key features include:

### Model-First Approach
Strands Agents SDK uses a model-first approach where the LLM acts as the orchestrator, making decisions about which tools to use and when. This approach allows for more flexible and intelligent agents that can adapt to complex scenarios.

### Agentic Loop Architecture
The SDK implements an agentic loop architecture where:
1. The agent receives a user request
2. The LLM analyzes the request and determines the best course of action
3. The agent executes tools as directed by the LLM
4. Results are fed back to the LLM for further analysis
5. The process repeats until the task is complete

### MCP Integration
This project utilizes two Model Context Protocol (MCP) servers:
- **AWS Documentation MCP Server**: Provides access to comprehensive AWS documentation
- **AWS Diagram MCP Server**: Enables the agent to generate visual AWS architecture diagrams

### Benefits
- **Simplified Development**: Create powerful agents with minimal code
- **Flexible Tool Integration**: Easily add new tools and capabilities
- **Intelligent Decision Making**: Let the LLM decide the best approach to solving problems
- **Transparent Reasoning**: Follow the agent's thought process and tool usage
- **Extensible Framework**: Build on top of the core architecture for specialized use cases
- **Built-in MCP**: Native support for Model Context Protocol (MCP) servers, enabling access to thousands of pre-built tools

### Documentation
For more information about Strands Agents SDK, visit the [official documentation](https://strandsagents.com/0.1.x/).

## License

This project is licensed under the MIT License - see the LICENSE file for details.
