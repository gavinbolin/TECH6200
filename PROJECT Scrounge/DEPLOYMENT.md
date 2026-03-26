# Deployment Guide: GitHub + Heroku

This guide covers deploying the Scrounge application to production using GitHub for version control and Heroku for hosting.

## Pre-Deployment Checklist

### 1. Security & Configuration
- [ ] **Environment Variables**: Ensure all sensitive data is loaded from environment variables
- [ ] **Secret Key**: Never commit `SECRET_KEY` to version control
- [ ] **Database**: Configure production database (Heroku Postgres recommended)
- [ ] **Encryption Key**: The `.fernet_key` file should NOT be committed to GitHub

### 2. Files to Verify
- [ ] `requirements.txt` - Contains all dependencies with versions
- [ ] `Procfile` - Tells Heroku how to run the application
- [ ] `runtime.txt` - Specifies Python version for Heroku
- [ ] `.env.example` - Template for environment variables (committed)
- [ ] `.env` - Local environment variables (NOT committed)
- [ ] `.gitignore` - Excludes sensitive files from Git

### 3. Code Quality
- [ ] Remove debug mode from production
- [ ] Ensure all imports work correctly
- [ ] Test application locally before deployment

## Step 1: Prepare for GitHub

### Initialize Git Repository
```bash
git init
git add .
git status  # Review what will be committed
```

### Important: Check .gitignore
Ensure your `.gitignore` includes:
```
.env
.fernet_key
__pycache__/
*.pyc
venv/
.env.local
```

### Create Initial Commit
```bash
# Remove any sensitive files that might have been added
git rm --cached .env .fernet_key  # If accidentally added

# Add and commit
git add .
git commit -m "Initial commit: Scrounge application"
```

### Create GitHub Repository
1. Go to [GitHub.com](https://github.com) and create a new repository
2. Copy the repository URL
3. Push to GitHub:
```bash
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git push -u origin main
```

## Step 2: Heroku Setup

### Install Heroku CLI
Download and install the Heroku CLI from [heroku.com/cli](https://devcenter.heroku.com/articles/heroku-cli)

### Login to Heroku
```bash
heroku login
```

### Create Heroku App
```bash
heroku create your-app-name
# Or let Heroku generate a name: heroku create
```

### Set Environment Variables on Heroku
```bash
# Set required environment variables
heroku config:set SECRET_KEY=your_super_secret_key_here

# Optional: Set database URL (Heroku provides DATABASE_URL automatically with Postgres add-on)
heroku config:set DATABASE_URI=DATABASE_URL
```

### Deploy to Heroku
```bash
# Push your code to Heroku
git push heroku main

# Or if your branch is master:
git push heroku master
```

### Database Setup (Optional)
If using Heroku Postgres:
```bash
# Add Postgres add-on
heroku addons:create heroku-postgresql:hobby-dev

# Run database migrations if needed
heroku run python -c "from app import app; app.app_context().push(); from models import db; db.create_all()"
```

## Step 3: Post-Deployment

### Check Application Logs
```bash
heroku logs --tail
```

### Open Application
```bash
heroku open
```

### Monitor Application
```bash
# View application info
heroku info

# Check running processes
heroku ps

# Scale dynos if needed
heroku ps:scale web=1
```

## Environment Variables Reference

### Required Variables
- `SECRET_KEY`: Flask session secret key (generate a long random string)

### Optional Variables
- `DATABASE_URI`: Database connection string (defaults to SQLite)

### Setting Variables Locally (.env file)
```
SECRET_KEY=your_secret_key_here
DATABASE_URI=sqlite:///scrounge.db
```

## Troubleshooting

### Common Issues

1. **Application Error (H10)**
   - Check logs: `heroku logs --tail`
   - Verify Procfile is correct
   - Ensure all dependencies are in requirements.txt

2. **KeyError: SECRET_KEY**
   - Set SECRET_KEY in Heroku config: `heroku config:set SECRET_KEY=your_key`

3. **Database Connection Issues**
   - For Heroku Postgres, use `DATABASE_URL` environment variable
   - Ensure database is properly configured

4. **Import Errors**
   - Verify all files are committed to GitHub
   - Check Python version compatibility

### Useful Commands
```bash
# View config vars
heroku config

# View logs
heroku logs --tail

# Restart application
heroku restart

# Run commands on Heroku
heroku run bash
heroku run python -c "print('Hello from Heroku')"
```

## Production Considerations

### Security
- Use strong, unique SECRET_KEY
- Never commit sensitive files to GitHub
- Use HTTPS (Heroku provides SSL certificates)
- Regularly update dependencies

### Performance
- Monitor application performance with `heroku logs`
- Scale dynos as needed: `heroku ps:scale web=2`
- Consider using Heroku Redis for session storage if needed

### Database
- Use Heroku Postgres for production
- Set up database backups
- Monitor database performance

### Maintenance
- Regularly update Python and dependencies
- Monitor for security vulnerabilities
- Keep backup of encryption keys (`.fernet_key`)

## File Structure for Deployment

```
your-project/
├── app.py                 # Main Flask application
├── wsgi.py               # WSGI entry point
├── models.py             # Database models
├── api.py                # API blueprint
├── requirements.txt      # Python dependencies
├── Procfile             # Heroku process definition
├── runtime.txt          # Python version specification
├── .env.example         # Environment variables template
├── .gitignore           # Git ignore rules
├── static/              # Static files
├── templates/           # Jinja2 templates
└── instance/            # Flask instance folder (auto-created)
```

## Final Steps

1. Test locally with production settings
2. Commit all changes to GitHub
3. Deploy to Heroku
4. Test the live application
5. Set up monitoring and alerts
6. Document any custom configurations

Remember: Always test thoroughly before deploying to production!