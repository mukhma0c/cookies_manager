from flask import Blueprint, render_template, request, jsonify, Response, current_app
from models import db, Order, OrderIngredient, OrderPackaging, Customer, Recipe, Ingredient, Packaging
from sqlalchemy import func, desc
from datetime import datetime, timedelta
import csv
import io
from collections import defaultdict

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

@reports_bp.route('/')
def index():
    """Reports dashboard index page."""
    # Get summary metrics
    orders_count = Order.query.count()
    
    # Profit calculations - use separate queries to avoid duplication
    # Get total revenue
    total_revenue_cents = db.session.query(func.sum(Order.sale_price_total_cents)).scalar() or 0
    
    # Get total ingredient costs
    total_ingredient_cost_cents = db.session.query(
        func.sum(OrderIngredient.cost_at_time_of_use_cents)
    ).scalar() or 0
    
    # Get total packaging costs
    total_packaging_cost_cents = db.session.query(
        func.sum(OrderPackaging.cost_at_time_of_use_cents)
    ).scalar() or 0
    
    # Calculate totals
    total_cost_cents = total_ingredient_cost_cents + total_packaging_cost_cents
    total_profit_cents = total_revenue_cents - total_cost_cents
    
    # Calculate profit margin percentage
    profit_margin = 0
    if total_revenue_cents > 0:
        profit_margin = (total_profit_cents / total_revenue_cents) * 100
    
    # Total cookies baked
    total_cookies = db.session.query(func.sum(Order.quantity_baked)).scalar() or 0
    
    # Top customers
    top_customers = db.session.query(
        Customer.name,
        func.count(Order.id).label('order_count'),
        func.sum(Order.sale_price_total_cents).label('revenue')
    ).join(Order).group_by(Customer.id).order_by(desc('revenue')).limit(5).all()
    
    # Top recipes
    top_recipes = db.session.query(
        Recipe.name,
        func.count(Order.id).label('order_count')
    ).join(Order).group_by(Recipe.id).order_by(desc('order_count')).limit(5).all()
    
    return render_template('reports/index.html',
                          orders_count=orders_count,
                          total_revenue_cents=total_revenue_cents,
                          total_cost_cents=total_cost_cents,
                          total_profit_cents=total_profit_cents,
                          profit_margin=profit_margin,
                          total_cookies=total_cookies,
                          top_customers=top_customers,
                          top_recipes=top_recipes)

