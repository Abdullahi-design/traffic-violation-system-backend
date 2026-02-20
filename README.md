# Traffic Violation & Fine Management System — Backend API

FastAPI backend for the Traffic Violation & Fine Management System.

## Tech Stack

- **Framework:** FastAPI
- **Database:** MySQL 8+ with SQLAlchemy (async)
- **Auth:** JWT with bcrypt password hashing
- **Migrations:** Alembic

## Setup

### 1. Create MySQL Database

```bash
mysql -u root -proot123 -e "CREATE DATABASE traffic_violation_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your database credentials
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run Migrations

```bash
alembic upgrade head
```

### 5. Seed the Database

```bash
python seed.py
```

### 6. Start the Server

```bash
uvicorn app.main:app --reload --port 8000
```

### 7. API Documentation

Open [http://localhost:8000/docs](http://localhost:8000/docs) for Swagger UI.

## Default Users

| Name | Email | Role | Password |
|------|-------|------|----------|
| Adebayo Okonkwo | adebayo@lastma.gov.ng | admin | password123 |
| Funke Adeyemi | funke@lastma.gov.ng | admin | password123 |
| Emeka Okafor | emeka@lastma.gov.ng | officer | password123 |
| Aisha Bello | aisha@lastma.gov.ng | officer | password123 |
| Chidi Nwosu | chidi@lastma.gov.ng | officer | password123 |

## API Endpoints

- `POST /api/auth/login` — Login
- `GET /api/auth/me` — Current user profile
- `GET /api/users/` — List users (admin)
- `GET /api/violations/` — List violations
- `POST /api/violations/` — Create violation
- `GET /api/payments/` — List payments
- `POST /api/payments/` — Record payment
- `GET /api/reports/summary` — Report summary (admin)
- `GET /api/reports/export/pdf` — Export PDF (admin)
- `GET /api/reports/export/excel` — Export Excel (admin)
- `GET /api/notifications/` — User notifications
- `GET /api/dashboard/admin` — Admin dashboard
- `GET /api/dashboard/officer` — Officer dashboard
