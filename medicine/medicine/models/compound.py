from medicine.flask_app import db
from medicine.models import medicine
from medicine.models.medicine_compound import medicine_compound


class Compound(db.Model):  # 複方
    __tablename__ = 'compound'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    description = db.Column(db.String(1000))
    medicine = db.relationship('Medicine',
                               secondary=medicine_compound,
                               backref='compound',
                               cascade='all')

    def __repr__(self):
        return "Compound(%r)" % self.name
