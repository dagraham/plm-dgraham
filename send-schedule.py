#!/usr/bin/python3

import email, smtplib, ssl, os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

import sys
import yaml


def send_mail(calfile, test=False):
    smtp_from = os.getenv('GMAIL_ADDRESS', None)
    smtp_pw = os.getenv('GMAIL_APPLICATION_PASSWORD', None)
    smtp_id = os.getenv('GMAIL_ID', None)
    smtp_server = 'smtp.gmail.com'
    smtp_address = 'dnlgrhm@gmail.com'
    port = 465

    pname, fname = os.path.split(calfile)
    dayname, ext = fname.split('.')
    rootfile = os.path.join(pname, "root.yaml")
    txtfile = os.path.join(pname, f"{dayname}.txt")
    calname = f"{dayname}.cal"
    txtname = f"{dayname}.txt"

    # load the calendar details
    print(f"using calfile: {calfile}")
    with open(calfile, 'r') as fo:
        details = yaml.load(fo, Loader=yaml.SafeLoader)
        # print("details:\n", details)
    # load the calendar details
    with open(rootfile, 'r') as fo:
        yaml_data = yaml.load(fo, Loader=yaml.SafeLoader)

    smtp_to = [x[1] for x in details]

    TITLE = yaml_data['TITLE']
    # if yaml_data['MINUTES']:
    #     STARTTIME = "{0}:{1}".format(yaml_data['HOURS'], yaml_data['MINUTES'])
    # else:
    #     STARTTIME = "{0}".format(yaml_data['HOURS'])

    head1 = f"""\
This is your personal schedule for {TITLE}.

SCHEDULED: You are scheduled to play on each of the dates listed below along with the THREE OTHER PLAYERS whose names follow the date. You are the captain for dates with asterisks. The captain is the player listed first for dates without asterisks. The captain is responsible for making the court reservations on Foretees and for providing the tennis balls."""

    maybehead = """\
POSSIBLE: Listed below are dates in which there are available but unscheduled players (without asterisks) who could be combined with possible substitute players (with asterisks) or players from outside the group to make a foursome. As an available player on these occassions, would you please reach out to the other players (before other plans are made) to see if a foursome could be scheduled? Player email addresses are in the attached ".txt" file."""

    head2 = """\
There are two attachments to this email. The first has the extension ".cal". It contains your personal schedule in a format that can be imported into your favorite calendar application. Importing this file will not only add the times you are playing to your calendar but also schedule timely reminders when you, as captain, need to reserve a court. You need to save the attachment and change the extension to ".ics" to import it.

The second attachment has the extension ".txt". It contains the complete schedules for all players in a plain text format. You may want to save this attachment for reference.
"""

    with smtplib.SMTP_SSL(smtp_server, port) as server:
        server.login(smtp_id, smtp_pw)
        print("logged in")
        # print(details)
        for name, address, cal, etm, ics, maybe, *other in details:
            # if other:
            #     print(name, address, other)
            # else:
            #     print(name)
            if address not in smtp_to:
                print('    skipping', name, '- not in smtp_to')
                continue
            if test and address != smtp_address:
                print('    skipping', name, '- testing and not smtp_address')
                continue
            if not cal and not test:
                print('    skipping', name, '- not scheduled')
                continue

            maybesection = f"{maybehead}\n\n{maybe}\n\n{head2}" if maybe else head2


            print('emailing', name)
            msg = MIMEMultipart()
            msg['From'] = smtp_from
            msg['To'] = address
            msg['Subject'] = TITLE
            body = f"""\
Dear {name.split(" ")[0].strip()},

{head1}

{cal}

{maybesection}
"""
            msg.attach(MIMEText(body, 'plain'))

            p = MIMEBase('application', 'octet-stream')
            p.set_payload(ics)
            encoders.encode_base64(p)
            p.add_header('Content-Disposition', f"attachment; filename={calname}")
            msg.attach(p)

            # print(f"attaching: {type(etm)}")
            # p = MIMEBase('application', 'octet-stream')
            # p.set_payload(etm)
            # encoders.encode_base64(p)
            # p.add_header('Content-Disposition', f"attachment; filename={basename}.etm")
            # msg.attach(p)

            with open(txtfile, 'r') as fo:
                sched = fo.read()
            p = MIMEBase('application', 'octet-stream')
            p.set_payload(sched)
            encoders.encode_base64(p)
            p.add_header('Content-Disposition', f"attachment; filename={txtname}")
            msg.attach(p)

            text = msg.as_string()
            # changed from smtp_to below to address 6/16/20
            server.sendmail(smtp_from, address, text)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        test = (len(sys.argv) > 2 and sys.argv[2] == "test")
        # basename = os.path.splitext(sys.argv[1])[0]
        calfile = sys.argv[1]
        dayname, ext = calfile.split('.')
        if ext == "cal":
            send_mail(calfile, test)
        else:
            print('The file extension must be "cal"')

    else:
        print('Usage: <path to <weekday>.cal [test]')

