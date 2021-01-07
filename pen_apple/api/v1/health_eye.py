# -*- coding: utf-8 -*-

import json
from functools import wraps
from flask import Blueprint, request, jsonify, current_app, abort
from flask_restful import Api, Resource
from ...commons import exceptions
from ...commons.utils import checksum_md5, params_encrypt
from ...models import GeoData, DataSource, DataOption, DataResult
from ...extensions import db
from ...tasks import test, test_b
import os
import uuid

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


@api.resource('/config/age_group')
class GroupConfigApi(Resource):
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
