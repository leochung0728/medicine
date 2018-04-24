from medicine.flask_app import db


class Alias(db.Model):  # 別名
    __tablename__ = 'alias'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicine.id'), nullable=False)

    @staticmethod
    def get(name, medicine_id=None):
        alias =None
        if medicine_id is None:
            alias = Alias.query.filter_by(name=name).first()
        else:
            alias = Alias.query.filter_by(name=name, medicine_id=medicine_id).first()
        return alias

    def __repr__(self):
        return "Alias(%r)" % self.name
