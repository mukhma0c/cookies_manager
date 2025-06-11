# Cookie Manager

A web application for managing cookie baking operations, including order tracking, inventory management, recipe handling, and cost analysis.

## Features

- Order management with step-by-step wizard
- Ingredient and packaging inventory tracking
- Recipe creation and management
- Cost calculation and profit analysis
- Customer management
- Purchase logging
- Reporting and analytics

## Setup

### Prerequisites

- Python 3.12+
- SQLite 3
- Git

### Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd cookiemgr
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Initialize the database:
   ```
   flask db upgrade
   python seed.py
   ```

5. Run the development server:
   ```
   flask run --debug
   ```

6. Access the application at http://127.0.0.1:5000

## Development

### Database Migrations

To create a new migration after model changes:
```
flask db migrate -m "Description of changes"
flask db upgrade
```

### Running Tests

```
pytest
```

## Production Deployment

See the deployment section in the technical specification document.
