"""
GW_chat5_UI.py - Main UI application for European Health Information Gateway

This module contains the main Gradio interface for the WHO European Health 
Information Gateway chat application using AutoGen agents.
"""

import os
import asyncio
import concurrent.futures
import threading
from dotenv import load_dotenv
from openai import OpenAI
import gradio as gr

# AutoGen imports
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.agents import AssistantAgent
from autogen_core import CancellationToken
from autogen_agentchat.messages import TextMessage

# Local imports
from GW_chat5_db import (
    search_indicators_advanced, 
    search_ind_name, 
    load_countries_data, 
    load_country_groups_data, 
    load_about_info
)
from GW_chat5_API import create_plot


def setup_environment():
    """
    Load environment variables and initialize OpenAI client.
    
    Returns:
        OpenAI: Initialized OpenAI client
    """
    load_dotenv(override=True)
    return OpenAI()


def create_system_prompt():
    """
    Create the system prompt for the AutoGen agent.
    
    Returns:
        str: System prompt string
    """
    agent_name = "European Health Information Gateway"
    search_indicator = "search_indicators_advanced"
    create_image = "create_plot"
    
    # Load data files
    euro_countries = load_countries_data()
    euro_cntry_groups = load_country_groups_data()
    summary = load_about_info()
    
    system_prompt = f"""You are acting as {agent_name}. You are answering questions on {agent_name}'s data portal, \
particularly questions related to {agent_name}'s health data, background, provide the links to health indicators from tool {search_indicator} \
Your responsibility is to represent {agent_name} for interactions on the website as faithfully as possible. \
    You task is to  guides users around gateway.euro.who.int and also helps them analyze and compare data \
You are given a table of {agent_name}'s indicators links in tool {search_indicator} summary about the portal which you can use to answer questions.\
    To find the indicator code for the indicator name, use tool {search_ind_name}.\
Use the tool {create_image} to create one single image the return URL to display the png image in the chat. Use parameters countries and country_groups from tool {create_image} to make one image only \
     IMPORTANT provide the link to download the image!The link should be visible bellow the image.\
Be professional and engaging, as if talking to data health scientist or a usual person who came across the website and interested in health data. \
If you don't know the answer, say so. \
IMPORTANT: ONLY provide URLs that are retrieved from the database using the search {search_indicator}. Do NOT provide any URLs from your training \
data as they may be outdated. Always use the {search_indicator} tool to get current URLS and display up to five links"""

    system_prompt += f"""\n\n## Summary:\n{summary}\n\n## health indicators list from tool {search_indicator}:please respond with links only from provided list\n\n \
## list of countries in WHO Europe in JSON:\n{euro_countries}\n\n \
## list of countries groups WHO Europe in JSON:\n{euro_cntry_groups}\n\n"""
    system_prompt += f"With this context, please chat with the user, always staying in character as {agent_name}."
    
    return system_prompt


def create_autogen_agent():
    """
    Create and configure the AutoGen assistant agent.
    
    Returns:
        AssistantAgent: Configured AutoGen agent
    """
    # Create model client
    model_client = OpenAIChatCompletionClient(model="gpt-4o-mini")
    
    # Create system prompt
    system_prompt = create_system_prompt()
    
    # Define tools
    gw_tools = [search_indicators_advanced, create_plot, search_ind_name]
    
    # Create smart agent
    smart_agent = AssistantAgent(
        name='gw_chat',
        model_client=model_client,
        system_message=system_prompt,
        model_client_stream=True,
        tools=gw_tools,
        reflect_on_tool_use=True
    )
    
    return smart_agent


async def chat_async(message: str, history) -> str:
    """
    Async chat function that properly handles the smart agent.
    
    Args:
        message (str): User message
        history: Chat history (unused but required by Gradio)
    
    Returns:
        str: Agent response
    """
    try:
        # Convert string message to TextMessage object that autogen expects
        text_message = TextMessage(content=message, source="user")
        response = await smart_agent.on_messages([text_message], cancellation_token=CancellationToken())
        # Access the content from the response
        return response.chat_message.content
    except Exception as e:
        return f"Error: {str(e)}"


def chat(message: str, history) -> str:
    """
    Chat function that properly handles the smart agent in Jupyter environment.
    
    Args:
        message (str): User message
        history: Chat history (unused but required by Gradio)
    
    Returns:
        str: Agent response
    """
    try:
        # Create a new event loop in a separate thread to avoid conflicts with Jupyter's loop
        def run_async():
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(chat_async(message, history))
            finally:
                loop.close()
        
        # Run the async function in a separate thread
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_async)
            return future.result()
            
    except Exception as e:
        return f"Error: {str(e)}"


def main():
    """
    Main function to launch the Gradio chat interface.
    """
    # Setup environment
    openai_client = setup_environment()
    
    # Create AutoGen agent
    global smart_agent
    smart_agent = create_autogen_agent()
    
    # Launch the Gradio chat interface with proper message format
    interface = gr.ChatInterface(
        fn=chat,
        title="European Health Information Gateway Chat",
        description="Ask questions about health indicators and data from the WHO European Region",
        examples=[
            "Plot life expectancy at birth for Denmark and EU",
            "Show me data about measles in the Nordic region",
            "Show maternal mortality rates in WHO European Region",
            "Compare the estimated maternal mortality ratios for both the European Union and the WHO European Region"
        ],
        type="messages"  # Use the new message format to avoid deprecation warning
    )
    
    interface.launch(share=False)


if __name__ == "__main__":
    main()
