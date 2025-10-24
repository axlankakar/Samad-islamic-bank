from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, Response
from flask_login import login_required
from ..models import User, Transaction
from .. import db
from decimal import Decimal
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import io

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/about')
def about():
    """About Us page - accessible to everyone"""
    return render_template('about.html')

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    users = User.query.all()
    total_system_balance = sum(user.balance for user in users if user.balance is not None)
    total_users = len(users)
    return render_template('admin_dashboard.html', 
                           total_system_balance=total_system_balance, 
                           total_users=total_users)

@admin_bp.route('/balances')
@login_required
def view_balances():
    users = User.query.order_by(User.name).all()
    total_system_balance = sum(user.balance for user in users if user.balance is not None)
    return render_template('view_balances.html', users=users, total_system_balance=total_system_balance)

@admin_bp.route('/users', methods=['GET', 'POST'])
@login_required
def manage_users():
    if request.method == 'POST':
        cnic = request.form.get('cnic')
        name = request.form.get('name')
        initial_amount_str = request.form.get('initial_amount')

        if not cnic or not name or not initial_amount_str:
            flash('CNIC, Name, and Initial Amount are required.', 'danger')
            return redirect(url_for('admin.manage_users'))

        existing_user = User.query.filter_by(cnic=cnic).first()
        if existing_user:
            flash(f'User with CNIC {cnic} already exists.', 'danger')
            return redirect(url_for('admin.manage_users'))
        
        try:
            initial_amount = Decimal(initial_amount_str)
            if initial_amount < 0:
                flash('Initial amount cannot be negative.', 'danger')
                return redirect(url_for('admin.manage_users'))
        except ValueError:
            flash('Invalid initial amount format.', 'danger')
            return redirect(url_for('admin.manage_users'))

        try:
            # First create and commit the user
            new_user = User(cnic=cnic, name=name, balance=initial_amount)
            db.session.add(new_user)
            db.session.commit()  # Commit to get the user ID
            
            # Now create the initial deposit transaction if needed
            if initial_amount > 0:
                initial_transaction = Transaction(
                    user_id=new_user.id,  # Now we have the user ID
                    transaction_type='credit',
                    amount=initial_amount,
                    description='Initial deposit'
                )
                db.session.add(initial_transaction)
                db.session.commit()  # Commit the transaction
                
            flash(f'User {name} ({cnic}) registered successfully with initial balance of {initial_amount}!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error registering user: {str(e)}', 'danger')
        
        return redirect(url_for('admin.manage_users'))

    users = User.query.all()
    return render_template('manage_users.html', users=users)

