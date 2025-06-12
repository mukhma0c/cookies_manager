from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Customer, Order

customers_bp = Blueprint('customers', __name__, url_prefix='/customers')

@customers_bp.route('/')
def list_customers():
    """Display list of all customers."""
    customers = Customer.query.order_by(Customer.name).all()
    return render_template('customers/list.html', customers=customers)

@customers_bp.route('/<int:customer_id>/edit', methods=['GET', 'POST'])
def edit_customer(customer_id):
    """Edit a customer."""
    customer = Customer.query.get_or_404(customer_id)
    
    if request.method == 'POST':
        customer.name = request.form.get('name')
        customer.customer_type = request.form.get('customer_type')
        customer.phone = request.form.get('phone')
        customer.notes = request.form.get('notes')
        
        db.session.commit()
        flash(f'Customer "{customer.name}" updated successfully.', 'success')
        return redirect(url_for('customers.list_customers'))
        
    return render_template('customers/edit.html', customer=customer)

@customers_bp.route('/<int:customer_id>/delete', methods=['POST'])
def delete_customer(customer_id):
    """Delete a customer."""
    customer = Customer.query.get_or_404(customer_id)
    
    # Check if customer has orders
    has_orders = Order.query.filter_by(customer_id=customer_id).first() is not None
    
    if has_orders:
        flash(f'Cannot delete customer "{customer.name}" because they have orders.', 'danger')
        return redirect(url_for('customers.list_customers'))
    
    try:
        name = customer.name
        db.session.delete(customer)
        db.session.commit()
        flash(f'Customer "{name}" deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting customer: {str(e)}', 'danger')
    
    return redirect(url_for('customers.list_customers'))