@reports_bp.route('/profit')
def profit_report():
    """Detailed profit analysis report."""
    # Get time range filters
    period = request.args.get('period', 'all')
    
    # Calculate date ranges
    today = datetime.now().date()
    start_date = None
    end_date = today + timedelta(days=1)  # Include today
    
    if period == 'month':
        start_date = today.replace(day=1)
    elif period == '3months':
        start_date = (today - timedelta(days=90))
    elif period == '6months':
        start_date = (today - timedelta(days=180))
    elif period == 'year':
        start_date = today.replace(month=1, day=1)
    
    # Get orders
    orders_query = Order.query
    if start_date:
        orders_query = orders_query.filter(Order.order_date >= start_date, Order.order_date <= end_date)
    orders = orders_query.order_by(Order.order_date.desc()).all()
    
    # Initialize totals
    total_revenue = 0
    total_ingredient_cost = 0
    total_packaging_cost = 0
    orders_data = []
    
    # Process each order
    for order in orders:
        # Get ingredient costs for this order
        ingredient_cost = db.session.query(
            func.sum(OrderIngredient.cost_at_time_of_use_cents)
        ).filter(OrderIngredient.order_id == order.id).scalar() or 0
        
        # Get packaging costs for this order
        packaging_cost = db.session.query(
            func.sum(OrderPackaging.cost_at_time_of_use_cents)
        ).filter(OrderPackaging.order_id == order.id).scalar() or 0
        
        # Calculate profit
        total_cost = ingredient_cost + packaging_cost
        profit = order.sale_price_total_cents - total_cost
        profit_margin_pct = 0
        if order.sale_price_total_cents > 0:
            profit_margin_pct = (profit / order.sale_price_total_cents) * 100
        
        # Add to totals
        total_revenue += order.sale_price_total_cents
        total_ingredient_cost += ingredient_cost
        total_packaging_cost += packaging_cost
        
        # Add to orders data
        orders_data.append({
            'id': order.id,
            'date': order.order_date,
            'customer': order.customer,
            'recipe': order.recipe.name if order.recipe else 'Custom',
            'quantity': order.quantity_baked,
            'revenue_cents': order.sale_price_total_cents,
            'ingredient_cost_cents': ingredient_cost,
            'packaging_cost_cents': packaging_cost,
            'total_cost_cents': total_cost,
            'profit_cents': profit,
            'profit_margin': profit_margin_pct
        })
    
    # Calculate totals
    total_cost = total_ingredient_cost + total_packaging_cost
    total_profit = total_revenue - total_cost
    
    # Calculate profit margin
    profit_margin = 0
    if total_revenue > 0:
        profit_margin = (total_profit / total_revenue) * 100
    
    # Format data for the template
    orders_data = []
    for item in orders:
        order = item.Order
        ingredient_cost = item.ingredient_cost or 0
        packaging_cost = item.packaging_cost or 0
        total_cost = ingredient_cost + packaging_cost
        profit = order.sale_price_total_cents - total_cost
        profit_margin_pct = 0
        if order.sale_price_total_cents > 0:
            profit_margin_pct = (profit / order.sale_price_total_cents) * 100
        
        orders_data.append({
            'id': order.id,
            'date': order.order_date,
            'customer': order.customer.name if order.customer else 'N/A',
            'recipe': order.recipe.name if order.recipe else 'Custom',
            'quantity': order.quantity_baked,
            'revenue_cents': order.sale_price_total_cents,
            'ingredient_cost_cents': ingredient_cost,
            'packaging_cost_cents': packaging_cost,
            'total_cost_cents': total_cost,
            'profit_cents': profit,
            'profit_margin': profit_margin_pct
        })
    
    return render_template('reports/profit.html',
                          orders=orders_data,
                          period=period,
                          total_revenue=total_revenue,
                          total_ingredient_cost=total_ingredient_cost,
                          total_packaging_cost=total_packaging_cost,
                          total_cost=total_cost,
                          total_profit=total_profit,
                          profit_margin=profit_margin)

@reports_bp.route('/inventory')
def inventory_report():
    """Inventory usage and cost report."""
    period = request.args.get('period', 'all')
    
    # Calculate date ranges
    today = datetime.now().date()
    start_date = None
    end_date = today + timedelta(days=1)  # Include today
    
    if period == 'month':
        start_date = today.replace(day=1)
    elif period == '3months':
        start_date = (today - timedelta(days=90))
    elif period == '6months':
        start_date = (today - timedelta(days=180))
    elif period == 'year':
        start_date = today.replace(month=1, day=1)
    
    # Query for ingredient usage
    ingredient_query = db.session.query(
        Ingredient.id,
        Ingredient.name,
        Ingredient.default_unit,
        func.sum(OrderIngredient.amount_used).label('amount_used'),
        func.sum(OrderIngredient.cost_at_time_of_use_cents).label('total_cost')
    ).join(OrderIngredient).join(Order)
    
    # Apply date filters if specified
    if start_date:
        ingredient_query = ingredient_query.filter(Order.order_date >= start_date, Order.order_date <= end_date)
    
    # Group and order results
    ingredients = ingredient_query.group_by(Ingredient.id).order_by(desc('total_cost')).all()
    
    # Query for packaging usage
    packaging_query = db.session.query(
        Packaging.id,
        Packaging.name,
        Packaging.default_unit,
        func.sum(OrderPackaging.quantity_used).label('quantity_used'),
        func.sum(OrderPackaging.cost_at_time_of_use_cents).label('total_cost')
    ).join(OrderPackaging).join(Order)
    
    # Apply date filters if specified
    if start_date:
        packaging_query = packaging_query.filter(Order.order_date >= start_date, Order.order_date <= end_date)
    
    # Group and order results
    packaging = packaging_query.group_by(Packaging.id).order_by(desc('total_cost')).all()
    
    return render_template('reports/inventory.html',
                          ingredients=ingredients,
                          packaging=packaging,
                          period=period)

