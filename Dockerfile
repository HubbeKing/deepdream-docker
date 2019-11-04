FROM bvlc/caffe:cpu

# Download caffe model binary
RUN /opt/caffe/scripts/download_model_binary.py /opt/caffe/models/bvlc_googlenet

# Copy in deepdream API and worker requirements and install
COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

# install gunicorn
RUN pip install gunicorn

# make a non-priviledged user for running the API and celery workers
RUN groupadd --gid 1000 dreamer
RUN useradd --uid 1000 --gid 1000 dreamer

USER dreamer

WORKDIR /opt/deepdream

# Start API by default
CMD ["gunicorn", "--bind=0.0.0.0:8000","--workers=4", "API:app"]
