import re

import os


def parse_conf_file(conf_path):
    if re.match('^~', conf_path):
        conf_path = conf_path.replace('~', os.environ['HOME'])

    lines = [x.strip() for x in open(conf_path) if re.match('^[\w*.~]', x.strip())]
    param = {}
    for p in lines:
        tmp = p.split('=', 1)
        if len(tmp) == 2:
            name = tmp[0].strip()
            value = tmp[1].strip()
            if re.match('^~/', value):
                value = value.replace('~', os.environ['HOME'])
            param[name] = value

    return param


def parse_ignore_file(ignore_path):
    if re.match('^~', ignore_path):
        ignore_path = ignore_path.replace('~', os.environ['HOME'])

    lines = [x.strip() for x in open(ignore_path) if re.match('^[\w*.]', x.strip())]
    return lines


def parse_conf_lines(lines):
    lines = [x.strip() for x in lines if re.match('^[\w*.]', x.strip())]
    param = {}
    for p in lines:
        tmp = p.split('=', 1)
        if len(tmp) == 2:
            param[tmp[0].strip()] = tmp[1].strip()

    return param
