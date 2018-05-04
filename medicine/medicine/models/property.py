from medicine.flask_app import db


class Property(db.Model):  # 性
    __tablename__ = 'property'

    id = db.Column(db.Integer, primary_key=True)
    position = db.Column(db.String(20))  # 部位

    cold = db.Column(db.Integer)  # 寒
    cool = db.Column(db.Integer)  # 涼
    warm = db.Column(db.Integer)  # 溫
    hot = db.Column(db.Integer)  # 熱
    neutral = db.Column(db.Integer)  # 平

    sour = db.Column(db.Integer)  # 酸
    sweet = db.Column(db.Integer)  # 甘
    bitter = db.Column(db.Integer)  # 苦
    salty = db.Column(db.Integer)  # 鹹
    pungent = db.Column(db.Integer)  # 辣

    poison = db.Column(db.Integer)  # 毒

    medicine_id = db.Column(db.Integer, db.ForeignKey('medicine.id'))
    # medicine = db.relationship("Medicine", back_populates='property')

    @staticmethod
    def get(position, medicine_id=None):
        property = None
        if medicine_id is not None:
            property = Property.query.filter_by(position=position, medicine_id=medicine_id).first()
        return property

    def __repr__(self):
        return "Property(%r, %r)" % (self.position, self.medicine_id)