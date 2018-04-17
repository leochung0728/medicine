from medicine import db

class Property(db.Model):  # 性
    __tablename__ = 'property'

    id = db.Column(db.Integer, primary_key=True)
    cold = db.Column(db.Integer)  # 寒
    cool = db.Column(db.Integer)  # 涼
    warm = db.Column(db.Integer)  # 溫
    hot = db.Column(db.Integer)  # 熱
    neutral = db.Column(db.Integer)  # 平
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicine.id'))
    # medicine = db.relationship("Medicine", back_populates='property')
