import streamlit as st
from cloud_engineer_agent import execute_predefined_task, execute_custom_task, get_predefined_tasks, PREDEFINED_TASKS
import re
import ast
import os
from PIL import Image
import logging
from fix_diagram_paths import fix_diagram_paths

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="CloudSage Strands-Agent",
    page_icon="☁️",
    layout="wide"
)

# Cache the agent functions
@st.cache_resource
def get_agent_functions():
    # This is just a placeholder to maintain the caching behavior
    # The actual agent is now initialized directly in cloud_engineer_agent.py
    return True

# Function to remove thinking process from response and handle formatting
def clean_response(response):
    # Handle None or empty responses
    if not response:
        return ""
    
    # Convert to string if it's not already
    if not isinstance(response, str):
        try:
            response = str(response)
        except:
            return "Error: Could not convert response to string"
    
    # Remove <thinking>...</thinking> blocks
    cleaned = re.sub(r'<thinking>.*?</thinking>', '', response, flags=re.DOTALL)
    
    # Check if response is in JSON format with nested content
    if cleaned.find("'role': 'assistant'") >= 0 and cleaned.find("'content'") >= 0 and cleaned.find("'text'") >= 0:
        try:
            # Try to parse as Python literal
            data = ast.literal_eval(cleaned)
            if isinstance(data, dict) and 'content' in data and isinstance(data['content'], list):
                for item in data['content']:
                    if isinstance(item, dict) and 'text' in item:
                        # Return the text content directly (preserves markdown)
                        return item['text']
        except:
            # If parsing fails, try regex as fallback
            match = re.search(r"'text': '(.+?)(?:'}]|})", cleaned, re.DOTALL)
            if match:
                # Unescape the content to preserve markdown
                text = match.group(1)
                text = text.replace('\\n', '\n')  # Replace escaped newlines
                text = text.replace('\\t', '\t')  # Replace escaped tabs
                text = text.replace("\\'", "'")   # Replace escaped single quotes
                text = text.replace('\\"', '"')   # Replace escaped double quotes
                return text
    
    return cleaned.strip()

# Function to check for image paths in text and display them
def display_message_with_images(content):
    # Use the fix_diagram_paths utility to handle image paths
    content = fix_diagram_paths(content)
    
    # Look for the updated image paths
    display_pattern = r'./generated-diagrams/([\w\-\.]+\.png)'
    image_paths = re.findall(display_pattern, content)
    
    # If no image paths found after processing, just display the content as markdown
    if not image_paths:
        st.markdown(content)
        return
    
    # Display the markdown content first
    st.markdown(content)
    
    # Then display all found images
    for img_name in image_paths:
        img_path = f"./generated-diagrams/{img_name}"
        if os.path.exists(img_path):
            try:
                image = Image.open(img_path)
                st.image(image, caption=f"Generated Diagram: {img_name}", use_container_width=True)
            except Exception as e:
                st.error(f"Error displaying image: {e}")
        else:
            st.warning(f"Image not found: {img_path}")

# Initialize chat history
def init_chat_history():
    if "messages" not in st.session_state:
        st.session_state.messages = []

