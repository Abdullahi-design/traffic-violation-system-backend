"""
Database seeder for Traffic Violation & Fine Management System.
Creates initial data matching the frontend mock data.
"""
import asyncio
import random
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import text
from app.database import engine, AsyncSessionLocal, Base
from app.models import User, ViolationType, Violation, Payment, Notification
from app.services.auth_service import hash_password


# ── Users ──────────────────────────────────────────────────────────────────────
USERS = [
    {"email": "adebayo@lastma.gov.ng", "full_name": "Adebayo Okonkwo", "role": "admin", "phone": "+234-801-234-5678", "badge_number": "ADM-001"},
    {"email": "funke@lastma.gov.ng", "full_name": "Funke Adeyemi", "role": "admin", "phone": "+234-802-345-6789", "badge_number": "ADM-002"},
    {"email": "emeka@lastma.gov.ng", "full_name": "Emeka Okafor", "role": "officer", "phone": "+234-803-456-7890", "badge_number": "OFF-001"},
    {"email": "aisha@lastma.gov.ng", "full_name": "Aisha Bello", "role": "officer", "phone": "+234-804-567-8901", "badge_number": "OFF-002"},
    {"email": "chidi@lastma.gov.ng", "full_name": "Chidi Nwosu", "role": "officer", "phone": "+234-805-678-9012", "badge_number": "OFF-003"},
]

# ── Violation Types ────────────────────────────────────────────────────────────
VIOLATION_TYPES = [
    {"name": "Speeding", "default_fine": Decimal("25000.00"), "description": "Exceeding the posted speed limit"},
    {"name": "Running Red Light", "default_fine": Decimal("50000.00"), "description": "Failing to stop at a red traffic signal"},
    {"name": "No Seatbelt", "default_fine": Decimal("15000.00"), "description": "Driving without wearing a seatbelt"},
    {"name": "Expired Vehicle Papers", "default_fine": Decimal("30000.00"), "description": "Operating a vehicle with expired registration documents"},
    {"name": "Wrong Parking", "default_fine": Decimal("10000.00"), "description": "Parking in a restricted or no-parking zone"},
    {"name": "Overloading", "default_fine": Decimal("35000.00"), "description": "Exceeding the vehicle's maximum passenger or cargo capacity"},
    {"name": "Using Phone While Driving", "default_fine": Decimal("20000.00"), "description": "Operating a mobile phone while driving"},
    {"name": "No Drivers License", "default_fine": Decimal("50000.00"), "description": "Driving without a valid driver's license"},
    {"name": "Broken Tail Light", "default_fine": Decimal("5000.00"), "description": "Operating a vehicle with non-functional tail lights"},
    {"name": "Illegal U-Turn", "default_fine": Decimal("15000.00"), "description": "Making a U-turn at a prohibited location"},
]

# ── Locations ──────────────────────────────────────────────────────────────────
LOCATIONS = [
    "Lekki-Epe Expressway, Lagos",
    "Ikorodu Road, Maryland, Lagos",
    "Third Mainland Bridge, Lagos",
    "Oshodi-Apapa Expressway, Lagos",
    "Allen Avenue, Ikeja, Lagos",
    "Admiralty Way, Lekki Phase 1, Lagos",
    "Ozumba Mbadiwe Avenue, Victoria Island, Lagos",
    "Ajah Roundabout, Lagos",
    "Berger Bus Stop, Ojodu, Lagos",
    "CMS Bus Stop, Lagos Island",
    "Wuse 2, Abuja",
    "Garki Area 11, Abuja",
    "Maitama District, Abuja",
    "Central Business District, Abuja",
    "Airport Road, Abuja",
    "Herbert Macaulay Way, Yaba, Lagos",
    "Opebi Road, Ikeja, Lagos",
    "Victoria Island, Lagos",
    "Surulere, Lagos",
    "Festac Town, Lagos",
]

# ── Plate formats ──────────────────────────────────────────────────────────────
PLATE_PREFIXES = ["LAG", "ABJ", "KAN", "OGN", "OYO", "RIV", "ENE", "ANA", "KWR", "BEN"]


