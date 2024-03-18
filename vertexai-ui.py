

import chainlit as cl

from typing import List

from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine_v1 as discoveryengine

project_id = ""
location = "global"                    # Values: "global", "us", "eu"
data_store_id = ""
search_query = ["sample questions"]


def multi_turn_search_sample(
    project_id: str,
    location: str,
    data_store_id: str,
    search_queries: List[str], 
) -> List[discoveryengine.ConverseConversationResponse]:
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
    
    
    # Initialize Multi-Turn Session
    conversation = client.create_conversation(
        # The full resource name of the data store
        # e.g. projects/{project_id}/locations/{location}/dataStores/{data_store_id}
        parent=client.data_store_path(
            project=project_id, location=location, data_store=data_store_id
        ),
        conversation=discoveryengine.Conversation(),
    )
    return client, conversation

client1, conversation1 = multi_turn_search_sample(project_id=project_id,location=location,data_store_id=data_store_id,search_queries=["hello"])


@cl.on_chat_start
async def on_chat_start():
    multi_turn_search_sample(project_id=project_id,location=location,data_store_id=data_store_id,search_queries=["hello"])

@cl.on_message
async def main(message: cl.Message, client = client1, conversation1 = conversation1):
    request = discoveryengine.ConverseConversationRequest(
        name=conversation1.name,
        query=discoveryengine.TextInput(input=message.content),
        serving_config=client1.serving_config_path(
            project=project_id,
            location=location,
            data_store=data_store_id,
            serving_config="default_config",
        ),
        # Options for the returned summary
        summary_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec(
            # Number of results to include in summary
            summary_result_count=3,
            model_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec.ModelSpec(version="preview"),
            model_prompt_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec.ModelPromptSpec(preamble="you are a helpful bot"),
            include_citations=True,
        ),
    )
    response = client1.converse_conversation(request)
    # Send a response back to the user
    await cl.Message(
        content=f"{response.reply.summary.summary_text}",
    ).send()





# @cl.on_chat_start
# def on_chat_start():
#     cl.user_session.set("counter", 0)


# @cl.on_message
# async def on_message(message: cl.Message):
#     counter = cl.user_session.get("counter")
#     counter += 1
#     cl.user_session.set("counter", counter)

#     await cl.Message(content=f"You sent {counter} message(s)!").send()

