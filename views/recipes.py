from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from models import db, Recipe, RecipeIngredient, Ingredient
import os
from werkzeug.utils import secure_filename
import uuid

recipes_bp = Blueprint('recipes', __name__, url_prefix='/recipes')

# Helper functions for file uploads
def allowed_file(filename):
    """Check if file has an allowed extension."""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_file(file):
    """Save uploaded file with a unique name."""
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Create a unique filename to prevent overwrites
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        # Create directory if it doesn't exist
        save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'recipes')
        os.makedirs(save_path, exist_ok=True)
        file_path = os.path.join(save_path, unique_filename)
        file.save(file_path)
        # Return the relative path to store in the database
        return os.path.join('img', 'recipes', unique_filename)
    return None

@recipes_bp.route('/')
def list_recipes():
    """Display all recipes."""
    recipes = Recipe.query.order_by(Recipe.name).all()
    return render_template('recipes/list.html', recipes=recipes)

@recipes_bp.route('/<int:recipe_id>')
def view_recipe(recipe_id):
    """View a single recipe."""
    recipe = Recipe.query.get_or_404(recipe_id)
    return render_template('recipes/view.html', recipe=recipe)

@recipes_bp.route('/new', methods=['GET', 'POST'])
def add_recipe():
    """Add a new recipe."""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        cookie_size = request.form.get('cookie_size')
        dough_weight_per_cookie_g = request.form.get('dough_weight_per_cookie_g', type=float)
        yield_cookies = request.form.get('yield_cookies', type=int)
        notes = request.form.get('notes')
        
        # Check if recipe with same name already exists
        existing = Recipe.query.filter_by(name=name).first()
        if existing:
            flash(f'Recipe "{name}" already exists.', 'danger')
            return redirect(url_for('recipes.add_recipe'))
        
        # Create new recipe
        recipe = Recipe(
            name=name,
            description=description,
            cookie_size=cookie_size,
            dough_weight_per_cookie_g=dough_weight_per_cookie_g,
            yield_cookies=yield_cookies,
            notes=notes
        )
        
        # Handle image upload
        file = request.files.get('image')
        if file and file.filename:
            image_path = save_file(file)
            if image_path:
                recipe.image_path = image_path
        
        db.session.add(recipe)
        db.session.commit()
        
        # Add ingredients
        ingredient_ids = request.form.getlist('ingredient_id[]')
        quantities = request.form.getlist('ingredient_quantity[]')
        
        for i in range(len(ingredient_ids)):
            try:
                ingredient_id = int(ingredient_ids[i])
                quantity = float(quantities[i])
                
                if ingredient_id and quantity > 0:
                    recipe_ingredient = RecipeIngredient(
                        recipe_id=recipe.id,
                        ingredient_id=ingredient_id,
                        quantity=quantity
                    )
                    db.session.add(recipe_ingredient)
            except (ValueError, IndexError):
                continue
        
        db.session.commit()
        flash(f'Recipe "{name}" added successfully.', 'success')
        return redirect(url_for('recipes.view_recipe', recipe_id=recipe.id))
    
    # Get all ingredients for the form
    ingredients = Ingredient.query.order_by(Ingredient.name).all()
    return render_template('recipes/form.html', recipe=None, ingredients=ingredients)

