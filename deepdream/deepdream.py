import caffe
from google.protobuf import text_format
import numpy as np
import os
import PIL.Image
import scipy.ndimage as nd


def preprocess(net, img):
    return np.float32(np.rollaxis(img, 2)[::-1]) - net.transformer.mean["data"]


def deprocess(net, img):
    return np.dstack((img + net.transformer.mean["data"])[::-1])


def objective_L2(dst):
    dst.diff[:] = dst.data


def make_step(net, step_size=1.5, end="inception_4c/output", jitter=32, clip=True, objective=objective_L2):
    """Basic gradient ascent step."""

    src = net.blobs['data']  # input image is stored in Net's 'data' blob
    dst = net.blobs[end]

    ox, oy = np.random.randint(-jitter, jitter + 1, 2)
    src.data[0] = np.roll(np.roll(src.data[0], ox, -1), oy, -2)  # apply jitter shift

    net.forward(end=end)
    objective(dst)  # specify the optimization objective
    net.backward(start=end)
    g = src.diff[0]
    # apply normalized ascent step to the input image
    src.data[:] += step_size / np.abs(g).mean() * g

    src.data[0] = np.roll(np.roll(src.data[0], -ox, -1), -oy, -2)  # un-shift image

    if clip:
        bias = net.transformer.mean['data']
        src.data[:] = np.clip(src.data, -bias, 255 - bias)


def deepdream(net, base_img, iter_n=10, octave_n=4, octave_scale=1.4, end='inception_4c/output', clip=True, **step_params):
    # prepare base images for all octaves
    octaves = [preprocess(net, base_img)]
    for i in xrange(octave_n - 1):
        octaves.append(nd.zoom(octaves[-1], (1, 1.0 / octave_scale, 1.0 / octave_scale), order=1))

    src = net.blobs['data']
    detail = np.zeros_like(octaves[-1])  # allocate image for network-produced details
    for octave, octave_base in enumerate(octaves[::-1]):
        h, w = octave_base.shape[-2:]
        if octave > 0:
            # upscale details from the previous octave
            h1, w1 = detail.shape[-2:]
            detail = nd.zoom(detail, (1, 1.0 * h / h1, 1.0 * w / w1), order=1)

        src.reshape(1, 3, h, w)  # resize the network's input image size
        src.data[0] = octave_base + detail
        for i in xrange(iter_n):
            make_step(net, end=end, clip=clip, **step_params)

        # extract details produced on the current octave
        detail = src.data[0] - octave_base
    # returning the resulting image
    return deprocess(net, src.data[0])


def dream_about(input_image_path, end_layer, width, output_folder):
    model_path = "/opt/caffe/models/bvlc_googlenet/"
    net_fn = os.path.join(model_path, "deploy.prototxt")
    param_fn = os.path.join(model_path, "bvlc_googlenet.caffemodel")

    # Patching model to be able to compute gradients.
    # Note that you can also manually add "force_backward: true" line to "deploy.prototxt".
    if not os.path.exists("tmp.prototxt"):
        model = caffe.io.caffe_pb2.NetParameter()
        with open(net_fn) as fp:
            text_format.Merge(fp.read(), model)
        model.force_backward = True
        with open("tmp.prototxt", "w") as fp:
            fp.write(str(model))

    net = caffe.Classifier("tmp.prototxt", param_fn,
                           mean=np.float32([104.0, 116.0, 122.0]),  # ImageNet mean, training set dependent
                           channel_swap=(2, 1, 0))  # the reference model has channels in BGR order instead of RGB

    # a couple of utility functions for converting to and from Caffe's input image layout

    img = PIL.Image.open(input_image_path)

    # if image exceeds maxwidth, scale using PIL.Image.ANTIALIAS
    if img.size[0] > width:
        wpercent = (width / float(img.size[0]))
        hsize = int((float(img.size[1]) * float(wpercent)))
        img = img.resize((width, hsize), PIL.Image.ANTIALIAS)

    # convert to numpy float32 and call actual deepdream function
    img = np.float32(img)
    frame = deepdream(net, img, end=end_layer)

    # save image to output path
    output_path = os.path.join(output_folder, os.path.basename(input_image_path))
    PIL.Image.fromarray(np.uint8(frame)).save(output_path)