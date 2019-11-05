# deepdream-docker
Simple deepdreaming docker-compose stack based on bvlc/caffe:cpu, flask, and celery

Meant to provide easy-to-setup deepdreaming and guided deepdreaming as a web service.
Accepts images to dream about in a web form, using a simple flask service running on gunicorn.
Deepdreams are ran using the Celery framework, for asynchronus dreaming of up to X images at once, where X is the number of processors on the host system
Result images from deepdreams are sent out via email, using gmail SMTP servers.

## Setup
- Get yourself a gmail to use for emailing out results
- Make an `.env` file based on [template.env](./template.env)
  - RabbitMQ credentials can be whatever you like, but if you for some reason have this externally accessible, it's better to have good passwords
- Run `docker-compose up -d`
- Point your browser at http://localhost:8000/upload
  - Alternatively, point a reverse proxy at it (nginx, apache, HAProxy)
