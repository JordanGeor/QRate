# QRate

QRate is a QR-based customer feedback and digital menu platform built with FastAPI.

It allows businesses such as restaurants, cafés, and hospitality venues to provide customers with a QR code for accessing venue information, browsing a digital menu, submitting feedback, and contacting the business.

## Features

- QR-based restaurant pages
- Customer ratings and feedback
- Google Reviews integration
- Digital restaurant menu
- Greek and English language support
- Admin dashboard
- Superadmin and owner roles
- Restaurant management
- Menu category and item management
- Customer contact requests
- Email notifications
- Review and contact management

## Tech Stack

- Python
- FastAPI
- SQLAlchemy
- SQLite
- Jinja2
- HTML/CSS

## Installation

Clone the repository:

```bash
git clone https://github.com/JordanGeor/QRate.git
cd QRate
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

## Environment Configuration

Create a `.env` file in the project root.

You can use `.env.example` as a template:

```env
SESSION_SECRET=your-secure-random-secret
COOKIE_SECURE=0

ADMIN_EMAIL=manager@example.com

SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your-email@example.com
SMTP_PASS=your-password
SMTP_FROM=your-email@example.com
SMTP_TLS=1
```

Never commit the real `.env` file or credentials to Git.

For local development over HTTP, use:

```env
COOKIE_SECURE=0
```

For production over HTTPS, use:

```env
COOKIE_SECURE=1
```

## Create the Superadmin

Run:

```bash
python create_admin.py
```

Enter the superadmin username and password when prompted.

## Run the Application

Start the development server:

```bash
uvicorn app.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000/admin/login
```

## Security

QRate includes:

- Password hashing using PBKDF2-HMAC-SHA256
- Signed and expiring authentication sessions
- HTTP-only authentication cookies
- Role-based access control
- Restaurant ownership checks
- Environment-based secret configuration
- Protection of local databases and environment files through `.gitignore`

Additional security improvements are planned as the project evolves.

## Project Status

QRate is currently under active development.

Planned improvements include enhanced security, analytics, structured feedback, QR source tracking, reporting, and additional SaaS-oriented functionality.

## Author

Developed by JordanGeor.