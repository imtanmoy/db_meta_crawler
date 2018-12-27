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

    @property
    def save_remote_columns(self):
        new_columns = []
        for column in self.get_remote_columns:
            ncol = Column(column_name=getattr(column, 'name'),
                          column_type=getattr((getattr(column, 'type')), '__visit_name__'),
                          column_default=getattr(column, 'default'),
                          is_nullable=getattr(column, 'nullable'),
                          is_autoincrement=False if getattr(column, 'autoincrement') == 'auto' else True,
                          is_pk=getattr(column, 'primary_key'))
            self.columns.append(ncol)
            db.session.add(ncol)
            db.session.commit()
            new_columns.append(ncol)
            fks = getattr(column, 'foreign_keys')
            if len(fks) > 0:
                parent = str(getattr(next(iter(fks)), '_colspec')).split('.')[0]
                parent_table = Table.query.filter_by(table_name=parent, database_id=self.database_id).first()
                scol = Column.query.filter_by(column_name=ncol.column_name, table_id=parent_table.id).first()
                fk_key = ForeignKey(column_id=ncol.id, table_id=ncol.table_id, referred_column_id=scol.id,
                                    referred_table_id=scol.table_id)
                db.session.add(fk_key)
                db.session.commit()
        return new_columns
