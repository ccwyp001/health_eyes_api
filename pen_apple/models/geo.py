# -*- coding: utf-8 -*-

from ..extensions import db, SLBigInteger, Geometry
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
    geometry = db.Column(Geometry)
    parent_id = db.Column(SLBigInteger)
    update_at = db.Column(SLBigInteger)

    def __repr__(self):
        return '<GeoData %r>' % self.name

    def to_dict(self):
        return {c.name: getattr(self, c.name, None) for c in self.__table__.columns}

    def display(self):
        return {}

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
