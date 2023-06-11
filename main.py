import datetime
import json
import logging
import os
from time import sleep

import dotenv
from requests import post
from webuntis.session import Session


class UntisSess():
    def __init__(self) -> None:
        self.s = Session(
            username=os.getenv("UNTIS_USER"),
            password=os.getenv("UNTIS_PASSWORD"),
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
            timetable = self.s.timetable(klasse=self.klasse, start=datetime.date.today(), end=datetime.date.today())
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

def create_message(when):
    weekdays = { 1: "Montag", 2: "Dienstag", 3: "Mittwoch", 4: "Donnerstag", 5: "Freitag", 6: "Samstag", 7: "Sonntag"}
    if datetime.datetime.now().isoweekday() == 5:
        return "Heute ist Freitag, es gibt keine Stunden mehr. Schönes Wochenende!"
    elif datetime.datetime.now().isoweekday() == 6:
        return "Heute ist Samstag, es gibt keine Stunden mehr. Schönes Wochenende!"
    elif when == "today":
        ausfall = "Heute entfallen folgende Stunden:\n"
    elif when == "tomorrow":
        ausfall = "Morgen entfallen folgende Stunden:\n"
    else:
        return "Error: Invalid argument"

    with open("timetable.json", "r") as file:
        timetable = json.load(file)
    with open("subjects.json", "r") as file:
        subjects = json.load(file)
    with open("teachers.json", "r") as file:
        teachers = json.load(file)
    for lesson in timetable:
        lessonname = subjects[str(timetable[lesson]['su'][0]['id'])]
        date = datetime.datetime.strptime(str(timetable[lesson]['date']), '%Y%m%d')
        ausfall += f"{lessonname} bei {teachers[lessonname]} am {weekdays[date.isoweekday()]}, dem {date.strftime('%d%m')}\n"

    if ausfall == "Heute entfallen folgende Stunden:\n":
        ausfall += "Keine"

    return ausfall

def send_telegram(message: str):
    req_resp = post(
    url='https://api.telegram.org/bot{0}/{1}'.format(os.getenv("TELEGRAM_API_TOKEN"), 'sendMessage'),
    data={'chat_id': os.getenv("CHAT_ID"), 'text': message}
    ).json()

    if req_resp['ok']:
        logging.log(level=logging.INFO, msg="Message sent to telegram")
    else:
        logging.log(level=logging.ERROR, msg="Message not sent to telegram")
        logging.log(level=logging.ERROR, msg="Error message: " + str(req_resp['description']))

def waittimedefine():
    current_time = datetime.datetime.now()
    target_time = None

    # Calculate target time for today
    if current_time.hour < 7 or (current_time.hour == 7 and current_time.minute < 10):
        target_time = current_time.replace(hour=7, minute=10, second=0, microsecond=0)
    elif current_time.hour < 20:
        target_time = current_time.replace(hour=20, minute=0, second=0, microsecond=0)
    else:
        # Calculate target time for tomorrow
        tomorrow = current_time + datetime.timedelta(days=1)
        target_time = tomorrow.replace(hour=7, minute=10, second=0, microsecond=0)

    wait_time = (target_time - current_time).total_seconds()
    return wait_time

def main():
    # obgligated initialisations
    sess = UntisSess()
    sess.get_subjects()
    while True:
        if datetime.datetime.now().hour == 7:
            sess.login()
            sess.get_timetable("today")
            sess.logout()
            message = create_message("today")
        else:
            sess.login()
            sess.get_timetable("tomorrow")
            sess.logout()
            message = create_message("tomorrow")

        send_telegram(message)
        waittime = waittimedefine()
        logging.log(level=logging.INFO, msg=f"Waiting {waittime} seconds")
        sleep(waittime)

if __name__ == "__main__":
    dotenv.load_dotenv()
    logging.basicConfig(filename='untis_ms.log', filemode="a", level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    main()
    
    
