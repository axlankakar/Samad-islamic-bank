from .. import db
from decimal import Decimal

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cnic = db.Column(db.String(15), unique=True, nullable=False) # Assuming CNIC format like XXXXX-XXXXXXX-X
    name = db.Column(db.String(100), nullable=False)
    balance = db.Column(db.Numeric(15, 2), default=Decimal('0.00'))

    # Relationships
    transactions = db.relationship('Transaction', backref='user', lazy=True, foreign_keys='Transaction.user_id')

    def __repr__(self):
        return f'<User {self.cnic} - {self.name}>' 