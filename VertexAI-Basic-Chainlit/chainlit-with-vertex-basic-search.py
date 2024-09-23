import re
import chainlit as cl
from typing import List
import os
from typing import Dict, Optional
from datetime import datetime
from typing import List, Optional, Tuple
from dotenv import load_dotenv
load_dotenv()
from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine_v1 as discoveryengine
from google.cloud.discoveryengine_v1 import Conversation



project_id = os.environ["project_id"]
location = os.environ["location"]  # Values: "global", "us", "eu"
data_store_id = os.environ["data_store_id"]



def parse_external_link(url=''):
    protocol_regex = r'^(gs)://'

    match = re.match(protocol_regex, url)
    protocol = match.group(1) if match else None

    if protocol == 'gs':
        return re.sub(protocol_regex, 'https://storage.cloud.google.com/', url)
    else:
        return url


def replace_references(text: str, urls: List[str]) -> str:
    # Split text into parts using '[' and ']'
    parts = text.split('[')

    # Initialize the parsed text
    parsed_text = parts[0]

    # Iterate through the remaining parts
    for part in parts[1:]:
        # Check if the part contains a reference
        if ']' in part:
            # Extract the reference number
            reference = part.split(']')[0]
            references = [int(ref.strip()) for ref in reference.split(',')]
            # Create HTML links for each reference
            links = []
            for ref in references:
                if ref <= len(urls):
                    link = f"{parse_external_link(urls[ref - 1].uri)}"
                    links.append(link)
            # Replace the reference with HTML links
            parsed_text += '[' + ''.join(links) + ']' + part.split(']')[1]
        else:
            parsed_text += '[' + part  # Re-attach if no reference

    return parsed_text
  




def initialize_client():
    #  For more information, refer to:
    # https://cloud.google.com/generative-ai-app-builder/docs/locations#specify_a_multi-region_for_your_data_store
    client_options = (
        ClientOptions(api_endpoint=f"{location}-discoveryengine.googleapis.com")
        if location != "global"
        else None
    )
    # Create a client
    client = discoveryengine.ConversationalSearchServiceClient(
        client_options=client_options
    )
    return client


discoveryengine_client = initialize_client()


def initialize_conversation(client) -> Conversation:
    conversation_instance = client.create_conversation(
        # The full resource name of the data store
        # e.g. projects/{project_id}/locations/{location}/dataStores/{data_store_id}
        parent=client.data_store_path(
            project=project_id, location=location, data_store=data_store_id
        ),
        conversation=discoveryengine.Conversation(),
    )
    return conversation_instance


@cl.on_chat_start
async def on_chat_start():
    conversation = initialize_conversation(discoveryengine_client)
    cl.user_session.set("conversation", conversation.name)
    await cl.Message(content=f"Welcome to the Chatbot. Please ask your question below.", type="system_message").send()



@cl.action_callback("ask_new_question")
async def on_action(action):
    conversation = initialize_conversation(discoveryengine_client)
    cl.user_session.set("conversation", conversation.name)
    await cl.Message(content=f"Sure, what's your next question?", type="system_message").send()



@cl.on_message
async def on_message(message: cl.Message):
    print(cl.user_session.get("conversation"))
    request = discoveryengine.ConverseConversationRequest(
        name=cl.user_session.get("conversation"),
        query=discoveryengine.TextInput(input=message.content),
        serving_config=discoveryengine_client.serving_config_path(
            project=project_id,
            location=location,
            data_store=data_store_id,
            serving_config="default_config",
        ),
        # Options for the returned summary
        summary_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec(
            # Number of results to include in summary
            summary_result_count=3,
            model_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec.ModelSpec(version="gemini-1.5-flash-001/answer_gen/v1"),
            model_prompt_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec.ModelPromptSpec
            (preamble="Given the conversation between a user and a helpful assistant and some search results, create a final answer for the assistant. Always respond back to the user in the same language as the user. The answer should use all relevant information from the search results, not introduce any additional information, and use exactly the same words as the search results when possible. The assistant's answer should be formatted as a bulleted list."),
            include_citations=True,
        ),
    )
    response = discoveryengine_client.converse_conversation(request)
    try:
        content = f"{replace_references(response.reply.summary.summary_text, response.reply.summary.summary_with_metadata.references)}"
        #content = f"{response.reply.summary.summary_text}"
    except AttributeError:
        content = f"{response.reply.summary.summary_text}"
    # Send a response back to the user
    await cl.Message(
        content=content
    ).send()
    return content
    
   

if __name__ == "__main__":
    from chainlit.cli import run_chainlit

    run_chainlit(__file__)
