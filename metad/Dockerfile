FROM google/cloud-sdk

RUN apt-get update && apt-get install -y python-pip
RUN pip install --upgrade pip

RUN gcloud components update

RUN mkdir -p /app
WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY app /app

EXPOSE 5000
ENV PYTHONPATH=/google-cloud-sdk/lib
CMD ["python", "metadata-service.py"]
