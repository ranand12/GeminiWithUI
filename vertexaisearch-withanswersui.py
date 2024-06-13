import re
import chainlit as cl
from typing import List
import os
from typing import Dict, Optional
from datetime import datetime
from typing import List, Optional, Tuple

# Update with your API URL if using a hosted instance of Langsmith.
from dotenv import load_dotenv
load_dotenv()
from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine_v1beta as discoveryengine
from google.cloud.discoveryengine_v1 import Conversation
import requests
from google.auth import default
from google.auth.transport.requests import Request


credentials, project = default()
credentials.refresh(Request())
access_token = credentials.token


project_id = os.environ["project_id"]
location = os.environ["location"]  # Values: "global", "us", "eu"
data_store_id = os.environ["data_store_id"]
query_rephraser_spec1 = discoveryengine.AnswerQueryRequest.QueryUnderstandingSpec.QueryRephraserSpec(disable=True)
query_understand_spec1 = discoveryengine.AnswerQueryRequest.QueryUnderstandingSpec(query_rephraser_spec=query_rephraser_spec1)
model_spec1 = discoveryengine.AnswerQueryRequest.AnswerGenerationSpec.ModelSpec(model_version="gemini-1.5-flash-001/answer_gen/v1",)
prompt_spec1 = discoveryengine.AnswerQueryRequest.AnswerGenerationSpec.PromptSpec(preamble="Given the conversation between a user and a helpful assistant and some search results, create a final answer for the assistant. Always respond back to the user in the same language as the user. The answer should use all relevant information from the search results, not introduce any additional information, and use exactly the same words as the search results when possible. The assistant's answer should be formatted as a bulleted list. Each list item should start with the \"-\" symbol.")
answer_generation_spec = discoveryengine.AnswerQueryRequest.AnswerGenerationSpec(model_spec=model_spec1,prompt_spec=prompt_spec1,include_citations=True,ignore_low_relevant_content=True)




def parse_external_link(url=''):
    protocol_regex = r'^(gs)://'
    match = re.match(protocol_regex, url)
    protocol = match.group(1) if match else None
    if protocol == 'gs':
        return re.sub(protocol_regex, 'https://storage.cloud.google.com/', url)
    else:
        return url


def add_references(text: str, search_results: List):
    textref = f"\n References"
    textlinks = ""
    for i, search_result in enumerate(search_results[:5]):
        placeholder = f"[{i + 1}]"
        textlinks+= (f"\n [{placeholder} {search_result.document.struct_data['title']}]({search_result.document.struct_data['url']})")
    text = text + textref + textlinks
    return text


@cl.oauth_callback
def oauth_callback(
  provider_id: str,
  token: str,
  raw_user_data: Dict[str, str],
  default_user: cl.User,
) -> Optional[cl.User]:
    authorizedDomains =["google.com"]
    if provider_id == "google":
        if raw_user_data["hd"] in authorizedDomains:
            return default_user
        return None


def initialize_client():
    client_options = (
        ClientOptions(api_endpoint="discoveryengine.googleapis.com")
    )
    client = discoveryengine.ConversationalSearchServiceClient(client_options=client_options)
    return client


client = initialize_client()



def set_session_variables():
    url = (f"https://discoveryengine.googleapis.com/v1beta/projects/{project_id}/locations/global/collections/default_collection/dataStores/{data_store_id}/sessions")
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = {
        "userPseudoId": "",  # Set your user ID
    }
    response = requests.post(url, headers=headers,json=data)
    return response.json()['name']



@cl.on_chat_start
async def on_chat_start():
    
    current_session_local = set_session_variables()
    global current_session
    current_session = current_session_local
    cl.user_session.set("conversation", current_session)
    await cl.Message(content=f"Welcome to the Chatbot. Please ask your question below.", type="system_message").send()



@cl.on_message
async def on_message(message: cl.Message):
    query = discoveryengine.Query()
    query.text = message.content
    request = discoveryengine.AnswerQueryRequest(
    query=query,
    session=current_session,
    serving_config= f"projects/{project_id}/locations/{location}/collections/default_collection/dataStores/{data_store_id}/servingConfigs/default_serving_config",
    query_understanding_spec = query_understand_spec1,answer_generation_spec=answer_generation_spec
    )
    response = client.answer_query(request=request)

    await cl.Message(
        content=response.answer.answer_text
    ).send()
    return response
    
   

if __name__ == "__main__":
    from chainlit.cli import run_chainlit

    run_chainlit(__file__)
