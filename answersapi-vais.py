from google.cloud import discoveryengine_v1beta as discoveryengine_v1
from google.api_core.client_options import ClientOptions
from dotenv import load_dotenv
load_dotenv()
import os
import requests
from google.auth import default
from google.auth.transport.requests import Request


credentials, project = default()
credentials.refresh(Request())
access_token = credentials.token


# Get the access token from gcloud (assumes gcloud is installed)
project_id = os.environ["project_id"]
location = os.environ["location"]  # Values: "global", "us", "eu"
data_store_id = os.environ["data_store_id"]

def session_variables():
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

session1 = session_variables()




client_options = (
    ClientOptions(api_endpoint="discoveryengine.googleapis.com")
)
client = discoveryengine_v1.ConversationalSearchServiceClient(client_options=client_options)
query = discoveryengine_v1.Query()
query.text = "how about dry cleaner"
query_rephraser_spec1 = discoveryengine_v1.AnswerQueryRequest.QueryUnderstandingSpec.QueryRephraserSpec(disable=True)
query_understand_spec1 = discoveryengine_v1.AnswerQueryRequest.QueryUnderstandingSpec(query_rephraser_spec=query_rephraser_spec1)
model_spec1 = discoveryengine_v1.AnswerQueryRequest.AnswerGenerationSpec.ModelSpec(model_version="gemini-1.5-flash-001/answer_gen/v1",)
prompt_spec1 = discoveryengine_v1.AnswerQueryRequest.AnswerGenerationSpec.PromptSpec(preamble="Given the conversation between a user and a helpful assistant and some search results, create a final answer for the assistant. Always respond back to the user in the same language as the user. The answer should use all relevant information from the search results, not introduce any additional information, and use exactly the same words as the search results when possible. The assistant's answer should be formatted as a bulleted list. Each list item should start with the \"-\" symbol.")
answer_generation_spec = discoveryengine_v1.AnswerQueryRequest.AnswerGenerationSpec(model_spec=model_spec1,prompt_spec=prompt_spec1,include_citations=True,ignore_low_relevant_content=True)

request = discoveryengine_v1.AnswerQueryRequest(
    query=query,
    session=session1,
    serving_config= f"projects/{project_id}/locations/{location}/collections/default_collection/dataStores/{data_store_id}/servingConfigs/default_serving_config",
    query_understanding_spec = query_understand_spec1,answer_generation_spec=answer_generation_spec
)


response = client.answer_query(request=request)
print(response.answer.answer_text)