@recipes_bp.route('/<int:recipe_id>/edit', methods=['GET', 'POST'])
def edit_recipe(recipe_id):
    """Edit an existing recipe."""
    recipe = Recipe.query.get_or_404(recipe_id)
    
    if request.method == 'POST':
        recipe.name = request.form.get('name')
        recipe.description = request.form.get('description')
        recipe.cookie_size = request.form.get('cookie_size')
        recipe.dough_weight_per_cookie_g = request.form.get('dough_weight_per_cookie_g', type=float)
        recipe.yield_cookies = request.form.get('yield_cookies', type=int)
        recipe.notes = request.form.get('notes')
        
        # Handle image upload
        file = request.files.get('image')
        if file and file.filename:
            image_path = save_file(file)
            if image_path:
                # Delete old image if it exists
                if recipe.image_path:
                    try:
                        old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], recipe.image_path)
                        if os.path.exists(old_path):
                            os.remove(old_path)
                    except Exception as e:
                        current_app.logger.error(f"Error deleting file: {e}")
                
                recipe.image_path = image_path
        
        # Update ingredients
        # First, delete all existing ingredients
        RecipeIngredient.query.filter_by(recipe_id=recipe.id).delete()
        
        # Then add new ingredients
        ingredient_ids = request.form.getlist('ingredient_id[]')
        quantities = request.form.getlist('ingredient_quantity[]')
        
        for i in range(len(ingredient_ids)):
            try:
                ingredient_id = int(ingredient_ids[i])
                quantity = float(quantities[i])
                
                if ingredient_id and quantity > 0:
                    recipe_ingredient = RecipeIngredient(
                        recipe_id=recipe.id,
                        ingredient_id=ingredient_id,
                        quantity=quantity
                    )
                    db.session.add(recipe_ingredient)
            except (ValueError, IndexError):
                continue
        
        db.session.commit()
        flash(f'Recipe "{recipe.name}" updated successfully.', 'success')
        return redirect(url_for('recipes.view_recipe', recipe_id=recipe.id))
    
    # Get all ingredients for the form
    ingredients = Ingredient.query.order_by(Ingredient.name).all()
    return render_template('recipes/form.html', recipe=recipe, ingredients=ingredients)

@recipes_bp.route('/<int:recipe_id>/delete', methods=['POST'])
def delete_recipe(recipe_id):
    """Delete a recipe."""
    recipe = Recipe.query.get_or_404(recipe_id)
    
    try:
        # Delete image file if it exists
        if recipe.image_path:
            try:
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], recipe.image_path)
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                current_app.logger.error(f"Error deleting file: {e}")
        
        name = recipe.name
        db.session.delete(recipe)
        db.session.commit()
        flash(f'Recipe "{name}" deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting recipe: {str(e)}', 'danger')
    
    return redirect(url_for('recipes.list_recipes'))

@recipes_bp.route('/<int:recipe_id>/clone', methods=['POST'])
def clone_recipe(recipe_id):
    """Clone an existing recipe."""
    original_recipe = Recipe.query.get_or_404(recipe_id)
    
    # Create new recipe with "(Copy)" suffix
    new_name = f"{original_recipe.name} (Copy)"
    # Check if name already exists, add number if needed
    counter = 1
    while Recipe.query.filter_by(name=new_name).first():
        counter += 1
        new_name = f"{original_recipe.name} (Copy {counter})"
    
    new_recipe = Recipe(
        name=new_name,
        description=original_recipe.description,
        cookie_size=original_recipe.cookie_size,
        dough_weight_per_cookie_g=original_recipe.dough_weight_per_cookie_g,
        yield_cookies=original_recipe.yield_cookies,
        notes=original_recipe.notes
    )
    
    # Copy image if exists
    if original_recipe.image_path:
        try:
            original_path = os.path.join(current_app.config['UPLOAD_FOLDER'], original_recipe.image_path)
            if os.path.exists(original_path):
                # Generate new filename with uuid
                filename = os.path.basename(original_recipe.image_path)
                unique_filename = f"{uuid.uuid4().hex}_{filename}"
                save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'recipes')
                os.makedirs(save_path, exist_ok=True)
                new_path = os.path.join(save_path, unique_filename)
                
                # Copy the file
                import shutil
                shutil.copy2(original_path, new_path)
                
                # Set path in new recipe
                new_recipe.image_path = os.path.join('img', 'recipes', unique_filename)
        except Exception as e:
            current_app.logger.error(f"Error copying image: {e}")
    
    db.session.add(new_recipe)
    db.session.flush()  # Get ID without committing
    
    # Clone all ingredients
    for ingredient in original_recipe.ingredients:
        new_ingredient = RecipeIngredient(
            recipe_id=new_recipe.id,
            ingredient_id=ingredient.ingredient_id,
            quantity=ingredient.quantity
        )
        db.session.add(new_ingredient)
    
    db.session.commit()
    flash(f'Recipe cloned successfully as "{new_name}".', 'success')
    return redirect(url_for('recipes.view_recipe', recipe_id=new_recipe.id))

@recipes_bp.route('/api/ingredients')
def api_ingredients():
    """API endpoint to get all ingredients for AJAX."""
    ingredients = Ingredient.query.order_by(Ingredient.name).all()
    return jsonify([{
        'id': ingredient.id,
        'name': ingredient.name,
        'default_unit': ingredient.default_unit
    } for ingredient in ingredients])
