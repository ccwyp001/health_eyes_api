# -*- coding: utf-8 -*-
import tempfile
import json
from functools import wraps
from flask import Blueprint, request, jsonify, current_app, abort
from flask_restful import Api, Resource
from ...commons import exceptions
from ...commons.utils import checksum_md5, params_encrypt, md5_code
from ...models import GeoData, DataSource, DataOption, DataResult, Icd10Data, AgeGroup
from ...extensions import db
from ...tasks import test, test_b
import os
import uuid
import pandas as pd

bp = Blueprint('health_eye', __name__)
api = Api(bp)


@api.resource('/')
class SelectApi(Resource):
    def get(self):
        params = request.args
        return params


@api.resource('/data')
class DataListApi(Resource):
    def get(self):
        params = request.args
        source = params.get('source', 0)
        data_source = DataSource.query.filter(DataSource.sign == str(source)).first()
        if not data_source:
            data_source = DataSource.query.first()
            if not data_source:
                abort(404, 'no data source')
        source = data_source.sign
        path = data_source.path

        data = {
            'source': source
        }
        # print(data)
        _ = params_encrypt(data, 'healtheye666')
        test_b.delay(path, _)
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
        data = AgeGroup.query.all()
        return [_.display() for _ in data]

    def post(self):
        data = request.json
        data['group'] = json.dumps(data['group'])
        data['sign'] = md5_code(data['group'])
        age_data = AgeGroup.query.filter(AgeGroup.sign == data['sign']).first()
        if age_data:
            return 'age group exists'
        age_data = AgeGroup.from_data(data)
        db.session.add(age_data)
        db.session.commit()
        return 'ok'


@api.resource('/config/age_group/<int:p>')
class GroupConfigApi(Resource):
    def get(self):
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
            v_list = GeoData.query.filter(GeoData.fullname == arg).all()
            return [_.display() for _ in v_list]
        return []


@api.resource('/icd10_list/_search')
class Icd10ListApi(Resource):
    def get(self):
        params = request.args
        arg = params.get('q', 0)
        if arg and len(arg) >= 2:
            rule = db.or_(
                Icd10Data.name.like('%%%s%%' % arg),
                Icd10Data.code.like('%%%s%%' % str(arg).upper()),
                Icd10Data.inputcode1.like('%%%s%%' % str(arg).upper()),
                Icd10Data.inputcode2.like('%%%s%%' % str(arg).upper()),
            )
            v_list = Icd10Data.query.filter(rule).distinct().all()
            return [_.display() for _ in v_list]
        return []


@api.resource('/source')
class DataSourceApi(Resource):
    def get(self):
        data = DataSource.query.all()
        return [_.display() for _ in data]

    def post(self):
        file = request.files['file']
        save_name = str(uuid.uuid4()) + '.' + file.filename.split('.')[-1]
        save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], save_name)
        file.save(save_path)
        sign = checksum_md5(save_path)
        exist_data = DataSource.query.filter(DataSource.sign == sign).first()
        if exist_data:
            os.remove(save_path)
            abort(400, 'this file is exists')

        data = {'name': file.filename.split('.')[0],
                'path': save_path,
                'sign': sign,
                }

        data_source = DataSource.from_data(data)
        db.session.add(data_source)
        db.session.commit()
        test.delay(save_path)
        #
        # if os.path.getsize(save_path) > 10 * 1024 * 1024:
        #     os.remove(save_path)
        #     abort(415)
        return data

    def delete(self):
        pass
