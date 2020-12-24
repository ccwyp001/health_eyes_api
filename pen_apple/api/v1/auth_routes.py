# -*- coding: utf-8 -*-

import json
from functools import wraps
from flask import Blueprint, request, jsonify, current_app
from flask_restful import Api, Resource
from ...commons import exceptions
from ...models import GeoData
from ...extensions import db

bp = Blueprint('auth_routes', __name__)
api = Api(bp)


@api.resource('/')
class AuthRouteApi(Resource):
    def get(self):
        return {'/form/advanced-form': {'authority': ['admin', 'user']}}

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
