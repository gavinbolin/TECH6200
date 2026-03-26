# Scrounge - Recipe Management Application

A Flask-based web application for managing inventory and discovering recipes based on available ingredients.

## Features

- User authentication and session management
- Inventory management with encrypted storage
- Recipe search using external APIs
- Ready-to-make meal suggestions
- RESTful API endpoints
- Production-ready deployment configuration

## Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/scrounge.git
   cd scrounge
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

5. **Run the application**
   ```bash
   # Development server
   python app.py

   # Or production server
   python wsgi.py
   ```

## Project Structure

```
scrounge/
├── app.py                 # Main Flask application
├── wsgi.py               # WSGI entry point for production
├── models.py             # Database models and business logic
├── api.py                # REST API blueprint
├── requirements.txt      # Python dependencies
├── Procfile             # Heroku deployment configuration
├── runtime.txt          # Python version for Heroku
├── .env.example         # Environment variables template
├── .gitignore           # Git ignore rules
├── DEPLOYMENT.md        # Detailed deployment guide
├── static/              # Static assets (CSS, JS, images)
├── templates/           # Jinja2 HTML templates
└── instance/            # Flask instance folder (auto-created)
```

## Configuration

The application uses environment variables for configuration. Copy `.env.example` to `.env` and modify as needed:

```bash
# Flask Configuration
SECRET_KEY=your_secret_key_here

# Database Configuration
DATABASE_URI=sqlite:///scrounge.db
```

### Required Environment Variables

- `SECRET_KEY`: A secure random string for Flask session management

### Optional Environment Variables

- `DATABASE_URI`: Database connection string (defaults to SQLite)

## API Endpoints

### Authentication Required Endpoints

- `GET /api/v1/inventory` - Get all inventory items
- `GET /api/v1/inventory/<item_name>` - Get specific inventory item

### Web Interface Routes

- `GET /` - Home page (login required)
- `GET /login` - User login
- `GET /register` - User registration
- `GET /inventory` - Inventory management
- `GET /ready_meals` - Recipes ready to make
- `GET /search_recipes` - Search for new recipes
- `GET /recipe_book` - Saved recipes

## Database

The application uses SQLAlchemy with SQLite by default. For production, consider using PostgreSQL.

### Models

- **User**: User accounts with encrypted passwords
- **Inventory**: User inventory items (encrypted)
- **Recipe**: Saved recipes (encrypted)
- **Preference**: User cuisine preferences (encrypted)

## Security Features

- Password hashing with Werkzeug
- Session-based authentication
- Data encryption for sensitive information
- Environment variable configuration
- CSRF protection via Flask-WTF

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions to Heroku.

### Quick Heroku Deployment

```bash
# Install Heroku CLI and login
heroku create your-app-name
heroku config:set SECRET_KEY=your_secret_key
git push heroku main
```

## Development

### Running Tests

```bash
python -m pytest
```

### Code Quality

- Follow PEP 8 style guidelines
- Use meaningful variable names
- Add docstrings to functions
- Test thoroughly before committing

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions, please open an issue on GitHub or contact the development team.

---

**Production Ready**: This application is configured for production deployment with proper security measures, environment variable management, and deployment automation.