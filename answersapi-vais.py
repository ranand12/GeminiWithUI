from google.cloud import discoveryengine_v1beta as discoveryengine_v1
from google.api_core.client_options import ClientOptions
from dotenv import load_dotenv
load_dotenv()
import os

# Get the access token from gcloud (assumes gcloud is installed)
project_id = os.environ["project_id"]
location = os.environ["location"]  # Values: "global", "us", "eu"
data_store_id = os.environ["data_store_id"]

client_options = (
    ClientOptions(api_endpoint="discoveryengine.googleapis.com")
)

# Create a client
client = discoveryengine_v1.ConversationalSearchServiceClient(client_options=client_options)


# Initialize request argument(s)



query = discoveryengine_v1.Query()
query.text = "how to open a juice bar"


request = discoveryengine_v1.AnswerQueryRequest(
    query=query,
    #session="projects/{project_id}/locations/global/collections/default_collection/dataStores/{data_store_id}/sessions/{session_id}",
    serving_config= f"projects/{project_id}/locations/{location}/collections/default_collection/dataStores/{data_store_id}/servingConfigs/default_serving_config"
)


response = client.answer_query(request=request)
print(response)

