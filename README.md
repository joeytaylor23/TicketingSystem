# Ticketing System

A comprehensive IT support ticketing system built with Python Flask, featuring multi-role user management, email notifications, and activity tracking.

## Features

### ✅ Implemented Features

- **Multi-Role Authentication**
  - Admin: Full system access and user management
  - Technician: Ticket management and resolution
  - User: Ticket creation and viewing

- **Ticket Management**
  - Create, view, update, and close tickets
  - Priority levels (Low, Medium, High, Urgent)
  - Category tagging for organization
  - Assignment to technicians
  - Status tracking (Open, In Progress, Resolved, Closed)

- **Email Notifications**
  - Automatic notifications for ticket creation
  - Status update notifications
  - Assignment notifications
  - Comment notifications

- **Activity Logging**
  - Complete audit trail of all ticket activities
  - User actions tracking
  - Timestamp logging for troubleshooting

- **Responsive Web Interface**
  - Modern Bootstrap 5 design
  - Mobile-friendly responsive layout
  - Real-time updates and search functionality
  - Dashboard with statistics

## Tech Stack

- **Backend**: Python 3.8+ with Flask
- **Database**: SQLite (easily configurable for PostgreSQL/MySQL)
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Authentication**: Flask-Login with password hashing
- **Email**: Flask-Mail with SMTP support
- **Forms**: Flask-WTF with validation

## Installation & Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd ticketing-system
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment (Optional)
Copy `config.env.example` to `.env` and update the values:
```bash
cp config.env.example .env
```

Edit `.env` file with your configuration:
- `SECRET_KEY`: Change to a secure random key for production
- Email settings: Configure SMTP for email notifications

### 5. Run the Application
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Default User Accounts

The system creates default accounts for testing:

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | Administrator |
| technician | tech123 | Technician |
| user | user123 | User |

**⚠️ Important**: Change these default passwords in production!

## Usage Guide

### For Users
1. **Register/Login**: Create an account or use demo credentials
2. **Create Ticket**: Submit new support requests with detailed descriptions
3. **Track Progress**: Monitor ticket status and add comments
4. **View History**: Review all your submitted tickets

### For Technicians
1. **Dashboard**: View assigned and available tickets
2. **Manage Tickets**: Update status, priority, and assignments
3. **Add Comments**: Communicate with users about ticket progress
4. **Close Tickets**: Mark issues as resolved

### For Administrators
1. **User Management**: Create users and manage roles
2. **Category Management**: Organize tickets with custom categories
3. **System Overview**: Monitor system statistics and health
4. **Full Access**: Complete visibility and control over all tickets

## API Endpoints

The system provides the following main routes:

- `GET /` - Landing page
- `POST /register` - User registration
- `POST /login` - User authentication
- `GET /dashboard` - Main dashboard
- `POST /create_ticket` - New ticket creation
- `GET /ticket/<id>` - View ticket details
- `POST /update_ticket/<id>` - Update ticket
- `POST /add_comment/<id>` - Add comment
- `GET /admin` - Admin panel (admin only)

## Configuration

### Email Settings
To enable email notifications, configure these environment variables:
```
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

### Database
By default, the system uses SQLite. For production, you can configure PostgreSQL or MySQL by updating the `SQLALCHEMY_DATABASE_URI` in `app.py`.

## Security Features

- Password hashing with Werkzeug
- Session management with Flask-Login
- CSRF protection with Flask-WTF
- Role-based access control
- Input validation and sanitization

## Development

### Project Structure
```
ticketing-system/
├── app.py                 # Main application file
├── requirements.txt       # Python dependencies
├── config.env.example     # Environment configuration template
├── templates/            # HTML templates
│   ├── base.html         # Base template
│   ├── index.html        # Landing page
│   ├── login.html        # Login form
│   ├── register.html     # Registration form
│   ├── dashboard.html    # Main dashboard
│   ├── create_ticket.html # Ticket creation
│   ├── view_ticket.html  # Ticket details
│   └── admin.html        # Admin panel
└── static/              # Static assets
    ├── style.css        # Custom CSS
    └── script.js        # Custom JavaScript
```

### Adding New Features

1. **Database Models**: Add new models in `app.py`
2. **Routes**: Define new routes with appropriate decorators
3. **Templates**: Create HTML templates in the `templates/` directory
4. **Styling**: Add custom CSS to `static/style.css`
5. **JavaScript**: Add interactive features to `static/script.js`

## Deployment

### Production Checklist

1. **Security**:
   - Change default SECRET_KEY
   - Update default user passwords
   - Use environment variables for sensitive data
   - Enable HTTPS

2. **Database**:
   - Configure production database (PostgreSQL/MySQL)
   - Set up database backups
   - Configure connection pooling

3. **Email**:
   - Configure production SMTP server
   - Set up email templates
   - Test notification delivery

4. **Performance**:
   - Configure reverse proxy (nginx)
   - Set up application server (gunicorn)
   - Enable caching if needed

### Example Deployment Commands
```bash
# Install production server
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the code comments

## Future Enhancements

Potential improvements for future versions:
- File attachment support
- Advanced reporting and analytics
- API authentication for external integrations
- Mobile application
- Advanced search and filtering
- Custom workflow automation
- Integration with external tools (Slack, Teams, etc.)