# -*- coding: utf-8 -*-
from flask_sqlalchemy import SQLAlchemy as BaseSQLAlchemy
from contextlib import contextmanager


# 自定义一个SQLAlchemy继承flask_sqlalchemy的,方便自定义方法！！！
class SQLAlchemy(BaseSQLAlchemy):

    # 利用contextmanager管理器,对try/except语句封装，使用的时候必须和with结合！！！
    @contextmanager
    def auto_commit_db(self):
        try:
            yield
            self.session.commit()
        except Exception as e:
            # 加入数据库commit提交失败，必须回滚！！！
            self.session.rollback()
            raise e


db = SQLAlchemy()
