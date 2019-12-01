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
    deepdream = dream(input_file_path, output_layer_name, maximum_image_width)
    if deepdream:
        output_file_name = os.path.join(OUTPUT_FOLDER, os.path.basename(input_file_path))
        mail(to_email, output_file_name)
        print "Successfully dreamed about {} and emailed.".format(input_file_path)
    else:
        print "Failed to dream about {}".format(input_file_path)


@app.task
def guided_dream_and_email(input_file_path, guide_file_path, output_layer_name, maximum_image_width, to_email):
    deepdream = guided_dream(input_file_path, guide_file_path, output_layer_name, maximum_image_width)
    if deepdream:
        output_file_name = os.path.join(OUTPUT_FOLDER, os.path.basename(input_file_path))
        mail(to_email, output_file_name)
        print "Successfully dreamed about {} and emailed.".format(input_file_path)
    else:
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
    Synchronous call to guided_dream, takes several minutes (at least)
    """
    start = time.time()
    print "Dreaming about {}".format(input_file_path)
    print "Using {} as a guide image".format(guide_file_path)
    print "Dreaming to layer {}".format(output_layer_name)
    print "Max-width is {}".format(maximum_image_width)
    guided_dream_about(input_file_path, guide_file_path, output_layer_name, maximum_image_width, OUTPUT_FOLDER)
    end = time.time()
    print "Dreaming took {} seconds".format(end-start)
    return os.path.exists(os.path.join(OUTPUT_FOLDER, os.path.basename(input_file_path)))


def mail(address, attachment_path):
    if address != "example@example.com":
        print "Emailing {} to {}".format(attachment_path, address)
        msg = MIMEMultipart()

        msg["From"] = EMAIL_USER
        msg["To"] = address
        msg["Subject"] = "Photo from Deep Dream"

        msg.attach(MIMEText("Please find attached photo"))

        with open(attachment_path, "rb") as attachment:
            img = MIMEImage(attachment.read())
        img["Content-Disposition"] = 'attachment; filename="{}"'.format(os.path.basename(attachment_path))
        msg.attach(img)

        mail_server = smtplib.SMTP(EMAIL_SMTP, EMAIL_PORT)
        mail_server.ehlo()
        mail_server.starttls()
        mail_server.ehlo()
        mail_server.login(EMAIL_USER, EMAIL_PASS)
        mail_server.sendmail(EMAIL_USER, [address], msg.as_string())
        mail_server.close()
