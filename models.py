from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func

db = SQLAlchemy()

class Ingredient(db.Model):
    """Model for ingredients used in recipes."""
    __tablename__ = 'ingredients'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    image_path = db.Column(db.String(255))
    default_unit = db.Column(db.String(10), nullable=False)  # 'g', 'ml', 'pcs'
    default_price_per_unit_cents = db.Column(db.Integer)
    low_stock_threshold = db.Column(db.Float, default=0)
    notes = db.Column(db.Text)
    
    # Relationships
    recipe_ingredients = db.relationship('RecipeIngredient', back_populates='ingredient', cascade='all, delete-orphan')
    order_ingredients = db.relationship('OrderIngredient', back_populates='ingredient')
    order_ingredient_overrides = db.relationship('OrderIngredientOverride', back_populates='ingredient')
    
    def __repr__(self):
        return f'<Ingredient {self.name}>'


class Packaging(db.Model):
    """Model for packaging materials used for cookies."""
    __tablename__ = 'packaging'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    image_path = db.Column(db.String(255))
    default_unit = db.Column(db.String(10), nullable=False)  # usually 'pcs'
    default_price_per_unit_cents = db.Column(db.Integer)
    low_stock_threshold = db.Column(db.Float, default=0)
    notes = db.Column(db.Text)
    
    # Relationships
    order_packaging = db.relationship('OrderPackaging', back_populates='packaging')
    
    def __repr__(self):
        return f'<Packaging {self.name}>'


class Customer(db.Model):
    """Model for customers who order cookies."""
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, primary_key=True)
    display_name = db.Column(db.String(100), nullable=False, unique=True)
    type = db.Column(db.String(10), db.CheckConstraint("type IN ('person', 'store')"))
    phone = db.Column(db.String(20))
    notes = db.Column(db.Text)
    
    # Relationships
    orders = db.relationship('Order', back_populates='customer')
    
    def __repr__(self):
        return f'<Customer {self.display_name}>'


class Recipe(db.Model):
    """Model for cookie recipes."""
    __tablename__ = 'recipes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    cookie_size = db.Column(db.String(10), db.CheckConstraint("cookie_size IN ('mini', 'regular', 'large')"))
    dough_weight_per_cookie_g = db.Column(db.Float, nullable=False)
    yield_cookies = db.Column(db.Integer)  # standard batch yield
    notes = db.Column(db.Text)
    image_path = db.Column(db.String(255))
    
    # Relationships
    ingredients = db.relationship('RecipeIngredient', back_populates='recipe', cascade='all, delete-orphan')
    orders = db.relationship('Order', back_populates='recipe')
    
    def __repr__(self):
        return f'<Recipe {self.name}>'


class RecipeIngredient(db.Model):
    """Association model between recipes and ingredients."""
    __tablename__ = 'recipe_ingredients'
    
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id', ondelete='CASCADE'), primary_key=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredients.id'), primary_key=True)
    quantity = db.Column(db.Float, nullable=False)  # in recipe's default unit
    
    # Relationships
    recipe = db.relationship('Recipe', back_populates='ingredients')
    ingredient = db.relationship('Ingredient', back_populates='recipe_ingredients')
    
    def __repr__(self):
        return f'<RecipeIngredient {self.recipe_id}:{self.ingredient_id}>'


class Purchase(db.Model):
    """Model for ingredient and packaging purchases."""
    __tablename__ = 'purchases'
    
    id = db.Column(db.Integer, primary_key=True)
    purchase_date = db.Column(db.Date, default=datetime.utcnow().date)
    item_type = db.Column(db.String(10), db.CheckConstraint("item_type IN ('ingredient', 'packaging')"))
    item_id = db.Column(db.Integer, nullable=False)  # FK resolved in app layer
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(10), nullable=False)
    total_cost_cents = db.Column(db.Integer, nullable=False)
    unit_cost_cents = db.Column(db.Integer)  # Generated column in app layer
    notes = db.Column(db.Text)
    
    def __repr__(self):
        return f'<Purchase {self.id} - {self.item_type}:{self.item_id}>'
    
    def calculate_unit_cost(self):
        """Calculate unit cost from total cost and quantity."""
        if self.quantity and self.total_cost_cents:
            self.unit_cost_cents = round(self.total_cost_cents / self.quantity)


