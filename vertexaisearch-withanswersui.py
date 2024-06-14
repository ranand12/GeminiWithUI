import re
import chainlit as cl
from typing import List
import os
from typing import Dict, Optional
from datetime import datetime
from typing import List, Optional, Tuple
from langsmith.run_helpers import traceable 

# Update with your API URL if using a hosted instance of Langsmith.
from dotenv import load_dotenv
load_dotenv()
from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine_v1beta as discoveryengine
from google.cloud.discoveryengine_v1 import Conversation
import requests
from google.auth import default
from google.auth.transport.requests import Request


os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_TRACING_V2"] = "true"
project_name = os.environ["LANGCHAIN_PROJECT"]  # Update with your project name
credentials, project = default()
model_version = os.environ["model_version"]
project_id = os.environ["project_id"]
location = os.environ["location"]  # Values: "global", "us", "eu"
data_store_id = os.environ["data_store_id"]
prompt=os.environ["prompt"]
authorizedDomainList=os.environ["authorizedDomainList"]
#query_rephraser_spec1 = discoveryengine.AnswerQueryRequest.QueryUnderstandingSpec.QueryRephraserSpec(disable=False)
#query_understand_spec1 = discoveryengine.AnswerQueryRequest.QueryUnderstandingSpec(query_rephraser_spec=query_rephraser_spec1)
model_spec1 = discoveryengine.AnswerQueryRequest.AnswerGenerationSpec.ModelSpec(model_version=model_version)
prompt_spec1 = discoveryengine.AnswerQueryRequest.AnswerGenerationSpec.PromptSpec(preamble=prompt)
related_question_spec = discoveryengine.AnswerQueryRequest.RelatedQuestionsSpec(enable=True)
answer_generation_spec = discoveryengine.AnswerQueryRequest.AnswerGenerationSpec(model_spec=model_spec1,prompt_spec=prompt_spec1,include_citations=True,ignore_low_relevant_content=True)




def parse_external_link(url=''):
    protocol_regex = r'^(gs)://'
    match = re.match(protocol_regex, url)
    protocol = match.group(1) if match else None
    if protocol == 'gs':
        return re.sub(protocol_regex, 'https://storage.cloud.google.com/', url)
    else:
        return url


def add_references_answers(text: str, citations: List,response):
    textref = f"\n References:"
    textlinks = []
    
    for i, citation in enumerate(citations):
        citindex = int(citation.sources[0].reference_id)
        url = response.answer.references[citindex].chunk_info.document_metadata.uri
        title = response.answer.references[citindex].chunk_info.document_metadata.title
        if not any(url in link for link in textlinks):
            textlinks.append(f"\n [{title}]({url})")
    text = text + textref + "".join(textlinks)
    return text


@cl.oauth_callback
def oauth_callback(
  provider_id: str,
  token: str,
  raw_user_data: Dict[str, str],
  default_user: cl.User,
) -> Optional[cl.User]:
    authorizedDomains =authorizedDomainList
    if provider_id == "google":
        if raw_user_data["hd"] in authorizedDomains:
            return default_user
        return None

@traceable(run_type="llm")
def initialize_client():
    client_options = (
        ClientOptions(api_endpoint="discoveryengine.googleapis.com")
    )
    client = discoveryengine.ConversationalSearchServiceClient(client_options=client_options)
    return client


client = initialize_client()



def set_session_variables():
    credentials.refresh(Request())
    access_token = credentials.token
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
@traceable(run_type="llm")
async def on_message(message: cl.Message):
    query = discoveryengine.Query()
    query.text = message.content
    request = discoveryengine.AnswerQueryRequest(
    query=query,
    session=current_session,
    serving_config= f"projects/{project_id}/locations/{location}/collections/default_collection/dataStores/{data_store_id}/servingConfigs/default_serving_config",answer_generation_spec=answer_generation_spec,related_questions_spec=related_question_spec )
    response = client.answer_query(request=request)
    content = f"{add_references_answers(response.answer.answer_text, response.answer.citations,response)}"
    async with cl.Step(name="Related questions") as parent_step:
        parent_step.output = response.answer.related_questions
    await cl.Message(
        content=content
    ).send()
    return content
    
   

if __name__ == "__main__":
    from chainlit.cli import run_chainlit

    run_chainlit(__file__)
