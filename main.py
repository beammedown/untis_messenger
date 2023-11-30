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
        try:
            self.s = Session(
                username=os.getenv("UNTIS_USER"),
                password=os.getenv("UNTIS_PASSWORD"),
                server=os.getenv("URL"),
                school=os.getenv("SCHOOL"),
                useragent=os.getenv("USERAGENT")
            ).login()

            class_id = os.getenv("CLASS_ID")
            if class_id is not None:
                self.klasse = int(class_id)
            else:
                exit("Error: No class id specified | set in .env to continue | exiting...")

        except Exception as e:
            logging.log(level=logging.ERROR, msg="Error while logging in: " + str(e))


    def get_subjects(self):
        subjects = self.s.subjects()
        with open(file="subjects.json", mode="w", encoding='utf-8') as file:
            file.write("{\n")
            for lesson in subjects:
                file.write(f'   "{lesson.id}": "{lesson.name}",\n')
        with open("subjects.json", "r") as f:
            read_data = f.read()
        with open("subjects.json", "w") as f:
            f.write(read_data[:-2] + "\n}")

    def get_timetable(self, when: str):
        try:
            written = []
            if when == "today":
                timetable = self.s.timetable(klasse=self.klasse, start=datetime.date.today(), end=datetime.date.today())
                with open("timetable.json", "w") as f:
                        f.write("{\n")
                        f.write(f'  "expand": "{True if datetime.datetime.now().hour == 7 else False}",\n')
                        for j, i in enumerate(list(timetable)): # type: ignore
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
                        for j, i in enumerate(list(timetable)): # type: ignore
                            if i.code == "cancelled":
                                if j not in written:
                                    f.write(f'  "{j}":'+str(i).replace("'",'"')+",\n")
                                    written.append(j)

                if len(written) == 0:
                    with open("timetable.json", "a") as f:
                        f.write("}")
                else:
                    with open("timetable.json", "r") as f:
                        read_data = f.read()
                    with open("timetable.json", "w") as f:
                        f.write(read_data[:-2] + "\n}")

        except Exception as e:
            logging.log(level=logging.ERROR, msg="Error while getting timetable: " + str(e))

    def logout(self):
        try:
            self.s.logout()
        except Exception as e:
            logging.log(level=logging.ERROR, msg="Error while logging out: " + str(e))
            return "Error"

    def login(self):
        try:
            self.s.login()
        except Exception as e:
            logging.log(level=logging.ERROR, msg="Error while logging in: " + str(e))
            return "Error"

def create_message(when: str):
    hours = {750: "1.", 840: "2.", 940: "3.", 1030: "4.", 1130: "5.", 1220: "6.", 1335: "7.", 1415: "8.", 1505: "9.", 1545: "10.", 1625: "11.", 1705: "12."}
    weekdays = { 1: "Montag", 2: "Dienstag", 3: "Mittwoch", 4: "Donnerstag", 5: "Freitag", 6: "Samstag", 7: "Sonntag"}
    if datetime.datetime.now().isoweekday() == 5 and datetime.datetime.now().hour == 20:
        return "Heute ist Freitag, es gibt keine Stunden mehr. Schönes Wochenende!"
    elif datetime.datetime.now().isoweekday() == 6:
        return ""
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
        date = timetable[lesson]['startTime']
        ausfall += f"{lessonname} bei {teachers[lessonname]} in der {hours[date]} Stunde\n"

    if ausfall == "Heute entfallen folgende Stunden:\n" or ausfall == "Morgen entfallen folgende Stunden:\n":
        ausfall += "Keine"

    return ausfall

def create_message_extended(when: str) -> str:
    hours = {750: "1.", 840: "2.", 940: "3.", 1030: "4.", 1130: "5.", 1220: "6.", 1335: "7.", 1415: "8.", 1505: "9.", 1545: "10.", 1625: "11.", 1705: "12."}
    with open("timetable.json", "r") as file:
        timetable = json.load(file)
    with open("subjects.json", "r") as file:
        subjects = json.load(file)
    with open("teachers.json", "r") as file:
        teachers = json.load(file)
    with open("archive.json", "r") as file:
        archive = json.load(file)
    if timetable['expand'] == "True":
        if datetime.datetime.now().isoweekday() == 5 and datetime.datetime.now().hour == 20:
            return "Heute ist Freitag, es gibt keine Stunden mehr. Schönes Wochenende!"
        elif datetime.datetime.now().isoweekday() == 6:
            return ""
        elif when == "today":
            ausfall = "Heute entfallen folgende Stunden:\n"
        elif when == "tomorrow":
            ausfall = "Morgen entfallen folgende Stunden:\n"
        else:
            return "Error: Invalid argument"


    else:
        if datetime.datetime.now().isoweekday() == 5 and datetime.datetime.now().hour == 20:
            return "Heute ist Freitag, es gibt keine Stunden mehr. Schönes Wochenende!"
        elif datetime.datetime.now().isoweekday() == 6:
            return ""
        elif when == "today":
            ausfall = "Heute entfallen folgende Stunden:\n"
        elif when == "tomorrow":
            ausfall = "Morgen entfallen folgende Stunden:\n"
        else:
            return "Error: Invalid argument"

        with open("archive.json", "a") as file:
            for lesson in timetable:
                lessonname = subjects[str(timetable[lesson]['su'][0]['id'])]
                date = timetable[lesson]['startTime']
                ausfall += f"{lessonname} bei {teachers[lessonname]} in der {hours[date]} Stunde\n"
                archive.append()
        if ausfall == "Heute entfallen folgende Stunden:\n" or ausfall == "Morgen entfallen folgende Stunden:\n":
            ausfall += "Keine"

    return ausfall

