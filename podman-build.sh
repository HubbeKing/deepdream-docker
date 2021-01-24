#!/bin/bash
sudo podman run --rm --privileged=true --env STORAGE_DRIVER=vfs --volume /home/hubbe/Projects/deepdream-docker/:/src:O quay.io/buildah/stable:latest buildah bud --tag test src
