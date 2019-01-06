import pprint

from app import db
from sqlalchemy import create_engine, MetaData


class Color:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


def without_color():
    Color.PURPLE = ''
    Color.CYAN = ''
    Color.DARKCYAN = ''
    Color.BLUE = ''
    Color.GREEN = ''
    Color.YELLOW = ''
    Color.RED = ''
    Color.BOLD = ''
    Color.UNDERLINE = ''
    Color.END = ''


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

    def get_remote_metadata(self):
        return MetaData(self.get_sqla_engine, reflect=True)

    def get_remote_tables(self):
        return self.get_remote_metadata().sorted_tables

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

    def get_number_of_tables(self):
        return len(self.tables)

    def get_tables(self):
        return self.tables

    def get_column_with_this_name(self, name):
        for table in self.tables:
            for column in table.get_columns():
                if column.column_name == name:
                    return column

    def get_table_by_name(self, table_name):
        for table in self.tables:
            if table.table_name == table_name:
                return table

    def get_tables_into_dictionary(self):
        data = {}
        for table in self.tables:
            data[table.name] = []
            for column in table.get_columns():
                data[table.table_name].append(column.column_name)
        return data

    def get_primary_keys_by_table(self):
        data = {}
        for table in self.tables:
            data[table.table_name] = table.get_primary_keys()
        return data

    def get_foreign_keys_by_table(self):
        data = {}
        for table in self.tables:
            data[table.table_name] = table.get_foreign_keys()
        return data

    def get_primary_keys_of_table(self, table_name):
        for table in self.tables:
            if table.table_name == table_name:
                return table.get_primary_keys()

    def get_primary_key_names_of_table(self, table_name):
        for table in self.tables:
            if table.table_name == table_name:
                return table.get_primary_key_names()

    def get_foreign_keys_of_table(self, table_name):
        for table in self.tables:
            if table.table_name == table_name:
                return table.get_foreign_keys()

    def get_foreign_key_names_of_table(self, table_name):
        for table in self.tables:
            if table.table_name == table_name:
                return table.get_foreign_key_names()

    def print_me(self):
        for table in self.tables:
            print('+-------------------------------------+')
            print("| %25s           |" % (table.table_name.upper()))
            print('+-------------------------------------+')
            for column in table.columns:
                if column.is_primary():
                    print("| 🔑 %31s           |" % (
                            Color.BOLD + column.column_name + ' (' + column.get_type() + ')' + Color.END))
                elif column.is_foreign():
                    print("| #️⃣ %31s           |" % (
                            Color.BOLD + column.column_name + ' (' + column.get_type() + ')' + Color.END))
                else:
                    print("|   %23s           |" % (column.column_name + ' (' + column.get_type() + ')'))
            print('+-------------------------------------+\n')
