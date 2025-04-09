FROM python:3.11
RUN curl -sSL https://sdk.cloud.google.com | bash
ENV PATH $PATH:/root/google-cloud-sdk/bin

# Install build dependencies
RUN pip install --upgrade pip
RUN pip install wheel setuptools

COPY chainlit-with-vertex-basic.py app.py
COPY requirements.txt /tmp/
COPY chainlit.md chainlit.md

# Create .chainlit directory if it doesn't exist
RUN mkdir -p /.chainlit

# Install dependencies
RUN pip install --requirement /tmp/requirements.txt
RUN pip install google-cloud-discoveryengine
RUN pip install chainlit==1.0.401
#RUN pip install chainlit==1.1.301

CMD ["chainlit", "run", "app.py", "-h"]  # Include "-h" for production