@reports_bp.route('/trends')
def trend_report():
    """Trend analysis over time."""
    period = request.args.get('period', 'year')
    
    # Calculate date ranges
    today = datetime.now().date()
    if period == 'year':
        start_date = today.replace(month=1, day=1)
        group_by = 'month'
    elif period == 'month':
        start_date = today.replace(day=1)
        group_by = 'day'
    elif period == 'all':
        # Use the date of the first order
        first_order = Order.query.order_by(Order.order_date).first()
        if first_order:
            start_date = first_order.order_date.date()
        else:
            start_date = today.replace(month=1, day=1)
        group_by = 'month'
    else:
        start_date = today - timedelta(days=90)
        group_by = 'week'
    
    end_date = today + timedelta(days=1)  # Include today
    
    # Build the query based on the grouping
    if group_by == 'month':
        date_extract = func.strftime('%Y-%m', Order.order_date)
    elif group_by == 'week':
        date_extract = func.strftime('%Y-%W', Order.order_date)
    else:  # day
        date_extract = func.strftime('%Y-%m-%d', Order.order_date)
    
    # Get revenue by time period
    revenue_data = db.session.query(
        date_extract.label('period'),
        func.sum(Order.sale_price_total_cents).label('revenue')
    ).filter(Order.order_date >= start_date, Order.order_date <= end_date) \
     .group_by('period').order_by('period').all()
    
    # Get costs by time period
    cost_data = db.session.query(
        date_extract.label('period'),
        func.sum(OrderIngredient.cost_at_time_of_use_cents).label('ingredient_cost'),
        func.sum(OrderPackaging.cost_at_time_of_use_cents).label('packaging_cost')
    ).join(OrderIngredient, Order.id == OrderIngredient.order_id, isouter=True) \
     .join(OrderPackaging, Order.id == OrderPackaging.order_id, isouter=True) \
     .filter(Order.order_date >= start_date, Order.order_date <= end_date) \
     .group_by('period').order_by('period').all()
    
    # Combine data
    trend_data = []
    cost_by_period = {item.period: (item.ingredient_cost or 0, item.packaging_cost or 0) for item in cost_data}
    
    for item in revenue_data:
        period = item.period
        revenue = item.revenue
        ingredient_cost, packaging_cost = cost_by_period.get(period, (0, 0))
        total_cost = ingredient_cost + packaging_cost
        profit = revenue - total_cost
        
        # Format display label based on grouping
        if group_by == 'month':
            # Convert YYYY-MM to Month YYYY
            display_period = datetime.strptime(period, '%Y-%m').strftime('%b %Y')
        elif group_by == 'week':
            # Convert YYYY-WW to Week WW, YYYY
            year, week = period.split('-')
            display_period = f"Week {week}, {year}"
        else:
            # Convert YYYY-MM-DD to Mon DD, YYYY
            display_period = datetime.strptime(period, '%Y-%m-%d').strftime('%b %d, %Y')
        
        trend_data.append({
            'period': period,
            'display_period': display_period,
            'revenue': revenue,
            'ingredient_cost': ingredient_cost,
            'packaging_cost': packaging_cost,
            'total_cost': total_cost,
            'profit': profit
        })
    
    # Get cookie count data
    cookie_data = db.session.query(
        date_extract.label('period'),
        func.sum(Order.quantity_baked).label('cookies')
    ).filter(Order.order_date >= start_date, Order.order_date <= end_date) \
     .group_by('period').order_by('period').all()
    
    cookies_by_period = {item.period: item.cookies for item in cookie_data}
    
    # Add cookie data to trend data
    for item in trend_data:
        item['cookies'] = cookies_by_period.get(item['period'], 0)
    
    return render_template('reports/trends.html',
                          trend_data=trend_data,
                          period=period,
                          group_by=group_by)

