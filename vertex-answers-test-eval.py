from google.cloud import discoveryengine_v1beta as discoveryengine_v1
from google.api_core.client_options import ClientOptions
from dotenv import load_dotenv
load_dotenv()
import os
import requests
from google.auth import default
from google.auth.transport.requests import Request
import pandas as pd
import time
from typing import List, Optional, Tuple

df = pd.read_csv("~/Downloads/OTI-Complete.csv")
queries = df["Query"]

df["Answers API"] = None
df["API Call Time (s)"] = None


# Get the access token from gcloud (assumes gcloud is installed)
project_id = os.environ["project_id"]
location = os.environ["location"]  # Values: "global", "us", "eu"
data_store_id = os.environ["data_store_id"]


def add_references_answers(citations: List,response):
    textref = f"\n References:"
    textlinks = []
    for i, citation in enumerate(citations):
        citindex = int(citation.sources[0].reference_id)
        url = response.answer.references[citindex].chunk_info.document_metadata.uri
        title = response.answer.references[citindex].chunk_info.document_metadata.title
        if not any(url in link for link in textlinks):
            textlinks.append(f"\n [{title}]({url})")
    text1 = textref + "".join(textlinks)
    return text1



client_options = (
    ClientOptions(api_endpoint="discoveryengine.googleapis.com")
)
client = discoveryengine_v1.ConversationalSearchServiceClient(client_options=client_options)
query = discoveryengine_v1.Query()
for index, row in df.iterrows():
    query.text = row["Query"]
    query_rephraser_spec1 = discoveryengine_v1.AnswerQueryRequest.QueryUnderstandingSpec.QueryRephraserSpec(disable=True)
    query_understand_spec1 = discoveryengine_v1.AnswerQueryRequest.QueryUnderstandingSpec(query_rephraser_spec=query_rephraser_spec1)
    model_spec1 = discoveryengine_v1.AnswerQueryRequest.AnswerGenerationSpec.ModelSpec(model_version="gemini-1.5-flash-001/answer_gen/v1",)
    prompt_spec1 = discoveryengine_v1.AnswerQueryRequest.AnswerGenerationSpec.PromptSpec(preamble="Given the conversation between a user and a helpful assistant and some search results, create a final answer for the assistant. Always respond back to the user in the same language as the user. The answer should use all relevant information from the search results, not introduce any additional information, and use exactly the same words as the search results when possible. The assistant's answer should be formatted as a bulleted list.")
    related_question_spec = discoveryengine_v1.AnswerQueryRequest.RelatedQuestionsSpec(enable=True)
    answer_generation_spec = discoveryengine_v1.AnswerQueryRequest.AnswerGenerationSpec(model_spec=model_spec1,prompt_spec=prompt_spec1,include_citations=True,ignore_low_relevant_content=True)
    request = discoveryengine_v1.AnswerQueryRequest(
            query=query,
            serving_config= f"projects/{project_id}/locations/{location}/collections/default_collection/dataStores/{data_store_id}/servingConfigs/default_serving_config",
            query_understanding_spec = query_understand_spec1,answer_generation_spec=answer_generation_spec,related_questions_spec=related_question_spec
        )
    start_time = time.monotonic()
    try:
        response = client.answer_query(request=request)
    except:
        print("errored out - sleeping now")
        time.sleep(500)
        start_time = time.monotonic()
        try:
            response = client.answer_query(request=request)
        except:
            df.to_csv("output_complete.csv", index=False)
    end_time = time.monotonic()
    elapsed_time = end_time - start_time
    references = f"{add_references_answers(response.answer.citations,response)}"
    df.at[index,"Answers API"] = response.answer.answer_text
    df.at[index, "API Call Time (s)"] = elapsed_time
    df.at[index, "References"] = references
    print(response.answer.answer_text)
    print(f"Completed processing {index}")
df.to_csv("output_complete.csv", index=False)



