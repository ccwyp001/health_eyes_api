# -*- coding: utf-8 -*-
import datetime
import traceback

import os
import json
import time
import uuid

import requests
# from suds.client import Client
from flask import current_app
from .commons.utils import str_coding
from .commons.exceptions import ItemDoesNotExist
from .extensions import celery, db
from .models import DataOption, DataResult, AnalysisRecord, DataSource, AgeGroup, Icd10Data
from hashlib import md5
import pandas as pd


def result_record(sign, name, value, state, sleep_time=0.1):
    print(name)
    if sleep_time:
        time.sleep(sleep_time)
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


def function_top(data, filter_data, **kwargs):
    g = data.groupby(['ICD10'])
    df_new = g.count().sort_values(by=['IDCARD'], ascending=0)
    gg = df_new['IDCARD'].head(10).to_dict()
    return [{'x': k, 'y': v, 'n': query_icd_name(k)} for k, v in gg.items()]


def function_org_dis(data, filter_data, **kwargs):
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


def function_time_dis(data, filter_data, **kwargs):
    g = filter_data.groupby(['ICD10'])
    df_new = g.resample('D').count()
    gg = df_new['IDCARD'].fillna(0).to_dict()
    ggg = {}
    for k, v in gg.items():
        if ggg.get(k[1]):
            ggg[k[1]].update({k[0]: v})
        else:
            ggg[k[1]] = {}
            [ggg[k[1]].update({_: 0}) for _ in g.count().index]
            ggg[k[1]].update({k[0]: v})

    g = filter_data.resample('D')
    df_new = g.count()
    gg = df_new['IDCARD'].fillna(0).to_dict()
    return [{'x': str(k), 'y': v, 'icds': ggg[k]} for k, v in gg.items()]


def function_age_dis(data, filter_data, **kwargs):
    age_groups = kwargs.get('age_groups')
    if age_groups:
        age_groups = [
            {'name': _.name, 'list': json.loads(_.group)}
            for _ in AgeGroup.query.filter(AgeGroup.sign.in_(age_groups)).all()
        ]
    else:
        age_groups = [{
            'name': '默认分组',
            'list': [0, 1, 2, 3, 4, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80]
        }]

    g = filter_data.groupby(['NL'])
    df_new = g.count().sort_index(axis=0, ascending=1)
    gg = df_new['IDCARD']
    return [{'groupName': group['name'], 'groupData': age_dis_spec(gg, group['list'])} for group in age_groups]


def age_dis_spec(data, group_list):
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
             'y': int(data[i[0]:i[1] if isinstance(i[1], int) else None].sum())} for i in nl_list]


def function_gender_dis(data, filter_data, **kwargs):
    g = filter_data.groupby(['XB'])
    df_new = g.count().sort_index(axis=0, ascending=1)
    return df_new['IDCARD'].to_dict()


def function_occ_dis(data, filter_data, **kwargs):
    g = filter_data.groupby(['OCCUPATION'])
    df_new = g.count().sort_index(axis=0, ascending=[1])
    gg = df_new['IDCARD'].fillna(0).to_dict()
    return [{'x': k, 'y': v} for k, v in gg.items()]


def function_ins_dis(data, filter_data, **kwargs):
    g = filter_data.groupby(['INS'])
    df_new = g.count().sort_index(axis=0, ascending=[1])
    gg = df_new['IDCARD'].fillna(0).to_dict()
    return [{'x': k, 'y': v} for k, v in gg.items()]


def function_town_dis(data, filter_data, **kwargs):
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
    community_dis = function_community_dis(filter_data)
    return [{'x': k, 'y': v, 'icds': ggg[k], 'children': community_dis.get(k, [])} for k, v in gg.items()]


def function_community_dis(filter_data):
    g = filter_data.groupby(['TOWN', 'COMMUNITY', 'ICD10'])
    df_new = g.count().sort_index(axis=0, ascending=[1, 1])
    gg = df_new['IDCARD'].fillna(0).to_dict()
    ggg = {}
    for k, v in gg.items():
        if ggg.get(k[0]):
            if ggg.get(k[0]).get(k[1]):
                ggg.get(k[0])[k[1]].update({k[2]: v})
            else:
                ggg.get(k[0])[k[1]] = {k[2]: v}
        else:
            ggg[k[0]] = {k[1]: {k[2]: v}}

    g = filter_data.groupby(['TOWN', 'COMMUNITY'])
    df_new = g.count().sort_index(axis=0, ascending=[1])
    gg = df_new['IDCARD'].fillna(0).to_dict()
    community_dis = {}
    [community_dis.update({k[0]: []}) for k, v in g]
    [community_dis[k[0]].append({'x': k[1], 'y': gg.get(k), 'icds': ggg[k[0]][k[1]]}) for k, v in g]
    return community_dis


def analysis_record(sign, state, exists_flag=False, value=''):
    data = {
        'sign': sign,
        'result': json.dumps(value),
        'state': state
    }
    _ = AnalysisRecord.query.filter(AnalysisRecord.sign == data['sign']).first()
    if _:
        if exists_flag and _.state != 99:  # record exists and state is not error
            return False
        _.update(data)
    else:
        _ = AnalysisRecord.from_data(data)
    with db.auto_commit_db():
        db.session.add(_)
    return True


def source_init_record(source_id, rate, status, value=''):
    data = {
        'rate': rate,
        'result': json.dumps(value),
        'status': status,
    }
    _ = DataSource.query.get(source_id)
    if _:
        _.update(data)
    with db.auto_commit_db():
        db.session.add(_)
    return True