@reports_bp.route('/api/trend-data')
def api_trend_data():
    """API endpoint for trend chart data."""
    period = request.args.get('period', 'year')
    
    # Calculate date ranges
    today = datetime.now().date()
    if period == 'year':
        start_date = today.replace(month=1, day=1)
        group_by = 'month'
    elif period == 'month':
        start_date = today.replace(day=1)
        group_by = 'day'
    elif period == 'all':
        # Use the date of the first order
        first_order = Order.query.order_by(Order.order_date).first()
        if first_order:
            start_date = first_order.order_date.date()
        else:
            start_date = today.replace(month=1, day=1)
        group_by = 'month'
    else:
        start_date = today - timedelta(days=90)
        group_by = 'week'
    
    end_date = today + timedelta(days=1)  # Include today
    
    # Build the query based on the grouping
    if group_by == 'month':
        date_extract = func.strftime('%Y-%m', Order.order_date)
    elif group_by == 'week':
        date_extract = func.strftime('%Y-%W', Order.order_date)
    else:  # day
        date_extract = func.strftime('%Y-%m-%d', Order.order_date)
    
    # Get revenue by time period
    revenue_data = db.session.query(
        date_extract.label('period'),
        func.sum(Order.sale_price_total_cents).label('revenue')
    ).filter(Order.order_date >= start_date, Order.order_date <= end_date) \
     .group_by('period').order_by('period').all()
    
    # Get ingredient costs by time period
    ingredient_cost_data = db.session.query(
        date_extract.label('period'),
        func.sum(OrderIngredient.cost_at_time_of_use_cents).label('ingredient_cost')
    ).select_from(OrderIngredient).join(Order) \
     .filter(Order.order_date >= start_date, Order.order_date <= end_date) \
     .group_by('period').order_by('period').all()
    
    # Get packaging costs by time period
    packaging_cost_data = db.session.query(
        date_extract.label('period'),
        func.sum(OrderPackaging.cost_at_time_of_use_cents).label('packaging_cost')
    ).select_from(OrderPackaging).join(Order) \
     .filter(Order.order_date >= start_date, Order.order_date <= end_date) \
     .group_by('period').order_by('period').all()
    
    # Get cookie count data
    cookie_data = db.session.query(
        date_extract.label('period'),
        func.sum(Order.quantity_baked).label('cookies')
    ).filter(Order.order_date >= start_date, Order.order_date <= end_date) \
     .group_by('period').order_by('period').all()
    
    # Prepare data for charts
    periods = []
    revenue = []
    costs = []
    profits = []
    cookies = []
    
    # Create dictionaries for quick lookup
    ingredient_costs_by_period = {item.period: (item.ingredient_cost or 0) for item in ingredient_cost_data}
    packaging_costs_by_period = {item.period: (item.packaging_cost or 0) for item in packaging_cost_data}
    cookies_by_period = {item.period: item.cookies for item in cookie_data}
    
    for item in revenue_data:
        period = item.period
        rev = item.revenue or 0
        ingredient_cost = ingredient_costs_by_period.get(period, 0)
        packaging_cost = packaging_costs_by_period.get(period, 0)
        total_cost = ingredient_cost + packaging_cost
        profit = rev - total_cost
        cookie_count = cookies_by_period.get(period, 0)
        
        # Format display label based on grouping
        if group_by == 'month':
            # Convert YYYY-MM to Month YYYY
            display_period = datetime.strptime(period, '%Y-%m').strftime('%b %Y')
        elif group_by == 'week':
            # Convert YYYY-WW to Week WW, YYYY
            year, week = period.split('-')
            display_period = f"Week {week}, {year}"
        else:
            # Convert YYYY-MM-DD to Mon DD, YYYY
            display_period = datetime.strptime(period, '%Y-%m-%d').strftime('%b %d')
        
        periods.append(display_period)
        revenue.append(rev / 100)  # Convert cents to dollars
        costs.append(total_cost / 100)
        profits.append(profit / 100)
        cookies.append(cookie_count)
    
    # Format data for Chart.js
    chart_data = {
        'labels': periods,
        'datasets': [
            {
                'label': 'Revenue',
                'data': revenue,
                'borderColor': 'rgba(54, 162, 235, 1)',
                'backgroundColor': 'rgba(54, 162, 235, 0.2)',
                'borderWidth': 2,
                'fill': True
            },
            {
                'label': 'Costs',
                'data': costs,
                'borderColor': 'rgba(255, 99, 132, 1)',
                'backgroundColor': 'rgba(255, 99, 132, 0.2)',
                'borderWidth': 2,
                'fill': True
            },
            {
                'label': 'Profit',
                'data': profits,
                'borderColor': 'rgba(75, 192, 192, 1)',
                'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                'borderWidth': 2,
                'fill': True
            }
        ]
    }
    
    cookie_chart_data = {
        'labels': periods,
        'datasets': [
            {
                'label': 'Cookies Baked',
                'data': cookies,
                'borderColor': 'rgba(255, 159, 64, 1)',
                'backgroundColor': 'rgba(255, 159, 64, 0.2)',
                'borderWidth': 2,
                'fill': True
            }
        ]
    }
    
    return jsonify({
        'financialChart': chart_data,
        'cookieChart': cookie_chart_data
    })

