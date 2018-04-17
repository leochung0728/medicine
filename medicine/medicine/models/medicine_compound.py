from medicine import db
# from medicine.models import medicine, compound

medicine_compound = db.Table('medicine_compound',
                             db.Column('medicine_id', db.Integer, db.ForeignKey('medicine.id'), primary_key=True),
                             db.Column('compound_id', db.Integer, db.ForeignKey('compound.id'), primary_key=True))
