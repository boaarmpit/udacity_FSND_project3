import csv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Class, Category

# Connect to Database and create database session
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

# Add sample data to database
with open('sample_data.csv', 'rb') as csvfile:
    csv_reader = csv.reader(csvfile, delimiter=',', quotechar='"',
                            skipinitialspace=True)
    for row in csv_reader:

        category = session.query(Category).filter_by(title=row[0]).first()
        if not category:
            category = Category(title=row[0])
            session.add(category)
            session.flush()  # so that category.id returns value before commit

        session.add(Class(category_id=category.id, title=row[1],
                          description=row[2]))
    session.commit()
