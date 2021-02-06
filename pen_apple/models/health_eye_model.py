# -*- coding: utf-8 -*-

from ..extensions import db, SLBigInteger
import time
import json


class DataSource(db.Model):
    __tablename__ = 'data_source'
    id = db.Column(SLBigInteger, primary_key=True)
    name = db.Column(db.String(100))
    sign = db.Column(db.String(100))
    path = db.Column(db.String(100))
    update_at = db.Column(SLBigInteger)

    def __repr__(self):
        return '<DataSource %r>' % self.id

    def to_dict(self):
        return {c.name: getattr(self, c.name, None) for c in self.__table__.columns}

    def display(self):
        return {
            'id': self.id,
            'name': self.name,
            'sign': self.sign,
            'path': self.path,
            'update_at': self.update_at
        }

    @classmethod
    def from_data(cls, data):
        update_at = int(time.time())
        _ = DataSource(**data)
        _.update_at = update_at
        return _


class DataOption(db.Model):
    __tablename__ = 'data_option'
    id = db.Column(SLBigInteger, primary_key=True)
    name = db.Column(db.String(20))
    enable = db.Column(db.Integer)
    update_at = db.Column(SLBigInteger)

    def __repr__(self):
        return '<DataOption %r>' % self.id

    def to_dict(self):
        return {c.name: getattr(self, c.name, None) for c in self.__table__.columns}


class DataResult(db.Model):
    __tablename__ = 'data_result'
    id = db.Column(SLBigInteger, primary_key=True)
    sign = db.Column(db.String(100))
    name = db.Column(db.String(20))
    result = db.Column(db.Text)
    state = db.Column(db.Integer)
    update_at = db.Column(SLBigInteger)

    def __repr__(self):
        return '<DataResult %r>' % self.id

    def to_dict(self):
        return {c.name: getattr(self, c.name, None) for c in self.__table__.columns}

    @classmethod
    def from_data(cls, data):
        update_at = int(time.time())
        _ = DataResult(**data)
        _.update_at = update_at
        return _

    def update(self, kwargs):
        update_at = int(time.time())
        kwargs['update_at'] = update_at
        for k, v in kwargs.items():
            setattr(self, k, v)
        return self


class AgeGroup(db.Model):
    __tablename__ = 'age_group'
    id = db.Column(SLBigInteger, primary_key=True)
    name = db.Column(db.String(20))
    group = db.Column(db.Text)
    sign = db.Column(db.String(100))
    update_at = db.Column(SLBigInteger)
    disabled = db.Column(db.Integer)

    def __repr__(self):
        return '<AgeGroup %r>' % self.id

    def to_dict(self):
        return {c.name: getattr(self, c.name, None) for c in self.__table__.columns}

    @classmethod
    def from_data(cls, data):
        update_at = int(time.time())
        _ = AgeGroup(**data)
        _.update_at = update_at
        return _

    def display(self):
        return {
            'id': self.id,
            'name': self.name,
            'sign': self.sign,
            'group': json.loads(self.group),
            'update_at': self.update_at,
            'disabled': self.disabled
        }

    def update(self, kwargs):
        update_at = int(time.time())
        kwargs['update_at'] = update_at
        kwargs['id'] = self.id
        for k, v in kwargs.items():
            setattr(self, k, v)
        return self


class AnalysisRecord(db.Model):
    __tablename__ = 'analysis_record'
    id = db.Column(SLBigInteger, primary_key=True)
    sign = db.Column(db.String(100))
    result = db.Column(db.Text)
    state = db.Column(db.Integer)  # 0 load source; 1 initializing ; 2  processing; 3 done; 99 error
    update_at = db.Column(SLBigInteger)

    def __repr__(self):
        return '<AnalysisRecord %r>' % self.id

    def to_dict(self):
        return {c.name: getattr(self, c.name, None) for c in self.__table__.columns}

    @classmethod
    def from_data(cls, data):
        update_at = int(time.time())
        _ = cls(**data)
        _.update_at = update_at
        return _

    def update(self, kwargs):
        update_at = int(time.time())
        kwargs['update_at'] = update_at
        for k, v in kwargs.items():
            setattr(self, k, v)
        return self
