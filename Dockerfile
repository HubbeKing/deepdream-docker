FROM docker.io/bvlc/caffe:cpu

# Download caffe model binary
RUN /opt/caffe/scripts/download_model_binary.py /opt/caffe/models/bvlc_googlenet

# install flask, celery, and uwsgi (API/worker requirements)
# what's needed for deepdream.py is already in the base image
RUN pip install "celery==4.4.7" "flask==1.1.2" "uwsgi==2.0.19.1"

# make a non-priviledged user for running the API and celery workers
RUN groupadd --gid 1000 dreamer
RUN useradd --uid 1000 --gid 1000 dreamer

WORKDIR /opt/deepdream
ADD ./* /opt/deepdream/

RUN chown -R dreamer:dreamer /opt/deepdream

USER dreamer

# Start API by default
CMD ["uwsgi", "--ini", "/opt/deepdream/uwsgi.ini"]