class Order(db.Model):
    """Model for cookie orders."""
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'))  # optional template
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    cookie_size = db.Column(db.String(10), db.CheckConstraint("cookie_size IN ('mini', 'regular', 'large')"))
    dough_weight_g = db.Column(db.Float, nullable=False)
    quantity_ordered = db.Column(db.Integer, nullable=False)
    quantity_baked = db.Column(db.Integer, nullable=False)
    quantity_kept_family = db.Column(db.Integer, default=0)
    sale_price_total_cents = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text)
    
    # Relationships
    customer = db.relationship('Customer', back_populates='orders')
    recipe = db.relationship('Recipe', back_populates='orders')
    ingredients = db.relationship('OrderIngredient', back_populates='order', cascade='all, delete-orphan')
    packaging = db.relationship('OrderPackaging', back_populates='order', cascade='all, delete-orphan')
    ingredient_overrides = db.relationship('OrderIngredientOverride', back_populates='order', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Order {self.id} - {self.customer.display_name if self.customer else "Unknown"}>'
    
    @property
    def ingredient_cost_cents(self):
        """Calculate total ingredient cost for this order."""
        return sum(oi.cost_at_time_of_use_cents for oi in self.ingredients)
    
    @property
    def packaging_cost_cents(self):
        """Calculate total packaging cost for this order."""
        return sum(op.cost_at_time_of_use_cents for op in self.packaging)
    
    @property
    def total_cost_cents(self):
        """Calculate total cost for this order."""
        return self.ingredient_cost_cents + self.packaging_cost_cents
    
    @property
    def profit_cents(self):
        """Calculate profit for this order."""
        return self.sale_price_total_cents - self.total_cost_cents
    
    @property
    def profit_margin(self):
        """Calculate profit margin percentage for this order."""
        if self.sale_price_total_cents == 0:
            return 0
        return (self.profit_cents / self.sale_price_total_cents) * 100


class OrderIngredient(db.Model):
    """Model for ingredients used in an order with cost snapshot."""
    __tablename__ = 'order_ingredients'
    
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), primary_key=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredients.id'), primary_key=True)
    amount_used = db.Column(db.Float, nullable=False)
    cost_at_time_of_use_cents = db.Column(db.Integer, nullable=False)
    
    # Relationships
    order = db.relationship('Order', back_populates='ingredients')
    ingredient = db.relationship('Ingredient', back_populates='order_ingredients')
    
    def __repr__(self):
        return f'<OrderIngredient {self.order_id}:{self.ingredient_id}>'


class OrderPackaging(db.Model):
    """Model for packaging used in an order with cost snapshot."""
    __tablename__ = 'order_packaging'
    
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), primary_key=True)
    packaging_id = db.Column(db.Integer, db.ForeignKey('packaging.id'), primary_key=True)
    quantity_used = db.Column(db.Float, nullable=False)
    cost_at_time_of_use_cents = db.Column(db.Integer, nullable=False)
    
    # Relationships
    order = db.relationship('Order', back_populates='packaging')
    packaging = db.relationship('Packaging', back_populates='order_packaging')
    
    def __repr__(self):
        return f'<OrderPackaging {self.order_id}:{self.packaging_id}>'


class OrderIngredientOverride(db.Model):
    """Model for ingredient overrides in an order."""
    __tablename__ = 'order_ingredient_overrides'
    
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), primary_key=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredients.id'), primary_key=True)
    new_amount = db.Column(db.Float, nullable=False)
    
    # Relationships
    order = db.relationship('Order', back_populates='ingredient_overrides')
    ingredient = db.relationship('Ingredient', back_populates='order_ingredient_overrides')
    
    def __repr__(self):
        return f'<OrderIngredientOverride {self.order_id}:{self.ingredient_id}>'
