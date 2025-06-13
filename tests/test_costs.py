import pytest
from app import create_app
from models import db, Ingredient, Packaging, Purchase
from cost_helpers import (
    get_latest_unit_cost,
    calculate_ingredient_cost,
    calculate_packaging_cost,
    calculate_order_cost_preview
)


@pytest.fixture
def app():
    """Create and configure a Flask app for testing."""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def test_data(app):
    """Create test data for cost calculations."""
    with app.app_context():
        # Create ingredients
        flour = Ingredient(
            name='Flour',
            default_unit='g',
            default_price_per_unit_cents=5  # 5 cents per gram
        )
        sugar = Ingredient(
            name='Sugar',
            default_unit='g',
            default_price_per_unit_cents=8  # 8 cents per gram
        )
        
        # Create packaging
        box = Packaging(
            name='Small Box',
            default_unit='pcs',
            default_price_per_unit_cents=50  # 50 cents per piece
        )
        
        db.session.add_all([flour, sugar, box])
        db.session.commit()
        
        # Create purchases
        flour_purchase = Purchase(
            item_type='ingredient',
            item_id=flour.id,
            quantity=1000,  # 1kg
            unit='g',
            total_cost_cents=4000  # $40.00
        )
        flour_purchase.calculate_unit_cost()  # 4000 millicents per gram (4 cents)
        
        sugar_purchase = Purchase(
            item_type='ingredient',
            item_id=sugar.id,
            quantity=500,  # 500g
            unit='g',
            total_cost_cents=3500  # $35.00
        )
        sugar_purchase.calculate_unit_cost()  # 7000 millicents per gram (7 cents)
        
        box_purchase = Purchase(
            item_type='packaging',
            item_id=box.id,
            quantity=10,
            unit='pcs',
            total_cost_cents=400  # $4.00
        )
        box_purchase.calculate_unit_cost()  # 40000 millicents per piece (40 cents)
        
        db.session.add_all([flour_purchase, sugar_purchase, box_purchase])
        db.session.commit()
        
        return {
            'flour': flour,
            'sugar': sugar,
            'box': box
        }


def test_get_latest_unit_cost(app, test_data):
    """Test getting the latest unit cost for items."""
    with app.app_context():
        # Test ingredient cost
        flour_cost = get_latest_unit_cost('ingredient', test_data['flour'].id)
        assert flour_cost == 4000  # 4000 millicents per gram (4 cents)
        
        sugar_cost = get_latest_unit_cost('ingredient', test_data['sugar'].id)
        assert sugar_cost == 7000  # 7000 millicents per gram (7 cents)
        
        # Test packaging cost
        box_cost = get_latest_unit_cost('packaging', test_data['box'].id)
        assert box_cost == 40000  # 40000 millicents per piece (40 cents)
        
        # Test non-existent item
        nonexistent_cost = get_latest_unit_cost('ingredient', 999)
        assert nonexistent_cost is None


def test_calculate_ingredient_cost(app, test_data):
    """Test calculating ingredient costs."""
    with app.app_context():
        # Test with purchases
        flour_cost = calculate_ingredient_cost(test_data['flour'].id, 200)  # 200g of flour
        assert flour_cost == 800  # 200g * 4 cents = 800 cents = $8.00
        
        sugar_cost = calculate_ingredient_cost(test_data['sugar'].id, 50)  # 50g of sugar
        assert sugar_cost == 350  # 50g * 7 cents = 350 cents = $3.50
        
        # Test non-existent ingredient
        assert calculate_ingredient_cost(999, 100) is None
        
        # Create a new ingredient without purchases to test fallback to default price
        with db.session.begin_nested():
            vanilla = Ingredient(
                name='Vanilla Extract',
                default_unit='ml',
                default_price_per_unit_cents=20  # 20 cents per ml
            )
            db.session.add(vanilla)
        
        vanilla_cost = calculate_ingredient_cost(vanilla.id, 5)  # 5ml of vanilla
        assert vanilla_cost == 100  # 5ml * 20 cents = 100 cents = $1.00


def test_calculate_packaging_cost(app, test_data):
    """Test calculating packaging costs."""
    with app.app_context():
        # Test with purchases
        box_cost = calculate_packaging_cost(test_data['box'].id, 2)  # 2 boxes
        assert box_cost == 80  # 2 boxes * 40 cents = 80 cents = $0.80
        
        # Test non-existent packaging
        assert calculate_packaging_cost(999, 1) is None
        
        # Create a new packaging without purchases to test fallback to default price
        with db.session.begin_nested():
            ribbon = Packaging(
                name='Ribbon',
                default_unit='m',
                default_price_per_unit_cents=15  # 15 cents per meter
            )
            db.session.add(ribbon)
        
        ribbon_cost = calculate_packaging_cost(ribbon.id, 0.5)  # 0.5m of ribbon
        assert ribbon_cost == 8  # 0.5m * 15 cents = 7.5 cents, rounded to 8 cents


def test_calculate_order_cost_preview(app, test_data):
    """Test calculating order cost preview."""
    with app.app_context():
        # Define ingredients and packaging for the order
        ingredients = [
            {'id': test_data['flour'].id, 'amount': 250},  # 250g of flour
            {'id': test_data['sugar'].id, 'amount': 100}   # 100g of sugar
        ]
        packaging = [
            {'id': test_data['box'].id, 'quantity': 3}     # 3 boxes
        ]
        
        # Calculate cost preview
        preview = calculate_order_cost_preview(ingredients, packaging)
        
        # Expected costs:
        # Flour: 250g * 4 cents = 1000 cents
        # Sugar: 100g * 7 cents = 700 cents
        # Total ingredients: 1700 cents
        # Boxes: 3 boxes * 40 cents = 120 cents
        # Total cost: 1700 + 120 = 1820 cents = $18.20
        
        assert preview['ingredient_cost_cents'] == 1700
        assert preview['packaging_cost_cents'] == 120
        assert preview['total_cost_cents'] == 1820
