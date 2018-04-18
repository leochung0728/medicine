from .tools.session import session_scope
from medicine.flask_app import db
from  medicine.models import alias, property, compound
from medicine.models.medicine_compound import medicine_compound


class Medicine(db.Model):  # 中藥
    __tablename__ = 'medicine'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False, unique=True)
    radical = db.Column(db.String(20))
    alias = db.relationship('Alias', backref='medicine', cascade='all, delete-orphan')
    property = db.relationship('Property', backref='medicine', cascade='all, delete-orphan')
    compound = db.relationship('Compound',
                               secondary=medicine_compound,
                               backref='medicine',
                               cascade='all')

    def __init__(self, name, radical='', alias=[], property=[], compound=[]):
        self.name = name
        self.radical = radical
        self.alias = alias
        self.property = property
        self.compound = compound

    @staticmethod
    def get(name):
        me = Medicine.query.filter_by(name=name).first()
        if me is None:
            me = Medicine(name=name)
        return me

    def save_or_update(self):
        with session_scope() as session:
            me = Medicine.query.filter_by(name=self.name).first()
            if me is not None:
                me.name = self.name
                me.radical = self.radical
                me.alias = self.alias
                me.property = self.property
                me.compound = self.compound
                db.session.add(me)
            else:
                session.add(self)

    def __repr__(self):
        return "Medicine(%r, %r)" % (self.name, self.radical)
