import re
import chainlit as cl
from typing import List

from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine_v1 as discoveryengine
from google.cloud.discoveryengine_v1 import Conversation

project_id = ""
location = "global"  # Values: "global", "us", "eu"
data_store_id = ""




def parse_external_link(url=''):
    protocol_regex = r'^(gs)://'

    match = re.match(protocol_regex, url)
    protocol = match.group(1) if match else None

    if protocol == 'gs':
        return re.sub(protocol_regex, 'https://storage.cloud.google.com/', url)
    else:
        return url


def replace_references(text: str, references: List):
    for i, reference in enumerate(references):
        placeholder = f"[{i + 1}]"
        text = text.replace(placeholder,
                            f"{placeholder}({parse_external_link(reference.uri)})")
    return text


def initialize_client():

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
    await cl.Message(content=f"Welcome to the XYZ Chatbot. Please ask your question below.", type="system_message").send()


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
            (preamble="Given the conversation between a user and a helpful assistant and some search results, create a final answer for the assistant. The answer should use all relevant information from the search results, not introduce any additional information, and use exactly the same words as the search results when possible. The assistant's answer should be formatted as a bulleted list."),
            include_citations=True,
        ),
    )
    response = discoveryengine_client.converse_conversation(request)

    try:
        content = f"{replace_references(response.reply.summary.summary_text, response.reply.summary.summary_with_metadata.references)}"
    except AttributeError:
        content = f"{response.reply.summary.summary_text}"
    
    print(response.reply.summary.summary_with_metadata)

    # Send a response back to the user
    await cl.Message(
        content=content
    ).send()


if __name__ == "__main__":
    from chainlit.cli import run_chainlit

    run_chainlit(__file__)
