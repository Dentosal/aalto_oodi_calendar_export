from .crypt import encrypt, decrypt
from .weboodi import WebOodi, InvalidCredentials
from flask import Flask, Response, request, render_template
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from os import environ
import json

URL_CRYPT_KEY = environ["CRYPT_KEY"]

app = Flask(__name__)
limiter = Limiter(app, key_func=get_remote_address, default_limits=["100/minute"])


@app.route("/", methods=["GET"])
@limiter.exempt
def index():
    return render_template("index.html")


@app.route("/", methods=["POST"])
@limiter.limit("5/minute")
def index_post():
    t_error = None
    t_url = None

    un = request.form.get("username")
    pw = request.form.get("password")
    if un and pw:
        oodi = WebOodi()
        try:
            oodi.login(un, pw)
        except InvalidCredentials:
            t_error = "Invalid Credentials"
        else:
            url_param = encrypt(
                json.dumps({"username": un, "password": pw}).encode(), URL_CRYPT_KEY
            )
            t_url = request.host_url + "cal?auth=" + url_param

    return render_template("index.html", error=t_error, url=t_url)


@app.route("/cal", methods=["GET"])
@limiter.limit("2/minute")
def exams_ical():
    auth = request.args.get("auth")
    if not auth:
        return "Authentocation missing", 403

    data = json.loads(decrypt(auth, URL_CRYPT_KEY))

    un = data["username"]
    pw = data["password"]

    oodi = WebOodi()
    try:
        oodi.login(un, pw)
    except InvalidCredentials:
        return "Invalid Credentials", 403

    cal_bytes = oodi.get_exams_cal().to_ical()
    return Response(cal_bytes, mimetype="text/calendar")


@app.errorhandler(429)
def ratelimit_handler(e):
    return (
        '<h1>Rate limit exceeded</h1> <a href="/">Back to frontpage</a><hr/>' + str(e),
        429,
    )


if __name__ == "__main__":
    app.run(debug=True)
