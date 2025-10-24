# Samad Islamic Banking System

A modern Islamic banking system built with Flask that handles user accounts, transactions, and profit distribution in accordance with Islamic banking principles.

## Features

- 🏦 **Admin Dashboard**: Centralized control panel for all banking operations
- 👥 **User Management**: Create, edit, and manage user accounts
- 💰 **Balance Management**: Track and manage user account balances
- 🔄 **Transaction System**: Handle credits, debits, and transfers between accounts
- 📊 **Profit Distribution**: Distribute profits among users based on their balance shares
- 🔒 **Secure Authentication**: Admin login system with session management
- 🎨 **Modern UI**: Responsive design with Islamic-themed styling

## Technology Stack

- **Backend**: Python 3.x, Flask
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: HTML5, CSS3, JavaScript
- **UI Framework**: Bootstrap 4.5
- **Icons**: Font Awesome 5
- **Fonts**: Google Fonts (Poppins)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Banking-app.git
cd Banking-app
```

2. Create and activate a virtual environment:
```bash
# On macOS/Linux



# On Windows
python -m venv venv
.\venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Initialize the database:
```bash
python init_db.py
```

5. Run the application:
```bash
python run.py --port 5001
```

The application will be available at `http://localhost:5001`

## Default Admin Credentials

- Username: admin
- Password: admin123

*Note: Please change these credentials in a production environment*

## Project Structure

```
Banking-app/
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── routes/
│   │   ├── auth.py
│   │   └── admin.py
│   ├── static/
│   │   └── css/
│   │       └── style.css
│   └── templates/
│       ├── base.html
│       ├── login.html
│       ├── admin_dashboard.html
│       └── ...
├── instance/
│   └── bank.sqlite
├── config.py
├── init_db.py
├── requirements.txt
└── run.py
```

## Features in Detail

### User Management
- Create new user accounts with CNIC and initial balance
- Edit user details and balances
- Delete users (only if balance is zero)
- View all users in a tabulated format

### Transaction System
- Credit: Add funds to user accounts
- Debit: Remove funds from user accounts
- Transfer: Move funds between user accounts
- Transaction history tracking

### Profit Distribution
- Calculate and distribute profits based on user balances
- Automatic profit share calculation
- Transaction records for profit distributions

### Security Features
- Password-protected admin access
- Session management
- CSRF protection
- Input validation

## Development

To contribute to this project:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to your branch
5. Create a Pull Request

## Production Deployment Notes

For production deployment:

1. Change the secret key in `config.py`
2. Use a production-grade WSGI server (e.g., Gunicorn)
3. Use a proper database (e.g., PostgreSQL)
4. Set up proper logging
5. Change default admin credentials
6. Set up HTTPS
7. Configure proper security headers

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue in the GitHub repository or contact the maintainers.

## Acknowledgments

- Flask framework and its contributors
- Bootstrap team
- Font Awesome team
- All contributors to this project 