@admin_bp.route('/user/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        cnic = request.form.get('cnic')
        name = request.form.get('name')
        balance_str = request.form.get('balance')
        
        if not cnic or not name or not balance_str:
            flash('All fields are required.', 'danger')
            return redirect(url_for('admin.edit_user', user_id=user_id))
            
        # Check if CNIC is being changed and if it already exists
        if cnic != user.cnic and User.query.filter_by(cnic=cnic).first():
            flash(f'User with CNIC {cnic} already exists.', 'danger')
            return redirect(url_for('admin.edit_user', user_id=user_id))
            
        try:
            new_balance = Decimal(balance_str)
            if new_balance < 0:
                flash('Balance cannot be negative.', 'danger')
                return redirect(url_for('admin.edit_user', user_id=user_id))
                
            # If balance is changed, create a transaction to record the adjustment
            if new_balance != user.balance:
                adjustment = new_balance - user.balance
                transaction_type = 'credit' if adjustment > 0 else 'debit'
                transaction = Transaction(
                    user_id=user.id,
                    transaction_type=transaction_type,
                    amount=abs(adjustment),
                    description=f'Balance adjustment during user edit'
                )
                db.session.add(transaction)
                
            user.cnic = cnic
            user.name = name
            user.balance = new_balance
            
            db.session.commit()
            flash('User updated successfully!', 'success')
            return redirect(url_for('admin.manage_users'))
            
        except ValueError:
            flash('Invalid balance format.', 'danger')
            return redirect(url_for('admin.edit_user', user_id=user_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating user: {str(e)}', 'danger')
            return redirect(url_for('admin.edit_user', user_id=user_id))
    
    return render_template('edit_user.html', user=user)

@admin_bp.route('/user/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.balance > 0:
        flash('Cannot delete user with positive balance. Please transfer or withdraw their balance first.', 'danger')
        return redirect(url_for('admin.manage_users'))
        
    try:
        # Delete associated transactions first
        Transaction.query.filter_by(user_id=user.id).delete()
        Transaction.query.filter_by(related_user_id=user.id).delete()
        
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting user: {str(e)}', 'danger')
    
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/transactions')
@login_required
def view_transactions():
    transactions = Transaction.query.order_by(Transaction.timestamp.desc()).all()
    return render_template('view_transactions.html', transactions=transactions)

@admin_bp.route('/profit-distribution', methods=['GET', 'POST'])
@login_required
def distribute_profit():
    if request.method == 'POST':
        total_profit_str = request.form.get('total_profit')
        distribution_percentage_str = request.form.get('distribution_percentage')
        
        if not total_profit_str:
            flash('Total profit amount is required.', 'danger')
            return redirect(url_for('admin.distribute_profit'))
            
        if not distribution_percentage_str:
            flash('Distribution percentage is required.', 'danger')
            return redirect(url_for('admin.distribute_profit'))

        try:
            total_profit = Decimal(total_profit_str)
            if total_profit <= 0:
                flash('Total profit must be a positive amount.', 'danger')
                return redirect(url_for('admin.distribute_profit'))
        except ValueError:
            flash('Invalid total profit amount. Please enter a valid number.', 'danger')
            return redirect(url_for('admin.distribute_profit'))
            
        try:
            distribution_percentage = Decimal(distribution_percentage_str)
            if distribution_percentage <= 0 or distribution_percentage > 100:
                flash('Distribution percentage must be between 0 and 100.', 'danger')
                return redirect(url_for('admin.distribute_profit'))
        except ValueError:
            flash('Invalid distribution percentage. Please enter a valid number.', 'danger')
            return redirect(url_for('admin.distribute_profit'))

        users = User.query.all()
        if not users:
            flash('No users registered to distribute profit to.', 'warning')
            return redirect(url_for('admin.distribute_profit'))

        total_system_balance = sum(user.balance for user in users if user.balance is not None and user.balance > 0)

        if total_system_balance <= 0:
            flash('Cannot distribute profit as the total system balance of all users is zero or less.', 'danger')
            return redirect(url_for('admin.distribute_profit'))

        # Calculate the actual amount to distribute based on percentage
        amount_to_distribute = (total_profit * distribution_percentage) / 100

        try:
            for user in users:
                if user.balance is not None and user.balance > 0: # Distribute only to users with positive balance
                    user_profit_share = (user.balance / total_system_balance) * amount_to_distribute
                    user.balance += user_profit_share # Balance was already Decimal, direct addition is fine
                    
                    profit_transaction = Transaction(
                        user_id=user.id,
                        transaction_type='profit_distribution',
                        amount=user_profit_share,
                        description=f'Profit share ({user.balance/total_system_balance*100:.2f}%) from {distribution_percentage}% of total profit {total_profit:.2f}'
                    )
                    db.session.add(profit_transaction)
            
            db.session.commit()
            flash(f'{distribution_percentage}% of total profit ({amount_to_distribute:.2f}) distributed successfully among eligible users based on their balances.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error distributing profit: {str(e)}', 'danger')

        return redirect(url_for('admin.distribute_profit'))
    
    users = User.query.all()
    total_system_balance = sum(user.balance for user in users if user.balance is not None)
    return render_template('distribute_profit.html', total_system_balance=total_system_balance)

@admin_bp.route('/account-operations', methods=['GET', 'POST'])
@login_required
def account_operations():
    if request.method == 'POST':
        operation_type = request.form.get('operation_type')
        user_cnic = request.form.get('user_cnic')
        amount_str = request.form.get('amount')
        to_user_cnic = request.form.get('to_user_cnic')

        if not operation_type or not user_cnic or not amount_str:
            flash('Missing required fields for the operation.', 'danger')
            return redirect(url_for('admin.account_operations'))
        
        try:
            amount = Decimal(amount_str)
            if amount <= 0:
                flash('Amount must be positive.', 'danger')
                return redirect(url_for('admin.account_operations'))
        except ValueError:
            flash('Invalid amount.', 'danger')
            return redirect(url_for('admin.account_operations'))

        user = User.query.filter_by(cnic=user_cnic).first()
        if not user:
            flash(f'User with CNIC {user_cnic} not found.', 'danger')
            return redirect(url_for('admin.account_operations'))

        try:
            if operation_type == 'credit':
                user.balance = (user.balance or Decimal('0.00')) + amount
                desc = f'Credit operation of {amount:.2f}'
                trans = Transaction(user_id=user.id, transaction_type='credit', amount=amount, description=desc)
                db.session.add(trans)
                flash(f'Successfully credited {amount:.2f} to user {user.name}.', 'success')

            elif operation_type == 'debit':
                if (user.balance or Decimal('0.00')) < amount:
                    flash(f'Insufficient balance for user {user.name} to debit {amount:.2f}.', 'danger')
                    return redirect(url_for('admin.account_operations'))
                user.balance -= amount
                desc = f'Debit operation of {amount:.2f}'
                trans = Transaction(user_id=user.id, transaction_type='debit', amount=amount, description=desc)
                db.session.add(trans)
                flash(f'Successfully debited {amount:.2f} from user {user.name}.', 'success')

            elif operation_type == 'transfer':
                if not to_user_cnic:
                    flash('Recipient CNIC is required for transfer.', 'danger')
                    return redirect(url_for('admin.account_operations'))
                if user_cnic == to_user_cnic:
                    flash('Cannot transfer to the same account.', 'danger')
                    return redirect(url_for('admin.account_operations'))
                
                to_user = User.query.filter_by(cnic=to_user_cnic).first()
                if not to_user:
                    flash(f'Recipient user with CNIC {to_user_cnic} not found.', 'danger')
                    return redirect(url_for('admin.account_operations'))

                if (user.balance or Decimal('0.00')) < amount:
                    flash(f'Insufficient balance for user {user.name} to transfer {amount:.2f}.', 'danger')
                    return redirect(url_for('admin.account_operations'))
                
                user.balance -= amount
                to_user.balance = (to_user.balance or Decimal('0.00')) + amount

                desc_sender = f'Transfer out of {amount:.2f} to user {to_user.name} ({to_user.cnic})'
                trans_sender = Transaction(user_id=user.id, transaction_type='transfer_out', amount=amount, description=desc_sender, related_user_id=to_user.id)
                db.session.add(trans_sender)

                desc_receiver = f'Transfer in of {amount:.2f} from user {user.name} ({user.cnic})'
                trans_receiver = Transaction(user_id=to_user.id, transaction_type='transfer_in', amount=amount, description=desc_receiver, related_user_id=user.id)
                db.session.add(trans_receiver)
                flash(f'Successfully transferred {amount:.2f} from user {user.name} to user {to_user.name}.', 'success')
            
            else:
                flash('Invalid operation type.', 'danger')
                return redirect(url_for('admin.account_operations'))

            db.session.commit()

        except Exception as e:
            db.session.rollback()
            flash(f'Error performing operation: {str(e)}', 'danger')

        return redirect(url_for('admin.account_operations'))

    users = User.query.all()
    return render_template('account_operations.html', users=users)

def generate_user_statement_pdf(user, transactions):
    """Generate a PDF statement for a user"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1,  # Center alignment
        textColor=colors.darkblue
    )
    
    # Story (content) list
    story = []
    
    # Title
    story.append(Paragraph("Samad Islamic Banking System", title_style))
    story.append(Paragraph("Account Statement", styles['Heading2']))
    story.append(Spacer(1, 12))
    
    # User Information
    user_info = [
        ['Account Holder:', user.name],
        ['CNIC:', user.cnic],
        ['Current Balance:', f"{user.balance:.2f}"],
        ['Statement Date:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
    ]
    
    user_table = Table(user_info, colWidths=[2*inch, 3*inch])
    user_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (1, 0), (1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(user_table)
    story.append(Spacer(1, 20))
    
    # Transaction History
    story.append(Paragraph("Transaction History", styles['Heading3']))
    story.append(Spacer(1, 12))
    
    if transactions:
        # Prepare transaction data
        transaction_data = [['Date', 'Type', 'Amount', 'Description']]
        
        for trans in transactions:
            transaction_data.append([
                trans.timestamp.strftime('%Y-%m-%d %H:%M'),
                trans.transaction_type.replace('_', ' ').title(),
                f"{trans.amount:.2f}",
                trans.description or 'N/A'
            ])
        
        # Create transaction table
        trans_table = Table(transaction_data, colWidths=[1.2*inch, 1*inch, 1*inch, 2.8*inch])
        trans_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (3, 1), (3, -1), 'LEFT'),  # Left align description column
        ]))
        
        story.append(trans_table)
    else:
        story.append(Paragraph("No transactions found.", styles['Normal']))
    
    story.append(Spacer(1, 20))
    
    # Footer
    story.append(Paragraph("This statement is generated by Samad Islamic Banking System", 
                          ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, alignment=1)))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

@admin_bp.route('/download-statement/<int:user_id>')
@login_required
def download_statement(user_id):
    """Download user statement as PDF"""
    user = User.query.get_or_404(user_id)
    
    # Get user transactions ordered by timestamp (newest first)
    transactions = Transaction.query.filter_by(user_id=user_id).order_by(Transaction.timestamp.desc()).all()
    
    # Generate PDF
    pdf_buffer = generate_user_statement_pdf(user, transactions)
    
    # Create filename
    filename = f"Statement_{user.name}_{user.cnic}_{datetime.now().strftime('%Y%m%d')}.pdf"
    
    return Response(
        pdf_buffer.getvalue(),
        mimetype='application/pdf',
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
    ) 