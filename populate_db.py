from app import app, db, Degree  # Import your app, db, and model from your main application
from faker import Faker
import random

fake = Faker()

with app.app_context():
    # Optional: Uncomment the following lines if you want to drop existing tables and start fresh.
    # db.drop_all()
    # db.create_all()

    for _ in range(700):
        entryno = fake.unique.bothify(text='??####')
        name = fake.name()
        name_hindi = fake.name()  # Placeholder; you might want to provide actual Hindi names
        spec_name = fake.word()
        spec_name_hindi = fake.word()
        degree_name = fake.word()
        degree_name_hindi = fake.word()
        completion_year = str(fake.year())
        convo_day = str(random.randint(1, 28))  # Keeping it within a safe range for days
        convo_month_hindi = fake.month_name()
        convo_year = str(fake.year())
        degree_gpa = str(round(random.uniform(6.0, 10.0), 2))
        given_day = str(random.randint(1, 28))
        given_month = fake.month_name()
        given_year = str(fake.year())

        degree = Degree(
            entryno=entryno,
            name=name,
            name_hindi=name_hindi,
            spec_name=spec_name,
            spec_name_hindi=spec_name_hindi,
            degree_name=degree_name,
            degree_name_hindi=degree_name_hindi,
            completion_year=completion_year,
            convo_day=convo_day,
            convo_month_hindi=convo_month_hindi,
            convo_year=convo_year,
            degree_gpa=degree_gpa,
            given_day=given_day,
            given_month=given_month,
            given_year=given_year
        )
        db.session.add(degree)
    db.session.commit()
    print("Database populated with 100 dummy entries.")
