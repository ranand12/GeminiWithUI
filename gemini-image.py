import vertexai
from vertexai.generative_models import GenerativeModel, Part, Image
import chainlit as cl
import base64
from pathlib import Path
import textwrap


project_id = ""

vertexai.init(project=project_id, location="us-central1")
model = GenerativeModel(model_name="gemini-1.5-pro-001")
chat = model.start_chat(history=[])

@cl.on_message
async def main(message: cl.Message):
    # cookie_picture = {
    #     'mime_type': 'image/png',
    #     'data': pathlib.Path('OTI-MyCity-Dev1/cookie.png').read_bytes()
    # }
    
    try:
        pdf_file_path = Path(message.elements[0].path)
        with open(pdf_file_path, "rb") as f:
            pdf_bytes = f.read()
            pdf_file = Part.from_data(pdf_bytes,mime_type= "application/pdf")
            prompt = message.content
            response = chat.send_message(content=[prompt, pdf_file])
        #await cl.Message(content=response.text).send()
        msg = cl.Message(content="")
        for token in response.text:
            await msg.stream_token(token)
        await msg.send()
    except:
        response = chat.send_message(content=[message.content])
        #await cl.Message(content=response.text).send()
        msg = cl.Message(content="")
        for token in response.text:
            await msg.stream_token(token)
        await msg.send()


if __name__ == "__main__":
    from chainlit.cli import run_chainlit
    run_chainlit(__file__)