import datetime
import json
import logging
import os
from time import sleep

import dotenv
from requests import post, get
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

            if os.getenv("CLASS_ID") != None:
                self.klasse = int(os.getenv("CLASS_ID")) # type: ignore
            else:
                exit("Error: No class id specified | set in .env to continue | exiting...")

        except Exception as e:
            logging.log(level=logging.ERROR, msg="Error while logging in: " + str(e))


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
        try:
            written = []
            if when == "today":
                timetable = self.s.timetable(klasse=self.klasse, start=datetime.date.today(), end=datetime.date.today())
                with open(f"{datetime.date.today()}.json", "w") as f:
                        f.write("{\n")
                        f.write(f'  "expand": "{True if datetime.datetime.now().hour == 7 else False}",\n')
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
                with open(f"{datetime.date.today() + datetime.timedelta(days=1)}.json", "w") as f:
                        f.write("{\n")
                        for j, i in enumerate(timetable): # type: ignore
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

def create_message():
    hours = {750: "1.", 840: "2.", 940: "3.", 1030: "4.", 1130: "5.", 1220: "6.", 1335: "7.", 1415: "8.", 1505: "9.", 1545: "10.", 1625: "11.", 1705: "12."}
    if datetime.datetime.now().isoweekday() == 5 and datetime.datetime.now().hour == 20:
        return "Heute ist Freitag, es gibt keine Stunden mehr. Schönes Wochenende!"
    elif datetime.datetime.now().isoweekday() == 6:
        return ""
    else:
        ausfall = "Morgen entfallen folgende Stunden:\n"

    with open(f"{datetime.date.today() + datetime.timedelta(days=1)}.json", "r") as file:
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


def create_message_extended():
    hours = {750: "1.", 840: "2.", 940: "3.", 1030: "4.", 1130: "5.", 1220: "6.", 1335: "7.", 1415: "8.", 1505: "9.", 1545: "10.", 1625: "11.", 1705: "12."}
    ausfall = "Heute entfallen folgende Stunden:\n"
    try:
        with open(f"{datetime.date.today()}.json", "r") as file:
            timetable = json.load(file)
    except FileNotFoundError:
        return "Keine Stunden entfallen"

    with open("subjects.json", "r") as file:
        subjects = json.load(file)

    with open("teachers.json", "r") as file:
        teachers = json.load(file)

    for lesson in timetable:
        lessonname = subjects[str(timetable[lesson]['su'][0]['id'])]
        date = timetable[lesson]['startTime']
        ausfall += f"{lessonname} bei {teachers[lessonname]} in der {hours[date]} Stunde\n"

    if ausfall == "Heute entfallen folgende Stunden:\n":
        return "Heute entfallen keine Stunden"
    else:
        return ausfall

def send_telegram(message: str):
    if message == "":
        logging.log(level=logging.INFO, msg="No message to send")
        return
    req_resp = post(
    url='https://api.telegram.org/bot{0}/{1}'.format(os.getenv("TELEGRAM_API_TOKEN"), 'sendMessage'),
    data={'chat_id': os.getenv("CHAT_ID"), 'text': message}
    ).json()

    if req_resp['ok']:
        logging.log(level=logging.INFO, msg="Message sent to telegram")
    else:
        logging.log(level=logging.ERROR, msg="Message not sent to telegram")
        logging.log(level=logging.ERROR, msg="Error message: " + str(req_resp['description']))


def do_send(sess, when):
    l = sess.login()
    if l == "Error":
        logging.log(level=logging.ERROR, msg="Error while logging in")
        sleep(60)
        return
    sess.get_timetable(when)
    sess.logout()
    message = create_message()

    if type(message) == str:
        send_telegram(message)
    else:
        return message

def do_extension(sess, when):
    sess.get_timetable(when)
    sess.logout()
    message = create_message_extended()
    if type(message) == list:
        send_telegram(message)
    else:
        return message


def main():
    reqenvvars = ["TELEGRAM_API_TOKEN", "CHAT_ID", "UNTIS_USER", "UNTIS_PASSWORD", "SCHOOL", "CLASS_ID", "URL", "USERAGENT", "CRONTAB_URL"]
    for i in reqenvvars:
        if i not in os.environ:
            logging.log(level=logging.ERROR, msg=f"Environment variable {i} not set")
            exit(f"Environment variable {i} not set")
    # obgligated initialisations
    sess = UntisSess()

    l = None
    for i in range(3):
        l = sess.login()
        if l == "Error":
            logging.log(level=logging.ERROR, msg="Error while logging in")
            sleep(60)
            continue
        else:
            break

    if l == "Error" or l == None:
        logging.log(level=logging.ERROR, msg=f"Error while logging in. Value of l = {l}")
        return

    sess.get_subjects()

    now = datetime.datetime.now()

    if now.isoweekday() == 6 or (now.isoweekday() == 7 and now.hour < 19):
        pass

    elif now.isoweekday() == 7 and now.hour > 20:
        res = do_send(sess, "tomorrow")

    elif now.hour == 7:
        res = do_extension(sess, "today")

    else:
        do_send(sess, "tomorrow")

    return "Success"

def sendsuccess():
    if get(str(os.getenv("CRONTAB_URL"))).status_code == 200:
        logging.log(level=logging.INFO, msg="Success message sent to status.liep.live")
    else:
        logging.log(level=logging.ERROR, msg="Error while sending success message to status.liep.live")

if __name__ == "__main__":
    dotenv.load_dotenv()
    logging.basicConfig(filename='untis_ms.log', filemode="a", level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    res = main()
    if res == "Success":
        sendsuccess()

    else:
        logging.log(level=logging.ERROR, msg="Error while running: " + str(res))