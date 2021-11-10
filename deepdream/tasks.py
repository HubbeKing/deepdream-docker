from celery import Celery
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import smtplib
import time

from deepdream import dream_about, guided_dream_about

EMAIL_SMTP = os.environ.get("EMAIL_SMTP")
EMAIL_PORT = os.environ.get("EMAIL_PORT")
EMAIL_SENDER = os.environ.get("EMAIL_SENDER")
EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASS = os.environ.get("EMAIL_PASS")

INPUT_FOLDER = "/opt/deepdream/inputs/"
OUTPUT_FOLDER = "/opt/deepdream/outputs/"

RABBIT_MQ_CONFIG = {
    "host": os.environ.get("RABBITMQ_HOST"),
    "port": os.environ.get("RABBITMQ_PORT"),
    "user": os.environ.get("RABBITMQ_DEFAULT_USER"),
    "pass": os.environ.get("RABBITMQ_DEFAULT_PASS"),
    "vhost": os.environ.get("RABBITMQ_DEFAULT_VHOST")
}

app = Celery('tasks', broker='pyamqp://{user}:{pass}@{host}:{port}/{vhost}'.format(**RABBIT_MQ_CONFIG))


@app.task
def dream_and_email(input_file_path, output_layer_name, maximum_image_width, to_email):
    try:
        deepdream = dream(input_file_path, output_layer_name, maximum_image_width)
    except Exception:
        failure(to_email, input_file_path)
        print "Failed to dream about {}".format(input_file_path)
    else:
        if deepdream:
            output_file_name = os.path.join(OUTPUT_FOLDER, os.path.basename(input_file_path))
            success(to_email, output_file_name)
            print "Successfully dreamed about {} and emailed.".format(input_file_path)
        else:
            failure(to_email, input_file_path)
            print "Failed to dream about {}".format(input_file_path)


@app.task
def guided_dream_and_email(input_file_path, guide_file_path, output_layer_name, maximum_image_width, to_email):
    try:
        deepdream = guided_dream(input_file_path, guide_file_path, output_layer_name, maximum_image_width)
    except Exception:
        failure(to_email, input_file_path)
        print "Failed to dream about {}".format(input_file_path)
    else:
        if deepdream:
            output_file_name = os.path.join(OUTPUT_FOLDER, os.path.basename(input_file_path))
            success(to_email, output_file_name)
            print "Successfully dreamed about {} and emailed.".format(input_file_path)
        else:
            failure(to_email, input_file_path)
            print "Failed to dream about {}".format(input_file_path)


def dream(input_file_path, output_layer_name, maximum_image_width):
    """
    Synchronous call to dream_about, takes several minutes (at least)
    """
    start = time.time()
    print "Dreaming about {}".format(input_file_path)
    print "Dreaming to layer {}".format(output_layer_name)
    print "Max-width is {}".format(maximum_image_width)
    dream_about(input_file_path, output_layer_name, maximum_image_width, OUTPUT_FOLDER)
    end = time.time()
    print "Dreaming took {} seconds".format(end-start)
    return os.path.exists(os.path.join(OUTPUT_FOLDER, os.path.basename(input_file_path)))


def guided_dream(input_file_path, guide_file_path, output_layer_name, maximum_image_width):
    """
    Synchronous call to guided_dream_about, takes several minutes (at least)
    """
    start = time.time()
    print "Dreaming about {}".format(input_file_path)
    print "Using {} as a guide image".format(guide_file_path)
    print "Dreaming to layer {}".format(output_layer_name)
    print "Max-width is {}".format(maximum_image_width)
    guided_dream_about(input_file_path, guide_file_path, output_layer_name, maximum_image_width, OUTPUT_FOLDER)
    end = time.time()
    print "Guided dreaming took {} seconds".format(end-start)
    return os.path.exists(os.path.join(OUTPUT_FOLDER, os.path.basename(input_file_path)))


def failure(address, attachment_path):
    print "Emailing about failure to {}".format(address)
    msg = MIMEMultipart()

    msg["From"] = EMAIL_SENDER
    msg["To"] = address
    msg["Subject"] = "Deep Dream Failure"

    msg.attach(MIMEText("Unfortunately, deepdreaming failed for your image {}.".format(os.path.basename(attachment_path))))

    send_mail(address, msg)


def success(address, attachment_path):
    print "Emailing {} to {}".format(attachment_path, address)
    msg = MIMEMultipart()

    msg["From"] = EMAIL_SENDER
    msg["To"] = address
    msg["Subject"] = "Deep Dream Success"

    msg.attach(MIMEText("Deepdreaming was successful! Please see attached image."))

    with open(attachment_path, "rb") as attachment:
        img = MIMEImage(attachment.read())
    img["Content-Disposition"] = 'attachment; filename="{}"'.format(os.path.basename(attachment_path))
    msg.attach(img)

    send_mail(address, msg)


def send_mail(address, mail):
    mail_server = smtplib.SMTP(EMAIL_SMTP, EMAIL_PORT)
    mail_server.ehlo()
    mail_server.starttls()
    mail_server.ehlo()
    mail_server.login(EMAIL_USER, EMAIL_PASS)
    mail_server.sendmail(EMAIL_USER, [address], mail.as_string())
    mail_server.close()
