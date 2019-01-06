from app import db


class Column(db.Model):
    __tablename__ = "columns"

    id = db.Column(db.Integer(), primary_key=True)
    column_name = db.Column(db.String(80), nullable=False)
    column_type = db.Column(db.String(80), nullable=False)
    column_default = db.Column(db.String(80), nullable=True)
    is_nullable = db.Column(db.Boolean, nullable=False)
    is_autoincrement = db.Column(db.Boolean, nullable=False, default=False)
    is_pk = db.Column(db.Boolean, nullable=False, default=False)
    is_fk = db.Column(db.Boolean, nullable=False, default=False)
    table_id = db.Column(db.Integer, db.ForeignKey('tables.id'))
    table = db.relationship('Table')

    foreign_key = db.relationship('ForeignKey', backref=db.backref('foreign_key', lazy='joined', uselist=False),
                                  lazy='dynamic', foreign_keys='ForeignKey.column_id')

    def __init__(self, column_name, column_type, column_default, is_nullable, is_autoincrement=False, is_pk=False,
                 is_fk=False):
        self.column_name = column_name
        self.column_type = column_type
        self.column_default = column_default
        self.is_nullable = is_nullable
        self.is_autoincrement = is_autoincrement
        self.is_pk = is_pk
        self.is_fk = is_fk
        super(Column, self).__init__()

    def __str__(self):
        return self.column_name

    def __repr__(self):
        return '<Column %r>' % self.id

    @property
    def to_json(self):
        json_column = {
            'id': self.id,
            'column_name': self.column_name,
            'column_type': self.column_type,
            'column_default': self.column_default,
            'is_nullable': self.is_nullable,
            'is_autoincrement': self.is_autoincrement,
            'is_pk': self.is_pk,
            'is_fk': self.is_fk,
            'table_id': self.table_id
        }
        return json_column

    @property
    def to_dict(self):
        return {
            'id': self.id,
            'column_name': self.column_name,
            'column_type': self.column_type,
            'column_default': self.column_default,
            'is_nullable': self.is_nullable,
            'is_autoincrement': self.is_autoincrement,
            'is_pk': self.is_pk,
            'is_fk': self.is_fk,
            'table_id': self.table_id
        }

    def get_type(self):
        return self.column_type

    def is_primary(self):
        return self.is_pk

    def is_foreign(self):
        return self.is_fk
