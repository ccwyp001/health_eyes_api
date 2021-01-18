# -*- coding: utf-8 -*-

from ..extensions import db, SLBigInteger, Geometry, LongText
import time


class Icd10Data(db.Model):
    __tablename__ = 'icd10'
    id = db.Column(SLBigInteger, primary_key=True)
    level = db.Column(db.Integer)
    code = db.Column(db.String(20))
    name = db.Column(db.String(100))
    d_code = db.Column(db.String(20))
    type = db.Column(db.String(100))
    parent_code = db.Column(db.String(20))
    inputcode1 = db.Column(db.String(20))
    inputcode2 = db.Column(db.String(20))
    update_at = db.Column(SLBigInteger)

    def __repr__(self):
        return '<Icd10Data %r>' % self.name

    def to_dict(self):
        return {c.name: getattr(self, c.name, None) for c in self.__table__.columns}

    def display(self):
        return {
            'name': self.name,
            'code': self.code,
            'level': self.level,
            'inputcode1': self.inputcode1,
            'inputcode2': self.inputcode2,
            'parent_code': self.parent_code,
        }

    @staticmethod
    def new(kwargs):
        update_at = int(time.time())
        _ = Icd10Data(**kwargs)
        _.update_at = update_at
        return _

    def update(self, kwargs):
        update_at = int(time.time())
        kwargs['update_at'] = update_at
        for k, v in kwargs.items():
            setattr(self, k, v)
        return self
