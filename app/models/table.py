from app import db
from app.models.column import Column
from app.models.foreignkey import ForeignKey


class Table(db.Model):
    __tablename__ = "tables"

    id = db.Column(db.Integer(), primary_key=True)
    table_name = db.Column(db.String(80), nullable=False)
    database_id = db.Column(db.Integer, db.ForeignKey('databases.id'))
    database = db.relationship('Database')

    columns = db.relationship('Column', backref=db.backref('tables', lazy='joined'), lazy='dynamic')

    relations = db.relationship('ForeignKey', backref=db.backref('relations', lazy='joined'), lazy='dynamic',
                                foreign_keys='ForeignKey.table_id')
    referred_relations = db.relationship('ForeignKey', backref=db.backref('referred_relations', lazy='joined'),
                                         lazy='dynamic',
                                         foreign_keys='ForeignKey.referred_table_id')

    def __init__(self, table_name):
        self.table_name = table_name
        super(Table, self).__init__()

    def __str__(self):
        return self.table_name

    def __repr__(self):
        return '<Table %r>' % self.id

    @property
    def to_json(self):
        json_table = {
            'id': self.id,
            'table_name': self.table_name,
            'database_id': self.database_id,
            'columns': [column.to_json for column in self.columns],
            'relations': [relation.to_json for relation in self.relations],
            'referred_relations': [referred_relation.to_json for referred_relation in self.referred_relations]
        }
        return json_table

    @property
    def get_db(self):
        return self.database

    @property
    def get_remote_db_metadata(self):
        return self.database.get_remote_metadata

    @property
    def get_remote_columns(self):
        return self.get_remote_db_metadata.tables[self.table_name].columns

    def get_number_of_columns(self):
        return len(self.columns)

    def get_columns(self):
        return self.columns

    def get_column_by_name(self, column_name):
        for column in self.columns:
            if column.column_name == column_name:
                return column

    def get_primary_keys(self):
        primary_keys = []
        for column in self.columns:
            if column.is_primary():
                primary_keys.append(column)
        return primary_keys

    def get_primary_key_names(self):
        primary_keys = []
        for column in self.columns:
            if column.is_primary():
                primary_keys.append(column.column_name)
        return primary_keys

    def get_foreign_keys(self):
        foreign_keys = []
        for column in self.columns:
            if column.is_foreign():
                foreign_keys.append(column)
        return foreign_keys

    def get_foreign_key_names(self):
        foreign_keys = []
        for column in self.columns:
            if column.is_foreign():
                foreign_keys.append(column.column_name)
        return foreign_keys
