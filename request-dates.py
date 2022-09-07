#!/usr/bin/python3
# FIXME: use results of create-template

import smtplib
import os
import sys
import yaml


def send_mail(rootfile, test=False):
    smtp_from = os.getenv('GMAIL_ADDRESS', None)
    smtp_pw = os.getenv('GMAIL_APPLICATION_PASSWORD', None)
    smtp_id = os.getenv('GMAIL_ID', None)
    smtp_server = 'smtp.gmail.com'
    port = 465

    # load the calendar details
    with open(rootfile, 'r') as fo:
        yaml_data = yaml.load(fo, Loader=yaml.SafeLoader)

    emails = yaml_data['EMAILS']
    letter = yaml_data['LETTER']

    if test:
        smtp_to = ['dnlgrhm@gmail.com']
    else:
        smtp_to = [address for name, address in emails.items()]

    # print("smtp_to:\n", smtp_to)

    TITLE = yaml_data['TITLE']

    subject = f"""Subject: {TITLE}\n\n"""

    with smtplib.SMTP_SSL(smtp_server, port) as server:
        # print("created server")
        server.login(smtp_id, smtp_pw)
        # print("logged in")

        for name, address in emails.items():
            if address not in smtp_to:
                print('skipping', name, '- not in smtp_to')
                continue
            fname = name.split(' ')[0].strip()
            message = f"""\
Subject: {TITLE}

Dear {fname},

{letter}"""
            print(f'sending email to {name} <{address}>')
            server.sendmail(smtp_from, address, message)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        test = (len(sys.argv) > 2 and sys.argv[2] == "test")
        # basename = os.path.splitext(sys.argv[1])[0]
        rootfile = sys.argv[1]
        send_mail(rootfile, test)
    else:
        print('Usage: <path to root.yaml> [test]')
