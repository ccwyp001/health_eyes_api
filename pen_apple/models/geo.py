# -*- coding: utf-8 -*-

from ..extensions import db, SLBigInteger, LongText
from ..commons.geo_object import GeoObject
import time


class GeoData(db.Model):
    __tablename__ = 'geo'
    id = db.Column(SLBigInteger, primary_key=True)
    min_x = db.Column(db.DECIMAL(20, 15))
    min_y = db.Column(db.DECIMAL(20, 15))
    max_x = db.Column(db.DECIMAL(20, 15))
    max_y = db.Column(db.DECIMAL(20, 15))
    label_x = db.Column(db.DECIMAL(20, 15))
    label_y = db.Column(db.DECIMAL(20, 15))
    oid = db.Column(db.String(30))
    name = db.Column(db.String(20))
    object_id = db.Column(db.String(30))
    village = db.Column(db.String(30))
    center_x = db.Column(db.DECIMAL(20, 15))
    center_y = db.Column(db.DECIMAL(20, 15))
    code = db.Column(db.String(20))
    city = db.Column(db.String(20))
    town = db.Column(db.String(20))
    address = db.Column(db.String(30))
    section_type = db.Column(db.String(30))
    province = db.Column(db.String(30))
    fullname = db.Column(db.String(30), unique=True)
    county = db.Column(db.String(20))
    geometry = db.Column(LongText)
    parent_id = db.Column(SLBigInteger, db.ForeignKey('geo.id'), nullable=True)
    parent = db.relationship('GeoData', backref='children', lazy='select', remote_side=[id])
    update_at = db.Column(SLBigInteger)

    def __repr__(self):
        return '<GeoData %r>' % self.name

    def to_dict(self):
        return {c.name: getattr(self, c.name, None) for c in self.__table__.columns}

    def display(self):
        return {
            'type': 'Feature',
            'properties': {
                'name': self.name,
                'fullname': self.fullname,
                'center': [self.center_x, self.center_y],
                'bound': [[self.max_x, self.max_y], [self.min_x, self.min_y]],
                'children': [_.display() for _ in self.children] if self.children else [],
            },
            'geometry': GeoObject(self.geometry).rawgeojson()
        }

    def display_with_trans(self):
        return {
            'key': self.id,
            'name': self.name,
            'fullname': self.fullname,
            'trans': [_.display() for _ in self.trans] if self.trans else [],
        }

    @staticmethod
    def new(kwargs):
        update_at = int(time.time())
        _ = GeoData(**kwargs)
        _.update_at = update_at
        return _

    def update(self, kwargs):
        update_at = int(time.time())
        kwargs['update_at'] = update_at
        for k, v in kwargs.items():
            setattr(self, k, v)
        return self

    @classmethod
    def from_data(cls, data):
        pass


class GeoTransData(db.Model):
    __tablename__ = 'geo_trans'
    id = db.Column(SLBigInteger, primary_key=True)
    name = db.Column(db.String(20))
    fullname = db.Column(db.String(30), unique=True)
    geo_name = db.Column(db.String(30), db.ForeignKey('geo.fullname'), nullable=True)
    type = db.Column(db.Integer)  # 1 merger, 2 alias
    enabled = db.Column(db.Integer, default=1)  # 1 enabled 0 not
    geo_data = db.relationship('GeoData', backref='trans', lazy='select')
    update_at = db.Column(SLBigInteger)

    def __repr__(self):
        return '<GeoTransData %r>' % self.name

    def to_dict(self):
        return {c.name: getattr(self, c.name, None) for c in self.__table__.columns}

    def display(self):
        return {
            'name': self.name,
            'fullname': self.fullname,
            'type': self.type,
            'enabled': self.enabled,
            'update_at': self.update_at,
        }

    @staticmethod
    def new(kwargs):
        update_at = int(time.time())
        _ = GeoTransData(**kwargs)
        _.update_at = update_at
        return _

    def update(self, kwargs):
        update_at = int(time.time())
        kwargs['update_at'] = update_at
        for k, v in kwargs.items():
            setattr(self, k, v)
        return self

    @classmethod
    def from_data(cls, data):
        pass
