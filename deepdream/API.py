from flask import Flask, request, Response
from flask_oidc_ext import OpenIDConnect
import os
from werkzeug.utils import secure_filename

from tasks import INPUT_FOLDER, dream_and_email, guided_dream_and_email

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = INPUT_FOLDER
app.secret_key = os.environ.get("FLASK_SECRET_KEY", os.urandom(16))
app.config["OIDC_CLIENT_SECRETS"] = os.environ.get("DEEPDREAM_OIDC_CLIENT_SECRETS_FILE", None)
oidc = OpenIDConnect(app)

ALLOWED_EXTENSIONS = [".jpg", ".jpeg", ".png"]


def allowed_file(filename):
    return os.path.splitext(filename)[1] in ALLOWED_EXTENSIONS


@app.route("/health/")
def health():
    return Response(response="ok", status=200)


@app.route("/upload/", methods=["GET", "POST"])
@oidc.require_login
def upload_page():
    if request.method == "GET":
        with open("html/form.html") as html_file:
            html = html_file.read()
        return html

    elif request.method == "POST":
        user_email_to = request.form["address"]
        user_end_layer = request.form["layer"]
        user_width = int(request.form["width"])
        user_input_file = request.files["input_file"]
        user_guide_file = request.files["guide_file"]

        if user_width > 1000:
            user_width = 1000

        if user_input_file and allowed_file(user_input_file.filename) and not user_guide_file:
            file_path = os.path.join(INPUT_FOLDER, secure_filename(user_input_file.filename))

            with open(file_path, "w") as fp:
                user_input_file.save(fp)

            dream_and_email.delay(file_path, user_end_layer, user_width, user_email_to)

            with open("html/success.html") as html_file:
                html = html_file.read().format(user_email_to)
        elif user_input_file and allowed_file(user_input_file.filename) and user_guide_file and allowed_file(user_guide_file.filename):
            input_file_path = os.path.join(INPUT_FOLDER, secure_filename(user_input_file.filename))
            guide_file_path = os.path.join(INPUT_FOLDER, secure_filename(user_guide_file.filename))

            with open(input_file_path, "w") as fp:
                user_input_file.save(fp)
            with open(guide_file_path, "w") as fp:
                user_guide_file.save(fp)

            guided_dream_and_email.delay(input_file_path, guide_file_path, user_end_layer, user_width, user_email_to)

            with open("html/success.html") as html_file:
                html = html_file.read().format(user_email_to)
        else:
            with open("html/fail.html") as html_file:
                html = html_file.read().format(" | ".join(ALLOWED_EXTENSIONS))

        return html
