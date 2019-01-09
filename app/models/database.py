from sqlalchemy.engine.reflection import Inspector
from sqlalchemy import create_engine, MetaData, select, exc
from sqlalchemy.orm import validates

from app import db

DATABASE_TYPES = {
    'mysql': 'mysql',
    'mssql': 'mssql+pymssql',
    'postgresql': 'postgresql+psycopg2'
}

DatabaseStatusTypes = ('pending', 'processed', 'failed')


class Database(db.Model):
    __tablename__ = "databases"

    id = db.Column(db.Integer(), primary_key=True)
    dbtype = db.Column(db.String(80), nullable=False)
    username = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(80), nullable=False)
    hostname = db.Column(db.String(80), nullable=False)
    dbname = db.Column(db.String(80), nullable=False)
    status = db.Column(db.Enum(*DatabaseStatusTypes), default=DatabaseStatusTypes[0], nullable=False,
                       server_default=DatabaseStatusTypes[0])

    tables = db.relationship('Table', backref=db.backref('databases', lazy='joined', cascade="all,delete"),
                             lazy='dynamic')

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

    @validates('dbtype')
    def validate_dbtype(self, key, dbtype):
        if not dbtype or len(dbtype) < 1:
            raise AssertionError('No Database Type provided')
        if dbtype not in DATABASE_TYPES:
            raise AssertionError('Database Type is not Supported')
        return dbtype

    @validates('username')
    def validate_username(self, key, username):
        if not username or len(username) < 1:
            raise AssertionError('No username provided')
        return username

    @validates('password')
    def validate_password(self, key, password):
        if not password or len(password) < 1:
            raise AssertionError('No password provided')
        return password

    @validates('hostname')
    def validate_hostname(self, key, hostname):
        if not hostname or len(hostname) < 1:
            raise AssertionError('No hostname provided')
        return hostname

    @validates('dbname')
    def validate_dbname(self, key, dbname):
        if not dbname or len(dbname) < 1:
            raise AssertionError('No database name provided')
        return dbname

    @property
    def get_sqlalchemy_uri(self):
        return self.get_sqlalchemy_driver + "://" + self.username + ":" + self.password + "@" + self.hostname + "/" \
               + self.dbname

    def get_sqla_engine(self, **kwargs):
        url = self.get_sqlalchemy_uri
        return create_engine(url, pool_recycle=3600, pool_pre_ping=True, pool_timeout=30,
                             connect_args=kwargs)

    def get_remote_inspector(self):
        return Inspector.from_engine(self.get_sqla_engine())

    def get_remote_metadata(self):
        return MetaData(self.get_sqla_engine(), reflect=True)

    def get_remote_tables(self):
        insp = self.get_remote_inspector()
        tables = []
        for tt in insp.get_sorted_table_and_fkc_names(schema=insp.default_schema_name):
            if tt[0] is not None:
                tables.append(tt[0])
        return tables

    def get_remote_columns(self, table_name):
        insp = self.get_remote_inspector()
        return insp.get_columns(table_name=table_name, schema=insp.default_schema_name)

    def get_remote_primary_keys(self, table_name):
        insp = self.get_remote_inspector()
        return insp.get_primary_keys(table_name=table_name, schema=insp.default_schema_name)

    def get_remote_foreign_keys(self, table_name):
        insp = self.get_remote_inspector()
        return insp.get_foreign_keys(table_name=table_name, schema=insp.default_schema_name)

    @property
    def to_json(self):
        json_database = {
            'id': self.id,
            'sqla_url': self.get_sqlalchemy_uri,
            'username': self.username,
            'password': self.password,
            'host': self.hostname,
            'dbname': self.dbname,
            'tables': [table.to_json for table in self.tables],
            'status': self.status
        }
        return json_database

    @property
    def get_sqlalchemy_driver(self):
        if self.dbtype in DATABASE_TYPES:
            return DATABASE_TYPES[self.dbtype]

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

    def ping_connection(self):
        if self.dbtype == 'mysql':
            engine = self.get_sqla_engine(connect_timeout=10)
        elif self.dbtype == 'mssql':
            engine = self.get_sqla_engine(login_timeout=10, timeout=10)
        elif self.dbtype == 'postgresql':
            engine = self.get_sqla_engine(connect_timeout=10)
        else:
            engine = self.get_sqla_engine()
        connection = engine.connect()
        save_should_close_with_result = connection.should_close_with_result
        connection.should_close_with_result = False

        try:
            return connection.scalar(select([1]))
        except exc.DBAPIError as err:
            if err.connection_invalidated:
                connection.scalar(select([1]))
            else:
                raise
        finally:
            # restore "close with result"
            connection.should_close_with_result = save_should_close_with_result
            connection.close()
            engine.dispose()
