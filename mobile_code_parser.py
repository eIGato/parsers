#!/usr/bin/env python3
# vim :set fileencoding=utf-8:

from sys import stderr
from requests import get
from lxml import html


def get_full_table():
    raw_data = list()
    for code in range(900, 1000):
        print(code, file=stderr)
        spam = get_part('http://www.kody.su/mobile/{}'.format(code))
        if spam != 404:
            raw_data.extend(spam)
    return raw_data


def get_part(url):
    if get(url).status_code == 404:
        return 404
    htm = html.parse(url).getroot().find_class('tbnum').pop()
    data = [get_row(_) for _ in htm.getchildren()[1:]]
    return data


def get_row(html_row):
    result = dict()
    row = html_row.getchildren()
    long_template = row[0].text.split('-')
    result['code'] = long_template[0]
    result['templates'] = list((long_template[1],))
    for span in row[0].getchildren():
        if span.text:
            result['templates'].append(span.text)
    result['provider'] = row[1].text
    result['region'] = row[2].text
    if not result['region']:
        result['region'] = ''
    return result


if __name__ == '__main__':
    raw_table = get_full_table()
    for row in raw_table:
        for template in row['templates']:
            print('"{}{}";"{}";"{}"'.format(row['code'], template, row['provider'], row['region']))