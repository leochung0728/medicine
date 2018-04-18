from medicine.flask_app import db
from medicine.models import medicine
from medicine.models.medicine_compound import medicine_compound


class Compound(db.Model):  # 複方
    __tablename__ = 'compound'

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200))
    # medicine = db.relationship('Medicine',
    #                            secondary=medicine_compound,
    #                            backref='compound')
