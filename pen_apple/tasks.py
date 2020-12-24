# -*- coding: utf-8 -*-
import os
import json
import time
import uuid

import requests
# from suds.client import Client
from flask import current_app
from .extensions import celery, db
# from .models import TtsHistory
from hashlib import md5
import pandas as pd


def new_encrypt(t1, t2):
    md = md5()
    _ = t2 + ''.join(['%s%s' % (k, v) for k, v in sorted(t1.items())]) + t2
    # print(_)
    md.update(_.encode())
    p1 = md.hexdigest()

    return p1


@celery.task
def test(file_path):
    if file_path.split('.')[-1] == 'csv':
        data = pd.read_csv(file_path)
    else:
        data = pd.read_excel(file_path)
    # data.to_csv('eee.csv', index=False, header=False, mode='a')

    data['NL'] = pd.to_numeric(data['NL'], errors='coerce', downcast='integer')
    data['ORG_CODE'] = data['ORG_CODE'].astype('category')
    data['INS'] = data['INS'].astype('category')
    data['TOWN'] = data['TOWN'].astype('category')
    data['XB'] = data['XB'].astype('category')
    data['OCCUPATION'] = data['OCCUPATION'].astype('category')
    data['COMMUNITY'] = data['COMMUNITY'].astype('category')
    data['CLINIC_TIME'] = pd.to_datetime(data['CLINIC_TIME'], format='%Y-%m-%d %H:%M:%S')
    data['SICKEN_TIME'] = pd.to_datetime(data['SICKEN_TIME'], format='%Y-%m-%d %H:%M:%S')

    data.set_index('CLINIC_TIME', inplace=True)
    data.index = pd.DatetimeIndex(data.index)
    data = data.sort_index(axis=0, ascending=1)
    data = data.sort_index(axis=1, ascending=1)
    data = data.dropna(how='any')

    return data.dtypes.to_json()

@celery.task
def test_b(data_stream):

    pass