def send_telegram(message: str):
    if message == "":
        logging.log(level=logging.INFO, msg="No message to send")
        return
    url = "https://api.telegram.org/bot"+os.getenv("TELEGRAM_API_TOKEN")+"/"+'sendMessage'
    req_resp = post(
    url='https://api.telegram.org/bot{0}/{1}'.format(os.getenv("TELEGRAM_API_TOKEN"), 'sendMessage'),
    data={'chat_id': os.getenv("CHAT_ID"), 'text': message},
    timeout=5
    ).json()

    if req_resp['ok']:
        logging.log(level=logging.INFO, msg="Message sent to telegram")
    else:
        logging.log(level=logging.ERROR, msg="Message not sent to telegram")
        logging.log(level=logging.ERROR, msg="Error message: " + str(req_resp['description']))

def waittimedefine() -> float:
    current_time = datetime.datetime.now()
    target_time = None

    # Check if current time is between 7 am and 8 am
    if current_time.hour >= 7 and current_time.hour < 8:
        target_time = current_time.replace(hour=20, minute=0, second=0, microsecond=0)
    elif current_time.hour < 20:
        target_time = current_time.replace(hour=20, minute=0, second=0, microsecond=0)
    else:
        # Calculate target time for tomorrow at 7 am
        tomorrow = current_time + datetime.timedelta(days=1)
        target_time = tomorrow.replace(hour=7, minute=0, second=0, microsecond=0)

    wait_time = (target_time - current_time).total_seconds()
    return wait_time

def send_ntfsh(message: str):
    if message == "":
        logging.log(level=logging.INFO, msg="No message to send")
        return
    
    url = os.getenv("NTFY_URL")
    if url is not None:
        req_resp = post(
            url=url,
            json=message,
            timeout=5,
        )
        try:
            if req_resp.status_code == 200:
                logging.log(level=logging.INFO, msg="Message sent to ntfs.h")
            else:
                logging.log(level=logging.ERROR, msg="Message not sent to ntfs.h")
                logging.log(level=logging.ERROR, msg="Error message: " + str(req_resp.json()['error']))
        except:
            logging.log(level=logging.ERROR, msg="Message not sent to ntfs.h")
            logging.log(level=logging.ERROR, msg="Error message: " + str(req_resp.json()['error']))
    else:
        logging.log(level=logging.ERROR, msg="Error while sending message to ntfs.h: No URL specified")
        return


def do_send(sess: UntisSess, when: str):
    l = sess.login()
    if l == "Error":
        logging.log(level=logging.ERROR, msg="Error while logging in")
        sleep(60)
        return
    sess.get_timetable(when)
    sess.logout()
    message = create_message(when)

    send_ntfsh(message)

def do_extension(sess, when):
    l = None
    for _i in range(3):
        l = sess.login()
        if l == "Error":
            logging.log(level=logging.ERROR, msg="Error while logging in")
            sleep(60)
            continue
        else:
            break

    if l == "Error" or l is None:
        logging.log(level=logging.ERROR, msg=f"Error while logging in. Value of l = {l}")
        return
    sess.get_timetable(when)
    sess.logout()
    message = create_message_extended(when)
    send_telegram(message)

def main():
    """The main function
    """
    reqenvvars = ["UNTIS_USER", "UNTIS_PASSWORD", "SCHOOL", "CLASS_ID", "URL", "USERAGENT", "NTFY_URL"]
    for i in reqenvvars:
        if i not in os.environ:
            logging.log(level=logging.ERROR, msg=f"Environment variable {i} not set")
            exit(f"Environment variable {i} not set")

    # obgligated initialisations
    sess = UntisSess()
    sess.get_subjects()

    while True:
        now = datetime.datetime.now()

        if now.isoweekday() == 6 or (now.isoweekday() == 7 and now.hour < 19):
            pass

        elif now.isoweekday() == 7 and now.hour > 20:
            do_send(sess, "tomorrow")

        elif now.hour == 7:
            do_extension(sess, "today")

        else:
            do_send(sess, "tomorrow")

        waittime = waittimedefine()
        logging.log(level=logging.INFO, msg=f"Waiting {waittime} seconds")
        sleep(waittime)

if __name__ == "__main__":
    dotenv.load_dotenv()
    logging.basicConfig(filename='untis_ms.log', filemode="a", level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    main()
