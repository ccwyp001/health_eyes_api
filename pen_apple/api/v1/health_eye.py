# -*- coding: utf-8 -*-
import tempfile
import json
from functools import wraps
from flask import Blueprint, request, jsonify, current_app, abort, Response
from flask_restful import Api, Resource
from ...commons import exceptions
from ...commons.utils import checksum_md5, params_encrypt, md5_code, str_coding
from ...models import GeoData, DataSource, DataOption, DataResult, Icd10Data, AgeGroup, AnalysisRecord
from ...extensions import db
from ...tasks import test, test_b
import os
import uuid
import pandas as pd

bp = Blueprint('health_eye', __name__)
api = Api(bp)


@api.resource('/template')
class SelectApi(Resource):
    def get(self):

        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'template.xlsx')

        def generate():
            with open(file_path, "rb") as f:
                while True:
                    chunk = f.read(10 * 1024 * 1024)
                    if not chunk:
                        break
                    yield chunk

        response = Response(generate(), mimetype='application/octet-stream')
        response.headers['Content-Disposition'] = 'attachment; filename={}.xlsx'.format("template")
        response.headers['content-length'] = os.stat(str(file_path)).st_size
        response.headers["Content-type"] = "application/x-xls"
        return response


@api.resource('/data')
class DataListApi(Resource):
    def get(self):
        params = request.args
        sign = params.get('sign', 0)
        _ = AnalysisRecord.query.filter(AnalysisRecord.sign == sign).first()
        if _:
            return {
                'current': _.state,
                'done': len([i for i in _.results if i.state == 2]),
                'total': len(_.results),
            }
        return {}

    def post(self):
        d = {
            # "source": "3",
            # "clinicTime": ["2021-02-01", "2021-02-28"],
            # "sickenTime": ["2021-02-01", "2021-02-28"],
            "town": "0",
            # "age": ["4", "6", "7"],
            "occupation": "0",
            # "icd10": ["E10", "E10.0", "E10.000", "E10.001", "E10.1"],
            "gender": "0"
        }
        data = request.json
        source = data.get('source', 0)
        clinic_time = data.get('clinicTime', [])
        sicken_time = data.get('sickenTime', [])
        age_groups = data.get('age', [])
        icd10s = data.get('icd10', [])
        level = data.get('level', 4)

        data_source = DataSource.query.filter(DataSource.id == int(source)).first()
        if not data_source:
            data_source = DataSource.query.first()
            if not data_source:
                abort(404, 'no data source')
        source = data_source.sign
        age_groups_sign = [_.sign for _ in AgeGroup.query.filter(AgeGroup.id.in_(age_groups)).all()]

        data = {
            'source': source,
            'clinic_time': clinic_time,
            'sicken_time': sicken_time,
            'age_groups': age_groups_sign,
            'icd10s': icd10s,
            'icd_level': level,
        }
        # print(data)
        _ = params_encrypt(data, 'healtheye666')
        test_b.delay(data, _)
        return _


@api.resource('/data/<string:p>')
class DataApi(Resource):
    def get(self, p):
        params = request.args
        option = DataOption.query.filter(DataOption.name == str(p)).first()
        if not option:
            abort(404, 'no this option!')
        sign = params.get('sign', 0)

        data = DataResult.query.filter(DataResult.sign == str(sign), DataResult.name == str(p)).first()
        if not data:
            data = DataResult.query.filter(DataResult.name == str(p)).order_by(db.desc(DataResult.update_at)).first()

        return json.loads(data.result) if data else []


@api.resource('/config/geo')
class GeoConfigApi(Resource):
    def get(self):
        return 'health_eye hello'

    def post(self):
        data = request.json
        geo_data = GeoData.query.filter(GeoData.fullname == data['fullname']).first()
        if geo_data:
            geo_data.update(data)
        else:
            geo_data = GeoData.new(data)
        parent = GeoData.query.filter(GeoData.fullname == data['address']).first()
        if parent:
            geo_data.parent_id = parent.id
        db.session.add(geo_data)
        db.session.commit()
        return 'ok'


@api.resource('/config/age_groups')
class GroupsConfigApi(Resource):
    def get(self):
        params = request.args
        enabled = int(params.get('enabled', 0))
        if enabled:
            data = AgeGroup.query.filter(AgeGroup.disabled != 1).all()
        else:
            data = AgeGroup.query.all()
        return [_.display() for _ in data]

    def post(self):
        data = request.json
        data['group'] = json.dumps(data['group'])
        data['sign'] = md5_code(data['group'])
        age_data = AgeGroup.query.filter(AgeGroup.sign == data['sign']).first()
        if age_data:
            return 'age group exists'
        with db.auto_commit_db():
            age_data = AgeGroup.from_data(data)
            db.session.add(age_data)
        return 'ok'


