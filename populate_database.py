import csv
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Class

# Connect to Database and create database session
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

with open('sample_data.csv', 'rb') as csvfile:
    csv_reader = csv.reader(csvfile, delimiter=',', quotechar='"', skipinitialspace=True)
    for row in csv_reader:
        session.add(Class(category=row[0], title=row[1], description=row[2]))
    session.commit()