@reports_bp.route('/export/profit-csv')
def export_profit_csv():
    """Export profit data as CSV."""
    period = request.args.get('period', 'all')
    
    # Calculate date ranges
    today = datetime.now().date()
    start_date = None
    end_date = today + timedelta(days=1)  # Include today
    
    if period == 'month':
        start_date = today.replace(day=1)
    elif period == '3months':
        start_date = (today - timedelta(days=90))
    elif period == '6months':
        start_date = (today - timedelta(days=180))
    elif period == 'year':
        start_date = today.replace(month=1, day=1)
    
    # Base query
    query = db.session.query(
        Order,
        func.sum(OrderIngredient.cost_at_time_of_use_cents).label('ingredient_cost'),
        func.sum(OrderPackaging.cost_at_time_of_use_cents).label('packaging_cost')
    ).join(OrderIngredient, Order.id == OrderIngredient.order_id, isouter=True) \
     .join(OrderPackaging, Order.id == OrderPackaging.order_id, isouter=True) \
     .group_by(Order.id)
    
    # Apply date filters if specified
    if start_date:
        query = query.filter(Order.order_date >= start_date, Order.order_date <= end_date)
    
    # Execute query
    orders = query.order_by(Order.order_date.desc()).all()
    
    # Create CSV file in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'Order ID', 'Date', 'Customer', 'Recipe', 'Quantity',
        'Revenue ($)', 'Ingredient Cost ($)', 'Packaging Cost ($)', 
        'Total Cost ($)', 'Profit ($)', 'Profit Margin (%)'
    ])
    
    # Write data rows
    for item in orders:
        order = item.Order
        ingredient_cost = item.ingredient_cost or 0
        packaging_cost = item.packaging_cost or 0
        total_cost = ingredient_cost + packaging_cost
        profit = order.sale_price_total_cents - total_cost
        profit_margin_pct = 0
        if order.sale_price_total_cents > 0:
            profit_margin_pct = (profit / order.sale_price_total_cents) * 100
        
        writer.writerow([
            order.id,
            order.order_date.strftime('%Y-%m-%d'),
            order.customer.name if order.customer else 'N/A',
            order.recipe.name if order.recipe else 'Custom',
            order.quantity_baked,
            "{:.2f}".format(order.sale_price_total_cents / 100),
            "{:.2f}".format(ingredient_cost / 100),
            "{:.2f}".format(packaging_cost / 100),
            "{:.2f}".format(total_cost / 100),
            "{:.2f}".format(profit / 100),
            "{:.2f}".format(profit_margin_pct)
        ])
    
    # Prepare response
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=profit_report_{period}_{today.strftime('%Y%m%d')}.csv"}
    )