@api.resource('/config/age_group/<int:p>')
class GroupConfigApi(Resource):
    def get(self, p):
        return 'health_eye hello'

    def put(self, p):
        data = request.json
        data['group'] = json.dumps(data['group'])
        data['sign'] = md5_code(data['group'])
        age_data = AgeGroup.query.get(p)
        if not age_data:
            return 'age group not found'
        with db.auto_commit_db():
            age_data.update(data)
            db.session.add(age_data)
        return 'ok'

    def delete(self, p):
        age_data = AgeGroup.query.get(p)
        if not age_data:
            return 'age group not found'
        with db.auto_commit_db():
            db.session.delete(age_data)
        return 'ok'


@api.resource('/config/icd10')
class Icd10ConfigApi(Resource):
    def get(self):
        return 'health_eye hello'

    def post(self):
        file = request.files['file']
        # make temp file
        tmp = tempfile.mktemp()
        file.save(tmp)
        data_list = pd.read_excel(tmp).fillna(value='').to_dict(orient='records')
        os.unlink(tmp)
        db.session.execute(
            Icd10Data.__table__.insert().prefix_with("IGNORE"),
            data_list
        )
        db.session.commit()
        return 'ok'


@api.resource('/geo')
class GeoApi(Resource):
    def get(self):
        params = request.args
        arg = params.get('fullname', 0)
        if arg:
            v_list = GeoData.query.filter(GeoData.fullname == arg).first()
            return {
                'type': 'FeatureCollection',
                'features': [_.display() for _ in v_list.children]
            } if v_list else {}
        return {}


@api.resource('/icd10_list/_search')
class Icd10ListApi(Resource):
    def get(self):
        params = request.args
        arg = params.get('q', 0)
        level = params.get('level', 4)
        page = int(params.get('page', 1))
        per_page = int(params.get('per_page', 10))
        if arg and len(arg) >= 2:
            rule = db.and_(
                db.or_(
                    Icd10Data.name.like('%%%s%%' % arg),
                    Icd10Data.code.like('%%%s%%' % str(arg).upper()),
                    Icd10Data.inputcode1.like('%%%s%%' % str(arg).upper()),
                    Icd10Data.inputcode2.like('%%%s%%' % str(arg).upper()),
                ),
                Icd10Data.level == int(level),
            )
            v_list = Icd10Data.query.filter(rule).distinct().paginate(page, per_page, error_out=False).items
            return [_.display() for _ in v_list]
        return []


@api.resource('/config/sources')
class DataSourcesApi(Resource):
    def get(self):
        params = request.args
        enabled = int(params.get('enabled', 0))
        page = int(params.get('currentPage', 1))
        per_page = int(params.get('pageSize', 10))
        if enabled:
            _paginate = DataSource.query.filter(DataSource.status == enabled).paginate(page, per_page, error_out=False)
        else:
            _paginate = DataSource.query.paginate(page, per_page, error_out=False)
        return {
            'list': [_.display() for _ in _paginate.items],
            'pagination': {
                'total': _paginate.total,
                'pageSize': _paginate.per_page,
                'current': _paginate.page,
            }
        }

    def post(self):
        file = request.files['file']
        if not file.filename.split('.')[-1] in ['csv', 'xlsx']:
            abort(415, 'unsupported file type')
        save_name = str(uuid.uuid4()) + '.' + file.filename.split('.')[-1]
        save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], save_name)
        file.save(save_path)
        sign = checksum_md5(save_path)
        exist_data = DataSource.query.filter(DataSource.sign == sign).first()
        if exist_data:
            os.remove(save_path)
            abort(400, 'this file is exists')
        encoding = str_coding(save_path)
        encoding = [encoding, 'gbk'][encoding == 'GB2312']

        if save_path.split('.')[-1] == 'csv':
            data = pd.read_csv(save_path, encoding=encoding)
        else:
            data = pd.read_excel(save_path)

        data = {'name': file.filename.split('.')[0],
                'path': save_path,
                'sign': sign,
                'cols': json.dumps(data.columns.to_list()),
                }
        data_source = DataSource.from_data(data)
        with db.auto_commit_db():
            db.session.add(data_source)
        # test.delay(save_path)
        #
        # if os.path.getsize(save_path) > 10 * 1024 * 1024:
        #     os.remove(save_path)
        #     abort(415)
        return data

    def put(self):
        data = request.json
        s_id = data.get('id', '')
        data['colsConfig'] = json.dumps(data['colsConfig'])
        source_data = DataSource.query.get(s_id)
        need_init = False
        if not source_data:
            return 'source data not found'
        if md5_code(data['colsConfig']) != md5_code(source_data.colsConfig):
            data['rate'] = 10
            data['status'] = 0
            need_init = True

        with db.auto_commit_db():
            source_data.update(data)
            db.session.add(source_data)
        if need_init:
            test.delay(s_id)
        return 'ok'

    def delete(self):
        data = request.json
        ids = data.get('ids', [])
        for i in ids:
            s = DataSource.query.get(i)
            if not s:
                continue
            with db.auto_commit_db():
                db.session.delete(s)
            if s.status == 1:
                os.remove(s.path + '.h5')
            os.remove(s.path)
        return 'ok'