# Main app
def main():
    init_chat_history()
    
    # Set main title
    st.title("☁️ CloudSage Strands-Agent")
    st.markdown("---")
    
    # Add model selection to sidebar
    st.sidebar.title("Settings")
    
    # Get available models from cloud_engineer_agent
    from cloud_engineer_agent import AVAILABLE_MODELS, DEFAULT_MODEL, get_agent
    
    # Create a list of display names and their corresponding keys
    model_options = [
        (model_data["display_name"], model_key)
        for model_key, model_data in AVAILABLE_MODELS.items()
    ]
    
    # Sort by display name
    model_options.sort(key=lambda x: x[0])
    
    # Initialize session state for model if not exists
    if 'selected_model' not in st.session_state:
        st.session_state.selected_model = DEFAULT_MODEL
    
    # Create model selection dropdown
    selected_model_display = st.sidebar.selectbox(
        "Select AI Model",
        options=[opt[0] for opt in model_options],
        index=next((i for i, (_, key) in enumerate(model_options) 
                  if key == st.session_state.selected_model), 0)
    )
    
    # Get the model key from the selected display name
    selected_model_key = next((key for name, key in model_options 
                             if name == selected_model_display), DEFAULT_MODEL)
    
    # Update session state if model changed
    if selected_model_key != st.session_state.selected_model:
        st.session_state.selected_model = selected_model_key
        st.session_state.messages = []  # Clear chat history on model change
        st.rerun()  # Rerun to apply the new model
    
    # Display current model info
    current_model = AVAILABLE_MODELS.get(st.session_state.selected_model, 
                                       AVAILABLE_MODELS[DEFAULT_MODEL])
    st.sidebar.markdown(f"**Current Model:** {current_model['display_name']}")
    st.sidebar.markdown("---")  # Add a separator
    
    # Create a two-columns layout with sidebar and main content
    # Sidebar for tools and predefined tasks
    with st.sidebar:

        st.markdown("---")
        
        # Predefined Tasks Dropdown - MOVED TO TOP
        st.subheader("Predefined Tasks")
        task_options = list(PREDEFINED_TASKS.values())
        task_keys = list(PREDEFINED_TASKS.keys())
        
        selected_task = st.selectbox(
            "Select a predefined task:",
            options=task_options,
            index=None,
            placeholder="Choose a task..."
        )
        
        if selected_task:
            task_index = task_options.index(selected_task)
            task_key = task_keys[task_index]
            
            if st.button("Run Selected Task", use_container_width=True):
                # Add task to chat as user message
                user_message = f"Please {selected_task.lower()}"
                st.session_state.messages.append({"role": "user", "content": user_message})
                
                # Generate response
                get_agent_functions()  # Ensure agent is cached
                with st.spinner("Working on it..."):
                    try:
                        result = execute_predefined_task(task_key)
                        print(f"RAW AGENT RESPONSE (predefined task '{task_key}'): {result}") # DEBUG LINE
                        cleaned_result = clean_response(result)
                        # Fix image paths before adding to session state
                        fixed_result = fix_diagram_paths(cleaned_result)
                        st.session_state.messages.append({"role": "assistant", "content": fixed_result})
                        st.rerun()
                    except Exception as e:
                        error_message = f"Error executing task: {str(e)}"
                        st.session_state.messages.append({"role": "assistant", "content": error_message})
                        st.rerun()
        
        st.markdown("---")
        
        # AWS configuration info
        st.subheader("AWS Configuration")
        st.info("Using AWS credentials from environment variables")
        
        # Available Tools Section
        st.subheader("Available Tools")
        
        # Display AWS CLI Tool
        st.markdown("**AWS CLI Tool**")
        st.markdown("- `use_aws`: Execute AWS CLI commands")
        st.markdown("**AWS Documentation MCP Tool**")
        st.markdown("**AWS Diagram MCP Tool**")

        # Clear chat button
        st.markdown("---")
        if st.button("Clear Chat History", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    
    # Main content area with chat interface
    st.title("CloudSage Strands-Agent")
    st.markdown("Ask questions about AWS resources, security, cost optimization, or select a predefined task from the sidebar.")
    
    # Display chat messages
    if not st.session_state.messages:
        # Welcome message if no messages
        with st.chat_message("assistant"):
            st.markdown("👋 Hello! I'm your CloudSage Strands-Agent. I can help you manage, optimize, and secure your AWS infrastructure. Select a predefined task from the sidebar or ask me anything about AWS!")
    else:
        # Display existing messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                # Use the special display function that can handle images
                display_message_with_images(message["content"])
    
    # User input
    if prompt := st.chat_input("Ask me about AWS..."):
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Generate response
        get_agent_functions()  # Ensure agent is cached
        with st.spinner(f"Executing with {AVAILABLE_MODELS[st.session_state.selected_model]['display_name']}..."):
            response = execute_custom_task(prompt, st.session_state.selected_model)
            print(f"RAW AGENT RESPONSE (custom task): {response}") # DEBUG LINE
            cleaned_response = clean_response(response)
            # Fix image paths and display the response
            fixed_response = fix_diagram_paths(cleaned_response)
            display_message_with_images(fixed_response)
        
        # Add assistant response to chat history with fixed image paths
        st.session_state.messages.append({"role": "assistant", "content": fixed_response})

if __name__ == "__main__":
    main()