from . import weboodi
from flask import Flask, Response

app = Flask(__name__)


@app.route("/exams_ical")
def exams_ical():
    cal_bytes = weboodi.get_exams_ical()
    return Response(cal_bytes, mimetype="text/calendar")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    app.run()
