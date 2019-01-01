import pprint

from app import db
from sqlalchemy import create_engine, MetaData

from app.models.table import Table


class Database(db.Model):
    __tablename__ = "databases"

    id = db.Column(db.Integer(), primary_key=True)
    dbtype = db.Column(db.String(80), nullable=False)
    username = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(80), nullable=False)
    hostname = db.Column(db.String(80), nullable=False, )
    dbname = db.Column(db.String(80), nullable=False)

    tables = db.relationship('Table', backref=db.backref('databases', lazy='joined'), lazy='dynamic')

    def __init__(self, dbtype, username, password, hostname, dbname):
        self.dbtype = dbtype
        self.username = username
        self.password = password
        self.hostname = hostname
        self.dbname = dbname
        super(Database, self).__init__()

    def __str__(self):
        return self.dbtype + "://" + self.username + ":" + self.password + "@" + self.hostname + "/" + self.dbname

    def __repr__(self):
        return '<Database %r>' % self.id

    @property
    def get_sqlalchemy_uri(self):
        return self.get_sqlalchemy_driver + "://" + self.username + ":" + self.password + "@" + self.hostname + "/" \
               + self.dbname

    @property
    def get_sqla_engine(self):
        url = self.get_sqlalchemy_uri
        return create_engine(url)

    @property
    def get_remote_metadata(self):
        return MetaData(self.get_sqla_engine, reflect=True)

    @property
    def get_remote_tables(self):
        return self.get_remote_metadata.sorted_tables

    @property
    def to_json(self):
        json_database = {
            'id': self.id,
            'sqla_url': self.get_sqlalchemy_uri,
            'username': self.username,
            'password': self.password,
            'host': self.hostname,
            'dbname': self.dbname,
            'tables': [table.to_json for table in self.tables]
        }
        return json_database

    @property
    def get_sqlalchemy_driver(self):
        if self.dbtype == 'mysql':
            return 'mysql'
        elif self.dbtype == 'mssql':
            return 'mssql+pymssql'
        elif self.dbtype == 'postgresql':
            return 'postgresql+psycopg2'
        else:
            return None
