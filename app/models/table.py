from app import db


class Table(db.Model):
    __tablename__ = "tables"

    id = db.Column(db.Integer(), primary_key=True)
    table_name = db.Column(db.String(80), nullable=False)
    database_id = db.Column(db.Integer, db.ForeignKey('databases.id'))
    database = db.relationship('Database')

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
            'database_id': self.database_id
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