def pre_deal(file_path, col_list=None):
    """
    :keyword 预处理：打开csv，xlsx文件，索引类型优化，并排序

    :param file_path: file path
    :param col_list: cols list which used
    :return: file data stream
    """
    encoding = str_coding(file_path)
    encoding = [encoding, 'gbk'][encoding == 'GB2312']

    if file_path.split('.')[-1] == 'csv':
        data = pd.read_csv(file_path, usecols=col_list, encoding=encoding)
    else:
        data = pd.read_excel(file_path, usecols=col_list)
    # data.to_csv('eee.csv', index=False, header=False, mode='a')
    print(data.columns.to_list())

    return data


def query_icd_name(code):
    _ = Icd10Data.query.filter(Icd10Data.code == code).first()

    return _.name if _ else code


def query_icd(row):
    _ = Icd10Data.query.filter(Icd10Data.code == str(row['ICD10'])).first()
    result = [None, None, None]

    def set_code(i):
        result[i.level - 2] = i.code
        return set_code(i.parent) if i.level > 2 else True

    if _:
        set_code(_)
    # print(result)
    return result


@celery.task
def test(source_id):
    data_source = DataSource.query.get(source_id)
    file_path = data_source.path
    cols_config = json.loads(data_source.colsConfig)
    rate = 20
    try:
        pre_data = pre_deal(file_path, [_ for _ in cols_config.values()])

        rate = 40
        source_init_record(source_id, rate, 0)

        data = pd.DataFrame()
        for k, v in cols_config.items():
            data[k] = pre_data[v]

        data['NL'] = pd.to_numeric(data['NL'], errors='coerce', downcast='float')
        data['ORG_CODE'] = data['ORG_CODE'].astype('category')
        data['INS'] = data['INS'].astype('category')
        data['TOWN'] = data['TOWN'].astype('category')
        data['XB'] = data['XB'].astype('category')
        data['OCCUPATION'] = data['OCCUPATION'].astype('category')
        data['COMMUNITY'] = data['COMMUNITY'].astype('category')
        data['CLINIC_TIME'] = pd.to_datetime(data['CLINIC_TIME'], format='%Y-%m-%d %H:%M:%S')
        data['SICKEN_TIME'] = pd.to_datetime(data['SICKEN_TIME'], format='%Y-%m-%d %H:%M:%S')

        data[['ICD10_2', 'ICD10_3', 'ICD10_4']] = data.apply(query_icd, axis=1, result_type="expand")
        print(data)
        rate = 70
        source_init_record(source_id, rate, 0)

        data.set_index('CLINIC_TIME', inplace=True)
        data.index = pd.DatetimeIndex(data.index)
        data = data.sort_index(axis=0, ascending=True)
        data = data.sort_index(axis=1, ascending=True)
        data = data.dropna(how='all')
        print(data)
        data.to_hdf(file_path + '.h5', 'aaa', mode='w', format="table")
        print(function_top(data, ''))
        rate = 100
        source_init_record(source_id, rate, 1)
    except Exception as e:
        print(e)
        traceback.print_exc()
        source_init_record(source_id, rate, 2, str(e))
    return True


def load_hdf(file_path: str) -> object:
    """

    :param file_path:
    """
    data = pd.read_hdf(file_path + '.h5', key='aaa')
    return data


@celery.task
def test_b(param_data: dict, param_sign):
    # loading
    if not analysis_record(param_sign, 0, True):
        return 'analysis done yet !'

    source = param_data.get('source', 0)
    clinic_time = param_data.get('clinic_time', [])
    sicken_time = param_data.get('sicken_time', [])
    age_groups = param_data.get('age_groups', [])
    icd10s = param_data.get('icd10s', [])
    icd_level = param_data.get('icd_level', 4)

    data_source = DataSource.query.filter(DataSource.sign == source).first()
    file_path = data_source.path

    try:
        # 读入数据
        data = load_hdf(file_path)
        # initializing
        analysis_record(param_sign, 1)
        if clinic_time:
            data = data[clinic_time[0]:clinic_time[1]]
        if sicken_time:
            data = data[(data['SICKEN_TIME'].map(
                lambda x:
                datetime.datetime.strptime(sicken_time[0], '%Y-%m-%d')
                <=
                x
                <=
                datetime.datetime.strptime(sicken_time[1], '%Y-%m-%d')
            ))]
        if icd_level:
            data['ICD10'] = data['ICD10_' + str(icd_level)]
        if icd10s:
            data = data[(data['ICD10'].map(lambda x: x in icd10s))]

        g = data.groupby(['ICD10'])
        df_new = g.count().sort_values(by=['IDCARD'], ascending=0)
        gg = df_new['IDCARD'].head(10).to_dict()
        filter_data = data[(data['ICD10'].map(lambda x: x in list(gg.keys())))]
        if filter_data.empty:
            raise ItemDoesNotExist('查询数据为空, 请重新选择筛选项')
        # processing
        analysis_record(param_sign, 2)
        func_list = ['top', 'town_dis', 'org_dis', 'age_dis', 'occ_dis', 'gender_dis', 'ins_dis', 'time_dis']

        [result_record(
            param_sign,
            name,
            [],
            1
        ) for name in func_list]
        [result_record(
            param_sign,
            name,
            globals()['function_' + name](data, filter_data, **{'age_groups': age_groups}),
            2
        ) for name in func_list]
        analysis_record(param_sign, 3)
    except Exception as e:
        print(e)
        traceback.print_exc()
        analysis_record(param_sign, 99, value=str(e))

    return True
