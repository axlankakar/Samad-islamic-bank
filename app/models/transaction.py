from .. import db
from datetime import datetime
from decimal import Decimal

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    transaction_type = db.Column(db.String(50), nullable=False)  # e.g., 'credit', 'debit', 'profit_distribution', 'transfer_out', 'transfer_in'
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.String(255), nullable=True) # Optional description
    related_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # For transfers, to link the other user

    related_user = db.relationship('User', foreign_keys=[related_user_id])

    def __repr__(self):
        return f'<Transaction {self.id} - {self.transaction_type} - User {self.user_id} - Amount {self.amount}>' 