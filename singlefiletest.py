import datetime
import json
import logging
import os
from time import sleep

from autologging import logged, traced, TRACE
import dotenv
import requests
import webuntis

def send_telegram(message: str):
    req_resp = requests.post(
    url='https://api.telegram.org/bot{0}/{1}'.format(os.getenv("TELEGRAM_API_TOKEN"), 'sendMessage'),
    data={'chat_id': os.getenv("CHAT_ID"), 'text': message}
    ).json()

    if req_resp['ok']:
        logging.log(level=logging.INFO, msg="Message sent to telegram")
    else:
        logging.log(level=logging.ERROR, msg="Message not sent to telegram")
        logging.log(level=logging.ERROR, msg="Error message: " + str(req_resp['description']))


class UntisSess():
    def __init__(self) -> None:
        self.s = webuntis.Session(
            username=os.getenv("USER"),
            password=os.getenv("PASSWORD"),
            server=os.getenv("URL"),
            school=os.getenv("SCHOOL"),
            useragent=os.getenv("USERAGENT")
        ).login()

        self.klasse = int(os.getenv("CLASS_ID")) # type: ignore

    def get_subjects(self):
        subjects = self.s.subjects()
        with open("subjects.json", "w") as file:
            file.write("{\n")
            for lesson in subjects:
                file.write(f'   "{lesson.id}": "{lesson.name}",\n')
        with open("subjects.json", "r") as f:
            read_data = f.read()
        with open("subjects.json", "w") as f:
            f.write(read_data[:-2] + "\n}")

    def get_timetable(self, when):
        written = []
        if when == "today":
            timetable = self.s.timetable(klasse=self.klasse, start=datetime.date.today(), end=datetime.date.today()+ datetime.timedelta(4))
            with open("timetable.json", "w") as f:
                    f.write("{\n")
                    for j, i in enumerate(timetable): # type: ignore
                        if i.code == "cancelled":
                            if j not in written:
                                f.write(f'  "{j}":'+str(i).replace("'",'"')+",\n")
                                written.append(j)
            if len(written) == 0:
                open("timetable.json", "a").write("}")
            else:
                with open("timetable.json", "r") as f:
                    read_data = f.read()
                with open("timetable.json", "w") as f:
                    f.write(read_data[:-2] + "\n}")

        elif when == "tomorrow":
            timetable = self.s.timetable(klasse=self.klasse, start=datetime.date.today()+datetime.timedelta(1), end=datetime.date.today()+datetime.timedelta(1))
            with open("timetable.json", "w") as f:
                    f.write("{\n")
                    for j, i in enumerate(timetable): # type: ignore
                        if i.code == "cancelled":
                            if j not in written:
                                f.write(f'  "{j}":'+str(i).replace("'",'"')+",\n")
                                written.append(j)

            with open("timetable.json", "r") as f:
                read_data = f.read()
            with open("timetable.json", "w") as f:
                f.write(read_data[:-2] + "\n}")


    def logout(self):
        self.s.logout()
    def login(self):
        self.s.login()

def create_message():
    weekdays = { 0: "Montag", 1: "Dienstag", 2: "Mittwoch", 3: "Donnerstag", 4: "Freitag", 5: "Samstag", 6: "Sonntag"}
    ausfall = "Heute entfallen folgende Stunden:\n"
    with open("timetable.json", "r") as file:
        timetable = json.load(file)
    with open("subjects.json", "r") as file:
        subjects = json.load(file)
    with open("teachers.json", "r") as file:
        teachers = json.load(file)
    for lesson in timetable:
        lessonname = subjects[lesson['su']['id']]
        date = datetime.datetime.strptime(lesson['date'], '%Y%m%d')
        ausfall += f"{lessonname} bei {teachers[lessonname]} am {weekdays[date.weekday]}, dem {date.strftime('%d%m')}\n"

    if ausfall == "Heute entfallen folgende Stunden:\n":
        ausfall += "Keine"

    return ausfall


def waittimedefine():
    now = datetime.datetime.now()
    if now.hour < 7:
        return 60 * 60 * (7 - now.hour)
    elif now.hour > 17:
        return 60 * 60 * (24 - now.hour + 7)
    else:
        return 60 * 60 * 2

def main():
    # obgligated initialisations
    sess = UntisSess()
    sess.get_subjects()
    while True:
        sess.get_timetable("today")
        sess.logout()
        send_telegram(create_message())
        sleep(waittimedefine())

if __name__ == "__main__":
    dotenv.load_dotenv()
    logging.basicConfig(filename='untis_ms.log', filemode="a", level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    main()