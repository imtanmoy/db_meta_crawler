from app import db


class ForeignKey(db.Model):
    __tablename__ = "foreign_keys"

    id = db.Column(db.Integer(), primary_key=True)

    column_id = db.Column(db.Integer, db.ForeignKey('columns.id'))
    column = db.relationship('Column', foreign_keys='ForeignKey.column_id')

    table_id = db.Column(db.Integer, db.ForeignKey('tables.id'))
    table = db.relationship('Table', foreign_keys='ForeignKey.table_id')

    referred_column_id = db.Column(db.Integer, db.ForeignKey('columns.id'))
    referred_column = db.relationship('Column', foreign_keys='ForeignKey.referred_column_id')

    referred_table_id = db.Column(db.Integer, db.ForeignKey('tables.id'))
    referred_table = db.relationship('Table', foreign_keys='ForeignKey.referred_table_id')

    def __init__(self, column_id, table_id, referred_column_id, referred_table_id):
        self.column_id = column_id
        self.table_id = table_id
        self.referred_column_id = referred_column_id
        self.referred_table_id = referred_table_id
        super(ForeignKey, self).__init__()

    def __str__(self):
        return self.id

    def __repr__(self):
        return '<ForeignKey %r>' % self.id

    @property
    def to_json(self):
        json_column = {
            'id': self.id,
            'column_id': self.column_id,
            'table_id': self.table_id,
            'referred_column_id': self.referred_column_id,
            'referred_table_id': self.referred_table_id
        }
        return json_column
