"""
Seed script to populate the database with initial data.
"""
from app import create_app
from models import db, Customer, Ingredient, Packaging, Recipe, RecipeIngredient

def seed_database():
    """Populate the database with initial data."""
    # Create all tables if they don't exist
    db.create_all()
    """Populate the database with initial data."""
    print("Seeding database with initial data...")
    
    # Add customers
    customers = [
        Customer(name="Smith Family", customer_type="family", notes="Regular customers"),
        Customer(name="Jane Doe", customer_type="friend", notes="Close friend"),
        Customer(name="Downtown Bakery", customer_type="store", phone="555-1234", notes="Village grocery store")
    ]
    db.session.add_all(customers)
    db.session.commit()
    print(f"Added {len(customers)} customers")
    
    # Add ingredients
    ingredients = [
        Ingredient(name="All-Purpose Flour", default_unit="g", default_price_per_unit_cents=4, low_stock_threshold=500),
        Ingredient(name="Granulated Sugar", default_unit="g", default_price_per_unit_cents=6, low_stock_threshold=400),
        Ingredient(name="Brown Sugar", default_unit="g", default_price_per_unit_cents=8, low_stock_threshold=300),
        Ingredient(name="Butter", default_unit="g", default_price_per_unit_cents=12, low_stock_threshold=250),
        Ingredient(name="Eggs", default_unit="pcs", default_price_per_unit_cents=25, low_stock_threshold=6),
        Ingredient(name="Vanilla Extract", default_unit="ml", default_price_per_unit_cents=80, low_stock_threshold=30),
        Ingredient(name="Baking Soda", default_unit="g", default_price_per_unit_cents=3, low_stock_threshold=50),
        Ingredient(name="Salt", default_unit="g", default_price_per_unit_cents=2, low_stock_threshold=50),
        Ingredient(name="Chocolate Chips", default_unit="g", default_price_per_unit_cents=20, low_stock_threshold=200)
    ]
    db.session.add_all(ingredients)
    db.session.commit()
    print(f"Added {len(ingredients)} ingredients")
    
    # Add packaging
    packaging = [
        Packaging(name="Small Box", default_unit="pcs", default_price_per_unit_cents=40, low_stock_threshold=10),
        Packaging(name="Medium Box", default_unit="pcs", default_price_per_unit_cents=60, low_stock_threshold=10),
        Packaging(name="Large Box", default_unit="pcs", default_price_per_unit_cents=80, low_stock_threshold=5),
        Packaging(name="Plastic Wrap", default_unit="m", default_price_per_unit_cents=5, low_stock_threshold=5),
        Packaging(name="Ribbon", default_unit="m", default_price_per_unit_cents=10, low_stock_threshold=2),
        Packaging(name="Paper Bag", default_unit="pcs", default_price_per_unit_cents=20, low_stock_threshold=15)
    ]
    db.session.add_all(packaging)
    db.session.commit()
    print(f"Added {len(packaging)} packaging items")
    
    # Add recipes
    choc_chip_recipe = Recipe(
        name="Chocolate Chip Cookies",
        description="Classic chocolate chip cookies with a chewy center and crisp edges.",
        cookie_size="regular",
        dough_weight_per_cookie_g=25,
        yield_cookies=24
    )
    db.session.add(choc_chip_recipe)
    db.session.commit()
    
    # Add recipe ingredients
    recipe_ingredients = [
        RecipeIngredient(recipe_id=choc_chip_recipe.id, ingredient_id=ingredients[0].id, quantity=280),  # Flour
        RecipeIngredient(recipe_id=choc_chip_recipe.id, ingredient_id=ingredients[1].id, quantity=150),  # Granulated Sugar
        RecipeIngredient(recipe_id=choc_chip_recipe.id, ingredient_id=ingredients[2].id, quantity=150),  # Brown Sugar
        RecipeIngredient(recipe_id=choc_chip_recipe.id, ingredient_id=ingredients[3].id, quantity=225),  # Butter
        RecipeIngredient(recipe_id=choc_chip_recipe.id, ingredient_id=ingredients[4].id, quantity=2),    # Eggs
        RecipeIngredient(recipe_id=choc_chip_recipe.id, ingredient_id=ingredients[5].id, quantity=5),    # Vanilla
        RecipeIngredient(recipe_id=choc_chip_recipe.id, ingredient_id=ingredients[6].id, quantity=5),    # Baking Soda
        RecipeIngredient(recipe_id=choc_chip_recipe.id, ingredient_id=ingredients[7].id, quantity=3),    # Salt
        RecipeIngredient(recipe_id=choc_chip_recipe.id, ingredient_id=ingredients[8].id, quantity=350)   # Chocolate Chips
    ]
    db.session.add_all(recipe_ingredients)
    db.session.commit()
    print(f"Added 1 recipe with {len(recipe_ingredients)} ingredients")
    
    print("Database seeding complete!")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        seed_database()
