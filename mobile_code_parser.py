#!.venv/bin/python3
# vim: set fileencoding=utf-8 :

import argparse
import os
from sys import stderr, stdout
from io import BytesIO
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate

from requests import get
from lxml import html


def get_full_table():
    raw_data = list()
    for code in range(900, 1000):
        print('Parsing code {}...'.format(code), end='\r', file=stderr)
        spam = get_part('http://www.kody.su/mobile/{}'.format(code))
        if spam != 404:
            raw_data.extend(spam)
    return raw_data


def get_part(url):
    response = get(url)
    if response.status_code == 404:
        return 404
    htm = html.parse(BytesIO(response.content)).getroot().find_class('tbnum').pop()
    data = [get_row(_) for _ in htm.getchildren()[1:]]
    return data


def get_row(html_row):
    result = dict()
    row = html_row.getchildren()
    long_template = row[0].text.split('-')
    result['code'] = long_template[0]
    result['templates'] = [long_template[1]]
    result['templates'].extend([span.text for span in row[0].getchildren() if span.text])
    result['provider'] = row[1].text
    result['region'] = row[2].text or ''
    return result


def parse_to(out, encoding='utf-8'):
    parsed = parse()
    file = open(out, 'w', encoding=encoding) if type(out) is str else out
    file.write(parsed)
    file.close()


def parse():
    raw_table = get_full_table()
    result = ''
    for row in raw_table:
        result += ''.join([
            '"{}{}";"{}";"{}"\r\n'.format(row['code'], template, row['provider'], row['region'])
            for template in row['templates']])
    return result


def send_mail(send_from, send_to, subject, text, files=None, server="localhost"):
    assert isinstance(send_to, list)
    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = COMMASPACE.join(send_to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject
    msg.attach(MIMEText(text))
    for f in files or []:
        with open(f, "rb") as fil:
            part = MIMEApplication(fil.read(), Name=os.path.basename(f))
            part['Content-Disposition'] = 'attachment; filename="%s"' % os.path.basename(f)
            msg.attach(part)
    smtp = smtplib.SMTP(server)
    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.close()


def diff(file_a, file_b, encoding='utf-8'):
    with open(file_a, 'r', encoding=encoding) as fa:
        with open(file_b, 'r', encoding=encoding) as fb:
            while True:
                try:
                    a = fa.readline()
                    b = fb.readline()
                except UnicodeDecodeError:
                    return True
                if a != b:
                    return True
                if a == '':
                    return False


def main():
    argp = argparse.ArgumentParser(description='Parses mobile codes from kody.su website into CSV format.')
    argp.add_argument('--out', help='Output filename. Default: {}'.format(stdout.name), default=stdout)
    argp.add_argument('--encoding', help='Output encoding. Default: UTF-8', default='utf-8')
    argp.add_argument(
        '--mail', help='Send file to MAIL. Overrides parameter "--out" with "results/codes.csv".', action='append')
    args = argp.parse_args()
    if args.mail is None:
        parse_to(out=args.out, encoding=args.encoding)
        return
    result_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'results')
    old_file = os.path.join(result_dir, 'codes.old')
    new_file = os.path.join(result_dir, 'codes.csv')
    if not os.path.isdir(result_dir):
        os.mkdir(result_dir)
    elif os.path.exists(new_file):
        if os.path.exists(old_file):
            os.remove(old_file)
        os.rename(new_file, old_file)
    parse_to(out=new_file, encoding=args.encoding)
    if not os.path.exists(old_file) or diff(old_file, new_file, encoding=args.encoding):
        send_mail(
            send_from='eIGato@github.com',
            send_to=args.mail,
            subject='Мобильные коды',
            text='Новые мобильные коды во вложении.',
            files=[new_file])
    else:
        send_mail(
            send_from='eIGato@github.com',
            send_to=args.mail,
            subject='Мобильные коды',
            text='Со времени предыдущего парсинга коды не изменились. Используйте старый файл.',
            files=[])


if __name__ == '__main__':
    main()
