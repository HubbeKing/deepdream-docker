from flask import Flask, request
import os
from werkzeug.utils import secure_filename

from tasks import INPUT_FOLDER, dream_and_email

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = INPUT_FOLDER

ALLOWED_EXTENSIONS = [".jpg", ".jpeg", ".png"]


def allowed_file(filename):
    return os.path.splitext(filename)[1] in ALLOWED_EXTENSIONS


@app.route("/upload/", methods=["GET", "POST"])
def upload_page():
    if request.method == "GET":
        with open("html/form.html") as html_file:
            html = html_file.read()
        return html

    elif request.method == "POST":
        user_email_to = request.form["address"]
        user_end_layer = request.form["layer"]
        user_width = int(request.form["width"])
        user_file = request.files["file"]

        if user_width > 1000:
            user_width = 1000

        if user_file and allowed_file(user_file.filename):
            file_path = os.path.join(INPUT_FOLDER, secure_filename(user_file.filename))

            with open(file_path, "w") as fp:
                user_file.save(fp)

            dream_and_email.delay(file_path, user_end_layer, user_width, user_email_to)

            with open("html/success.html") as html_file:
                html = html_file.read().format(user_email_to)
        else:
            with open("html/fail.html") as html_file:
                html = html_file.read().format(" | ".join(ALLOWED_EXTENSIONS))

        return html