def random_plate():
    prefix = random.choice(PLATE_PREFIXES)
    letters = "".join(random.choices("ABCDEFGHJKLMNPRSTUVWXYZ", k=2))
    digits = "".join(random.choices("0123456789", k=3))
    suffix = random.choice("ABCDEFGHJKLMNPRSTUVWXYZ")
    return f"{prefix}-{digits}{letters}"


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # ── Seed Users ─────────────────────────────────────────────────────
        print("Seeding users...")
        db_users = []
        for u in USERS:
            user = User(
                email=u["email"],
                password_hash=hash_password("password123"),
                full_name=u["full_name"],
                role=u["role"],
                phone=u["phone"],
                badge_number=u["badge_number"],
            )
            session.add(user)
            db_users.append(user)
        await session.flush()

        admins = [u for u in db_users if u.role == "admin"]
        officers = [u for u in db_users if u.role == "officer"]

        # ── Seed Violation Types ───────────────────────────────────────────
        print("Seeding violation types...")
        db_vtypes = []
        for vt in VIOLATION_TYPES:
            vtype = ViolationType(**vt)
            session.add(vtype)
            db_vtypes.append(vtype)
        await session.flush()

        # ── Seed Violations (60 records over 3 months) ─────────────────────
        print("Seeding violations...")
        now = datetime.utcnow()
        db_violations = []
        # Generate unique plates, some repeated for "repeat offenders"
        vehicle_pool = [random_plate() for _ in range(35)]
        # Add some duplicates for repeat offenders
        repeat_vehicles = random.sample(vehicle_pool, 8)
        vehicle_pool.extend(repeat_vehicles * 2)

        for i in range(60):
            vtype = random.choice(db_vtypes)
            officer = random.choice(officers)
            days_ago = random.randint(0, 90)
            hours = random.randint(6, 22)
            minutes = random.randint(0, 59)
            dt = (now - timedelta(days=days_ago)).replace(hour=hours, minute=minutes, second=0, microsecond=0)

            # Fine amount: use default_fine with some variation (±20%)
            base_fine = float(vtype.default_fine)
            variation = random.uniform(0.8, 1.2)
            fine = Decimal(str(round(base_fine * variation / 1000) * 1000))

            violation = Violation(
                vehicle_number=random.choice(vehicle_pool),
                violation_type_id=vtype.id,
                officer_id=officer.id,
                date_time=dt,
                location=random.choice(LOCATIONS),
                fine_amount=fine,
                description=f"{vtype.name} violation recorded at {random.choice(LOCATIONS)}",
                payment_status="unpaid",
            )
            session.add(violation)
            db_violations.append(violation)

        await session.flush()

        # ── Seed Payments ──────────────────────────────────────────────────
        print("Seeding payments...")
        payment_methods = ["cash", "bank_transfer", "online", "pos"]
        payment_count = 0

        for v in db_violations:
            roll = random.random()
            if roll < 0.35:
                # Fully paid
                receipt_num = f"RCP-{random.randint(10000, 99999)}"
                payment = Payment(
                    violation_id=v.id,
                    amount=v.fine_amount,
                    payment_method=random.choice(payment_methods),
                    payment_date=v.date_time + timedelta(days=random.randint(1, 14)),
                    receipt_number=receipt_num,
                    received_by=random.choice(db_users).id,
                    notes="Full payment received",
                )
                session.add(payment)
                v.payment_status = "paid"
                payment_count += 1
            elif roll < 0.55:
                # Partial payment
                partial_amount = Decimal(str(round(float(v.fine_amount) * random.uniform(0.3, 0.7) / 1000) * 1000))
                receipt_num = f"RCP-{random.randint(10000, 99999)}"
                payment = Payment(
                    violation_id=v.id,
                    amount=partial_amount,
                    payment_method=random.choice(payment_methods),
                    payment_date=v.date_time + timedelta(days=random.randint(1, 14)),
                    receipt_number=receipt_num,
                    received_by=random.choice(db_users).id,
                    notes="Partial payment",
                )
                session.add(payment)
                v.payment_status = "partial"
                payment_count += 1
            # else: remains unpaid

        await session.flush()

        # ── Seed Notifications ─────────────────────────────────────────────
        print("Seeding notifications...")
        notification_templates = [
            {"title": "New Violation Recorded", "type": "info", "related_type": "violation"},
            {"title": "Payment Received", "type": "success", "related_type": "payment"},
            {"title": "Overdue Fine Alert", "type": "warning", "related_type": "violation"},
            {"title": "System Update", "type": "info", "related_type": None},
            {"title": "High Fine Collected", "type": "success", "related_type": "payment"},
        ]

        for i in range(18):
            template = random.choice(notification_templates)
            user = random.choice(admins) if random.random() < 0.6 else random.choice(officers)
            days_ago = random.randint(0, 30)
            dt = now - timedelta(days=days_ago, hours=random.randint(0, 23))

            notification = Notification(
                user_id=user.id,
                title=template["title"],
                message=f"{template['title']} - Auto-generated notification #{i+1}",
                type=template["type"],
                is_read=random.random() < 0.4,
                related_id=random.choice(db_violations).id if template["related_type"] else None,
                related_type=template["related_type"],
            )
            notification.created_at = dt
            session.add(notification)

        await session.commit()

        print(f"\nSeed completed successfully!")
        print(f"  Users: {len(db_users)}")
        print(f"  Violation Types: {len(db_vtypes)}")
        print(f"  Violations: {len(db_violations)}")
        print(f"  Payments: {payment_count}")
        print(f"  Notifications: 18")


if __name__ == "__main__":
    asyncio.run(seed())
