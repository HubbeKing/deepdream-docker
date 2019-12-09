FROM bvlc/caffe:cpu

# Download caffe model binary
RUN /opt/caffe/scripts/download_model_binary.py /opt/caffe/models/bvlc_googlenet

# install flask, celery, and gunicorn (API/worker requirements)
# what's needed for deepdream.py is already in the base image
RUN pip install celery flask gunicorn

# make a non-priviledged user for running the API and celery workers
RUN groupadd --gid 1000 dreamer
RUN useradd --uid 1000 --gid 1000 dreamer

WORKDIR /opt/deepdream
ADD ./* /opt/deepdream/

RUN chown -R dreamer:dreamer /opt/deepdream

USER dreamer

# Start API by default
CMD ["gunicorn", "--bind=0.0.0.0:8000","--workers=4", "API:app"]