@reports_bp.route('/export/inventory-csv')
def export_inventory_csv():
    """Export inventory usage data as CSV."""
    period = request.args.get('period', 'all')
    
    # Calculate date ranges
    today = datetime.now().date()
    start_date = None
    end_date = today + timedelta(days=1)  # Include today
    
    if period == 'month':
        start_date = today.replace(day=1)
    elif period == '3months':
        start_date = (today - timedelta(days=90))
    elif period == '6months':
        start_date = (today - timedelta(days=180))
    elif period == 'year':
        start_date = today.replace(month=1, day=1)
    
    # Query for ingredient usage
    ingredient_query = db.session.query(
        Ingredient.id,
        Ingredient.name,
        Ingredient.default_unit,
        func.sum(OrderIngredient.amount_used).label('amount_used'),
        func.sum(OrderIngredient.cost_at_time_of_use_cents).label('total_cost')
    ).join(OrderIngredient).join(Order)
    
    # Apply date filters if specified
    if start_date:
        ingredient_query = ingredient_query.filter(Order.order_date >= start_date, Order.order_date <= end_date)
    
    # Group and order results
    ingredients = ingredient_query.group_by(Ingredient.id).order_by(desc('total_cost')).all()
    
    # Query for packaging usage
    packaging_query = db.session.query(
        Packaging.id,
        Packaging.name,
        Packaging.default_unit,
        func.sum(OrderPackaging.quantity_used).label('quantity_used'),
        func.sum(OrderPackaging.cost_at_time_of_use_cents).label('total_cost')
    ).join(OrderPackaging).join(Order)
    
    # Apply date filters if specified
    if start_date:
        packaging_query = packaging_query.filter(Order.order_date >= start_date, Order.order_date <= end_date)
    
    # Group and order results
    packaging = packaging_query.group_by(Packaging.id).order_by(desc('total_cost')).all()
    
    # Create CSV file in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write ingredients section
    writer.writerow(['INGREDIENTS'])
    writer.writerow(['ID', 'Name', 'Unit', 'Amount Used', 'Total Cost ($)'])
    
    for ingredient in ingredients:
        writer.writerow([
            ingredient.id,
            ingredient.name,
            ingredient.default_unit,
            "{:.2f}".format(ingredient.amount_used),
            "{:.2f}".format(ingredient.total_cost / 100)
        ])
    
    # Add a blank row between sections
    writer.writerow([])
    
    # Write packaging section
    writer.writerow(['PACKAGING'])
    writer.writerow(['ID', 'Name', 'Unit', 'Quantity Used', 'Total Cost ($)'])
    
    for item in packaging:
        writer.writerow([
            item.id,
            item.name,
            item.default_unit,
            "{:.2f}".format(item.quantity_used),
            "{:.2f}".format(item.total_cost / 100)
        ])
    
    # Prepare response
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=inventory_report_{period}_{today.strftime('%Y%m%d')}.csv"}
    )

