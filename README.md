# Cookie Manager

A web application for managing cookie baking operations, including order tracking, inventory management, recipe handling, and cost analysis.

## Features

- Order management with step-by-step wizard
- Ingredient and packaging inventory tracking
- Recipe creation and management
- Cost calculation and profit analysis
- Customer management
- Purchase logging
- Reporting and analytics with CSV export
- Accessibility features including high contrast mode

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

For production deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

### Key Components

- **Nginx**: Serves as a reverse proxy and handles SSL termination
- **Gunicorn**: WSGI application server for running the Flask application
- **Systemd**: Manages the application service for auto-restart
- **Automated Backups**: Daily backups of database and static files

## Project Structure

```
cookiemgr/
├── app.py                 # Application entry point
├── config.py              # Configuration settings
├── models.py              # Database models
├── cost_helpers.py        # Cost calculation utilities
├── migrations/            # Database migrations
├── scheduled_jobs.py      # Scheduled background tasks
├── seed.py                # Initial data seeding
├── static/                # Static assets
│   ├── css/               # CSS stylesheets
│   └── img/               # Uploaded images
├── templates/             # Jinja2 templates
│   ├── dashboard/         # Dashboard views
│   ├── inventory/         # Inventory management
│   ├── orders/            # Order processing
│   ├── purchases/         # Purchase tracking
│   ├── recipes/           # Recipe management
│   └── reports/           # Reporting and analytics
├── views/                 # Blueprint controllers
│   ├── dashboard.py       # Dashboard routes
│   ├── inventory.py       # Inventory routes
│   ├── orders.py          # Order routes
│   ├── purchases.py       # Purchase routes
│   ├── recipes.py         # Recipe routes
│   └── reports.py         # Reporting routes
├── tests/                 # Test suite
├── backup.sh              # Backup script
├── cookiemgr.service      # Systemd service file
├── nginx_cookiemgr.conf   # Nginx configuration
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

## License

[MIT License](LICENSE)
