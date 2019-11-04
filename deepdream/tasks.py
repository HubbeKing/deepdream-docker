from celery import Celery
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import smtplib

from deepdream import dream_about

GMAIL_USER = os.environ.get("GMAIL_USER")
GMAIL_PASS = os.environ.get("GMAIL_PASS")
INPUT_FOLDER = "/opt/deepdream/inputs/"
OUTPUT_FOLDER = "/opt/deepdream/outputs/"

RABBIT_MQ_CONFIG = {
    "user": os.environ.get("RABBITMQ_DEFAULT_USER"),
    "pass": os.environ.get("RABBITMQ_DEFAULT_PASS"),
    "vhost": os.environ.get("RABBITMQ_DEFAULT_VHOST")
}

app = Celery('tasks', broker='pyamqp://{user}:{pass}@queue:5672/{vhost}'.format(**RABBIT_MQ_CONFIG))


@app.task
def dream_and_email(input_file_path, output_layer_name, maximum_image_width, to_email):
    deepdream = dream(input_file_path, output_layer_name, maximum_image_width)
    if deepdream:
        output_file_name = "/opt/deepdream/outputs/{}".format(os.path.basename(input_file_path))
        mail(to_email, output_file_name)
        print "Successfully dreamed about {} and emailed.".format(input_file_path)
    else:
        print "Failed to dream about {}".format(input_file_path)


def dream(input_file_path, output_layer_name, maximum_image_width):
    """
    Synchronous call to dream_about, takes several minutes (at least)
    """
    print "Dreaming about {}".format(input_file_path)
    print "Dreaming to layer {}".format(output_layer_name)
    print "Max-width is {}".format(maximum_image_width)
    dream_about(input_file_path, output_layer_name, maximum_image_width, OUTPUT_FOLDER)
    return os.path.exists(os.path.join(OUTPUT_FOLDER, os.path.basename(input_file_path)))


def mail(address, attachment_path):
    print "Emailing {} to {}".format(attachment_path, address)
    msg = MIMEMultipart()

    msg["From"] = GMAIL_USER
    msg["To"] = address
    msg["Subject"] = "Photo from Deep Dream"

    msg.attach(MIMEText("Please find attached photo"))

    with open(attachment_path, "rb") as attachment:
        img = MIMEImage(attachment.read())
    img["Content-Disposition"] = 'attachment; filename="{}"'.format(os.path.basename(attachment_path))
    msg.attach(img)

    mail_server = smtplib.SMTP("smtp.gmail.com", 587)
    mail_server.ehlo()
    mail_server.starttls()
    mail_server.ehlo()
    mail_server.login(GMAIL_USER, GMAIL_PASS)
    mail_server.sendmail(GMAIL_USER, [address], msg.as_string())
    mail_server.close()
