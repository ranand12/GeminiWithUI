FROM python:3.11
RUN curl -sSL https://sdk.cloud.google.com | bash
ENV PATH $PATH:/root/google-cloud-sdk/bin
COPY vertexaisearch-withanswersui.py app.py
COPY requirements.txt /tmp/
RUN pip install --requirement /tmp/requirements.txt
RUN pip install google-cloud-discoveryengine
RUN pip install chainlit 
CMD ["chainlit", "run", "app.py", "-h"]  # Include "-h" for production


