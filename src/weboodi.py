import requests
import os
import bs4
import datetime
from icalendar import Calendar, Event, vText
import pytz

BASE_URL = "https://oodi.aalto.fi"


class InvalidCredentials(Exception):
    pass


class WebOodi:
    def __init__(self) -> None:
        self.session = requests.Session()

    def login(self, username: str, password: str) -> None:
        r = self.session.get(BASE_URL + "/a/etusivu.html")
        r.raise_for_status()

        r = self.session.get(
            BASE_URL
            + "/a/jsp/oodihaka.jsp?return=https%3A%2F%2Foodi.aalto.fi%2Fa%2Fetusivu.html"
        )
        r.raise_for_status()

        r = self.session.post(
            "https://idp.aalto.fi/idp/profile/SAML2/Redirect/SSO?execution=e1s1",
            data={
                "j_username": username,
                "j_password": password,
                "_eventId_proceed": "",
            },
        )
        r.raise_for_status()

        if "The password you entered was incorrect." in r.text:
            raise InvalidCredentials()

        soup = bs4.BeautifulSoup(r.text, "lxml")
        form = soup.find("form")
        data = {
            e.attrs["name"]: e.attrs["value"]
            for e in form.find_all("input")
            if "name" in e.attrs
        }

        r = self.session.post(form.attrs["action"], data=data)
        r.raise_for_status()

    def get_exam_time_and_place(self, path: str) -> Event:
        r = self.session.get(BASE_URL + path)
        r.raise_for_status()

        soup = bs4.BeautifulSoup(r.text, "lxml")
        td = soup.find_all("td", class_="OK_OT")[-1]
        tc = [c.strip() for c in td.children if isinstance(c, str)]

        description = soup.find_all("td", class_="OK_OT")[8].find("td").text.strip()

        location = [
            inp.attrs["value"]
            for inp in td.find_all("input")
            if inp.attrs["name"] == "LINKOPETPAIK_1"
        ][0]
        location = " ".join(location.split())

        day, month, year2 = map(int, tc[0].strip().split("."))
        date = datetime.date(day=day, month=month, year=year2 + 2000)

        timerange = [
            datetime.time(**dict(zip(["hour", "minute"], map(int, t.split(".")))))
            for t in tc[1].split()[1].split("-")
        ]

        start = datetime.datetime.combine(
            date, timerange[0], tzinfo=pytz.timezone("Europe/Helsinki")
        )
        end = datetime.datetime.combine(
            date, timerange[1], tzinfo=pytz.timezone("Europe/Helsinki")
        )

        event = Event()
        event.add("summary", "EXAM: " + description)
        event.add("dtstart", start)
        event.add("dtend", end)
        event["location"] = vText(location)

        return event

    def get_exams_cal(self) -> Calendar:
        r = self.session.get(BASE_URL + "/a/omatopinn.jsp?NaytIlm=1&Kieli=6")
        r.raise_for_status()

        calendar = Calendar()

        soup = bs4.BeautifulSoup(r.text, "lxml")
        table = soup.find("table").find("table")
        header = [t.text.strip() for t in table.find_all("th")]
        for row in table.find_all("tr"):
            row = dict(zip(header, row.find_all("td")))
            if not row:
                continue
            if row["Type"].text.strip() == "Examination":
                event = self.get_exam_time_and_place(
                    row["Study module"].find("a").attrs["href"]
                )
                calendar.add_component(event)

        return calendar