@reports_bp.route('/export/trends-csv')
def export_trends_csv():
    """Export trend data as CSV."""
    period = request.args.get('period', 'year')
    
    # Calculate date ranges
    today = datetime.now().date()
    if period == 'year':
        start_date = today.replace(month=1, day=1)
        group_by = 'month'
    elif period == 'month':
        start_date = today.replace(day=1)
        group_by = 'day'
    elif period == 'all':
        # Use the date of the first order
        first_order = Order.query.order_by(Order.order_date).first()
        if first_order:
            start_date = first_order.order_date.date()
        else:
            start_date = today.replace(month=1, day=1)
        group_by = 'month'
    else:
        start_date = today - timedelta(days=90)
        group_by = 'week'
    
    end_date = today + timedelta(days=1)  # Include today
    
    # Build the query based on the grouping
    if group_by == 'month':
        date_extract = func.strftime('%Y-%m', Order.order_date)
    elif group_by == 'week':
        date_extract = func.strftime('%Y-%W', Order.order_date)
    else:  # day
        date_extract = func.strftime('%Y-%m-%d', Order.order_date)
    
    # Get revenue by time period
    revenue_data = db.session.query(
        date_extract.label('period'),
        func.sum(Order.sale_price_total_cents).label('revenue')
    ).filter(Order.order_date >= start_date, Order.order_date <= end_date) \
     .group_by('period').order_by('period').all()
    
    # Get costs by time period
    cost_data = db.session.query(
        date_extract.label('period'),
        func.sum(OrderIngredient.cost_at_time_of_use_cents).label('ingredient_cost'),
        func.sum(OrderPackaging.cost_at_time_of_use_cents).label('packaging_cost')
    ).join(OrderIngredient, Order.id == OrderIngredient.order_id, isouter=True) \
     .join(OrderPackaging, Order.id == OrderPackaging.order_id, isouter=True) \
     .filter(Order.order_date >= start_date, Order.order_date <= end_date) \
     .group_by('period').order_by('period').all()
    
    # Get cookie count data
    cookie_data = db.session.query(
        date_extract.label('period'),
        func.sum(Order.quantity_baked).label('cookies')
    ).filter(Order.order_date >= start_date, Order.order_date <= end_date) \
     .group_by('period').order_by('period').all()
    
    # Create dictionaries for quick lookup
    cost_by_period = {item.period: (item.ingredient_cost or 0, item.packaging_cost or 0) for item in cost_data}
    cookies_by_period = {item.period: item.cookies for item in cookie_data}
    
    # Create CSV file in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'Period', 'Revenue ($)', 'Ingredient Cost ($)', 
        'Packaging Cost ($)', 'Total Cost ($)', 'Profit ($)', 
        'Cookies Baked'
    ])
    
    # Write data rows
    for item in revenue_data:
        period = item.period
        revenue = item.revenue or 0
        ingredient_cost, packaging_cost = cost_by_period.get(period, (0, 0))
        total_cost = ingredient_cost + packaging_cost
        profit = revenue - total_cost
        cookie_count = cookies_by_period.get(period, 0)
        
        # Format display label based on grouping
        if group_by == 'month':
            # Convert YYYY-MM to Month YYYY
            display_period = datetime.strptime(period, '%Y-%m').strftime('%b %Y')
        elif group_by == 'week':
            # Convert YYYY-WW to Week WW, YYYY
            year, week = period.split('-')
            display_period = f"Week {week}, {year}"
        else:
            # Convert YYYY-MM-DD to Mon DD, YYYY
            display_period = datetime.strptime(period, '%Y-%m-%d').strftime('%b %d, %Y')
        
        writer.writerow([
            display_period,
            "{:.2f}".format(revenue / 100),
            "{:.2f}".format(ingredient_cost / 100),
            "{:.2f}".format(packaging_cost / 100),
            "{:.2f}".format(total_cost / 100),
            "{:.2f}".format(profit / 100),
            cookie_count
        ])
    
    # Prepare response
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=trends_report_{period}_{today.strftime('%Y%m%d')}.csv"}
    )
