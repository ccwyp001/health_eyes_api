# -*- coding: utf-8 -*-

import json
from functools import wraps
from flask import Blueprint, request, jsonify, current_app
from flask_restful import Api, Resource
from ...commons import exceptions
from flask_jwt_extended import (
    jwt_required, create_access_token, jwt_refresh_token_required,
    create_refresh_token, get_jwt_identity)
from datetime import datetime
from ...commons.utils import md5_code

bp = Blueprint('user', __name__)
api = Api(bp)


def double_wrap(f):
    @wraps(f)
    def new_dec(*args, **kwargs):
        if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
            # actual decorated function
            return f(args[0])
        else:
            # decorator arguments
            return lambda real_f: f(real_f, *args, **kwargs)

    return new_dec


@double_wrap
def check_identity(fn, roles=0):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        current_user = get_jwt_identity()
        _ = json.loads(current_user)
        if _.get('roles', 0) & roles:
            return fn(*args, **kwargs)
        raise exceptions.InsufficientPrivilege

    return wrapper


@api.resource('/test')
class TestApi(Resource):
    @jwt_required
    def get(self):
        return {'a': 'hello world'}


@api.resource('/current')
class CurrentUserApi(Resource):
    # @jwt_required
    def get(self):
        # current_user = get_jwt_identity()
        # _ = json.loads(current_user)
        # return {'name': _.get('name'), 'userid': _.get('id')}
        return {'name': 'Small Big', 'userid': '00000001'}


@api.resource('/login')
class Login(Resource):
    def post(self):
        try:
            data = request.json
            # TODO login api
            return {"status": 'ok',
                    "currentAuthority": "admin"}
            if data:
                identity = json.dumps({'id': data['userName']})
                access_token = create_access_token(identity=identity)
                refresh_token = create_refresh_token(identity=identity)
                return {"access_token": access_token,
                        "refresh_token": refresh_token,
                        "status": 'ok',
                        "currentAuthority": "admin"}
            raise exceptions.AccountLoginFailed
        except:
            raise exceptions.AccountLoginFailed


@api.resource('/token')
class Refresh(Resource):
    @jwt_refresh_token_required
    def post(self):
        current_user = get_jwt_identity()
        # print(current_user)
        ret = {
            'access_token': create_access_token(identity=current_user),
            'refresh_token': create_refresh_token(identity=current_user)
        }
        return ret
