# MedSupport System - Healthcare IT Support Platform

A comprehensive ticketing system designed specifically for healthcare IT support, featuring role-based access control, real-time notifications, and professional admin tools.

## 🏥 Features

### Core Functionality
- **User Management**: Admin, Technician, and User roles with appropriate permissions
- **Ticket System**: Create, update, and track support tickets with priority levels
- **Activity Logging**: Complete audit trail of all system activities
- **Email Notifications**: Automated email alerts for ticket updates
- **Category Management**: Organize tickets by hardware, software, network, etc.

### Admin Tools
- **System Health Monitoring**: Real-time server and application metrics
- **Generate Reports**: Comprehensive analytics and statistics
- **Export Data**: CSV export functionality for data analysis
- **Clear Cache**: Maintenance tools for system optimization
- **User Role Management**: Assign and modify user permissions

### Professional UI/UX
- **Dark Professional Theme**: Hospital-appropriate color scheme
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Bootstrap 5**: Modern, accessible interface components
- **Font Awesome Icons**: Professional visual elements

## 🚀 Live Demo

**Demo URL**: [Your deployed URL here]

### Demo Accounts
- **Admin**: `admin` / `admin123` - Full system access
- **Technician**: `technician` / `tech123` - Ticket management
- **User**: `user` / `user123` - Submit and track tickets

## 🛠️ Technology Stack

- **Backend**: Python Flask
- **Database**: SQLite (production-ready for PostgreSQL)
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Authentication**: Flask-Login
- **Email**: Flask-Mail
- **Deployment**: Gunicorn, Heroku/Railway ready

## 📋 Installation

### Local Development
```bash
# Clone the repository
git clone [your-repo-url]
cd ticketing-system

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export FLASK_ENV=development
export SECRET_KEY=your-secret-key

# Run the application
python app.py
```

### Production Deployment

#### Heroku
```bash
# Install Heroku CLI
heroku create your-app-name
git push heroku main
```

#### Railway
```bash
# Connect your GitHub repository
# Railway will automatically detect and deploy
```

#### VPS/Cloud
```bash
# Install dependencies
pip install -r requirements.txt

# Run with Gunicorn
gunicorn app:app -b 0.0.0.0:8000
```

## 🔧 Configuration

### Environment Variables
```bash
SECRET_KEY=your-secret-key-here
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

### Database
The system uses SQLite by default. For production, consider PostgreSQL:
```python
# In app.py
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///ticketing_system.db')
```

## 📊 System Architecture

### User Roles
- **Admin**: Full system access, user management, system monitoring
- **Technician**: Ticket assignment, status updates, priority management
- **User**: Create tickets, add comments, track progress

### Database Models
- **User**: Authentication and role management
- **Ticket**: Support request tracking
- **Category**: Ticket organization
- **ActivityLog**: Audit trail

### Key Features
- **Real-time System Health**: CPU, memory, disk monitoring
- **Comprehensive Reporting**: Analytics and statistics
- **Email Integration**: Automated notifications
- **Professional UI**: Hospital-appropriate design

## 🔒 Security Features

- **Role-based Access Control**: Granular permissions
- **Session Management**: Secure user sessions
- **Input Validation**: XSS and injection protection
- **Password Hashing**: Secure credential storage
- **CSRF Protection**: Cross-site request forgery prevention

## 📈 Performance

- **Optimized Queries**: Efficient database operations
- **Caching**: Activity log cleanup and optimization
- **Responsive Design**: Fast loading on all devices
- **Minimal Dependencies**: Lightweight deployment

## 🎯 Use Cases

### Healthcare IT Support
- **Hardware Issues**: Computer, printer, scanner problems
- **Software Support**: Application installation and troubleshooting
- **Network Problems**: Connectivity and access issues
- **Account Management**: User access and permissions

### Benefits
- **Improved Response Time**: Organized ticket management
- **Better Tracking**: Complete audit trail
- **Professional Interface**: Hospital-appropriate design
- **Scalable Solution**: Ready for enterprise deployment

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👨‍💻 Author

**Joey Taylor** - Healthcare IT Support System Developer

## 🙏 Acknowledgments

- Bootstrap for the responsive UI framework
- Font Awesome for professional icons
- Flask community for the excellent web framework
- Healthcare IT professionals for domain expertise

---

**MedSupport System** - Professional Healthcare IT Support Platform
*Secure • Reliable • Professional*