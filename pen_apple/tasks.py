# -*- coding: utf-8 -*-
import os
import json
import time
import uuid

import requests
# from suds.client import Client
from flask import current_app
from .extensions import celery, db
from .models import DataOption, DataResult
from hashlib import md5
import pandas as pd


def pre_deal(file_path):
    """
    :keyword 预处理：打开csv，xlsx文件，索引类型优化，并排序

    :param file_path: file path
    :return: file data stream
    """
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
    return data


def result_record(sign, name, value, state):
    print(name)
    data = {
        'sign': sign,
        'name': name,
        'result': json.dumps(value),
        'state': state
    }
    _ = DataResult.query.filter(DataResult.sign == data['sign'], DataResult.name == data['name']).first()
    if _:
        _.update(data)
    else:
        _ = DataResult.from_data(data)
    db.session.add(_)
    db.session.commit()
    return True


def function_top(data, filter_data):
    g = data.groupby(['ICD10'])
    df_new = g.count().sort_values(by=['IDCARD'], ascending=0)
    gg = df_new['IDCARD'].head(10).to_dict()
    return [{'x': k, 'y': v} for k, v in gg.items()]


def function_org_dis(data, filter_data):
    g = filter_data.groupby(['ORG_CODE', 'ICD10'])
    df_new = g.count().sort_index(axis=0, ascending=[1, 1])
    gg = df_new['IDCARD'].fillna(0).to_dict()
    ggg = {}
    for k, v in gg.items():
        if ggg.get(k[0]):
            ggg[k[0]].update({k[1]: v})
        else:
            ggg[k[0]] = {k[1]: v}

    g = filter_data.groupby(['ORG_CODE'])
    df_new = g.count()
    gg = df_new['IDCARD'].fillna(0).to_dict()
    return [{'x': k, 'y': v, 'icds': ggg[k]} for k, v in gg.items()]


def function_time_dis(data, filter_data):
    g = filter_data.groupby(['ICD10']).resample('D')
    df_new = g.count()
    gg = df_new['IDCARD'].fillna(0).to_dict()
    ggg = {}
    for k, v in gg.items():
        if ggg.get(k[1]):
            ggg[k[1]].update({k[0]: v})
        else:
            ggg[k[1]] = {k[0]: v}

    g = filter_data.resample('D')
    df_new = g.count()
    gg = df_new['IDCARD'].fillna(0).to_dict()
    return [{'x': str(k), 'y': v, 'icds': ggg[k]} for k, v in gg.items()]


def function_age_dis(data, filter_data):
    g = filter_data.groupby(['NL'])
    df_new = g.count().sort_index(axis=0, ascending=1)
    gg = df_new['IDCARD']
    group_list = [
        0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85]
    nl_list = []
    for i in range(len(group_list)):
        if i == 0:
            if group_list[i + 1] - group_list[i] == 1:
                nl_list.append([0, 0])
                nl_list.append([group_list[i + 1], group_list[i + 1]])
            else:
                nl_list.append([group_list[i], group_list[i + 1]])
        else:
            nl_list.append([group_list[i] + 1, group_list[i + 1] if i < len(group_list) - 1 else ''])

    return [{'x': str(i[0]) if i[0] == i[1] else '{}-{}'.format(i[0], i[1]),
             'y': int(gg[i[0]:i[1] if isinstance(i[1], int) else None].sum())} for i in nl_list]


def function_gender_dis(data, filter_data):
    g = filter_data.groupby(['XB'])
    df_new = g.count().sort_index(axis=0, ascending=1)
    return df_new['IDCARD'].to_dict()


def function_occ_dis(data, filter_data):
    g = filter_data.groupby(['OCCUPATION'])
    df_new = g.count().sort_index(axis=0, ascending=[1])
    gg = df_new['IDCARD'].fillna(0).to_dict()
    return [{'x': k, 'y': v} for k, v in gg.items()]


def function_ins_dis(data, filter_data):
    g = filter_data.groupby(['INS'])
    df_new = g.count().sort_index(axis=0, ascending=[1])
    gg = df_new['IDCARD'].fillna(0).to_dict()
    return [{'x': k, 'y': v} for k, v in gg.items()]


def function_town_dis(data, filter_data):
    g = filter_data.groupby(['TOWN', 'ICD10'])
    df_new = g.count().sort_index(axis=0, ascending=[1, 1])
    gg = df_new['IDCARD'].fillna(0).to_dict()
    ggg = {}
    for k, v in gg.items():
        if ggg.get(k[0]):
            ggg[k[0]].update({k[1]: v})
        else:
            ggg[k[0]] = {k[1]: v}
    g = filter_data.groupby(['TOWN'])
    df_new = g.count().sort_index(axis=0, ascending=[1])
    gg = df_new['IDCARD'].fillna(0).to_dict()
    return [{'x': k, 'y': v, 'icds': ggg[k]} for k, v in gg.items()]


@celery.task
def test(file_path):
    data = pre_deal(file_path)
    return function_top(data, '')


@celery.task
def test_b(file_path, param_sign):
    data = pre_deal(file_path)
    g = data.groupby(['ICD10'])
    df_new = g.count().sort_values(by=['IDCARD'], ascending=0)
    gg = df_new['IDCARD'].head(10).to_dict()
    filter_data = data[(data['ICD10'].map(lambda x: x in list(gg.keys())))]
    func_list = ['top', 'town_dis', 'org_dis', 'age_dis', 'occ_dis', 'gender_dis', 'ins_dis', 'time_dis']
    # func_name = 'org_dis'
    # value = globals()['function_' + func_name](data, filter_data)
    # result_record(param_sign, func_name, value, state=2)
    [result_record(
        param_sign,
        name,
        globals()['function_' + name](data, filter_data),
        state=2
    ) for name in func_list]
    return True
