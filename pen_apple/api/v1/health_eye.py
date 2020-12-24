# -*- coding: utf-8 -*-

import json
from functools import wraps
from flask import Blueprint, request, jsonify, current_app, abort
from flask_restful import Api, Resource
from ...commons import exceptions
from ...models import GeoData
from ...extensions import db
from ...tasks import test
import os
import uuid

bp = Blueprint('health_eye', __name__)
api = Api(bp)


@api.resource('/')
class AuthRouteApi(Resource):
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


@api.resource('/upload')
class AmbulManagePicApi(Resource):
    def post(self):
        file = request.files['file']
        save_name = str(uuid.uuid4()) + '.' + file.filename.split('.')[-1]
        save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], save_name)
        file.save(save_path)
        test.delay(save_path)
        #
        # if os.path.getsize(save_path) > 10 * 1024 * 1024:
        #     os.remove(save_path)
        #     abort(415)
        return {'id':'1'}
