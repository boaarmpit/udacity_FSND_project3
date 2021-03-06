from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from collections import OrderedDict

Base = declarative_base()

# Define 'user' class to keep track of users logged in with OAuth
class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))
    points = Column(Integer)

# Define 'category' class to categorize university classes in database
class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    title = Column(String(250), nullable=False)

# Define 'class' class for university classes to be stored in database
class Class(Base):
    __tablename__ = 'class'

    id = Column(Integer, primary_key=True)

    user = relationship(User)
    teacher_id = Column(Integer, ForeignKey('user.id'))

    category = relationship(User)
    category_id = Column(Integer, ForeignKey('category.id'))

    title = Column(String(250), nullable=False)
    description = Column(String(500), nullable=False)
    picture = Column(String(250))

    @property
    def serialize(self):
        """Return object data in easily serializeable format
        for json endpoint"""
        return OrderedDict([
            ('id', self.id),
            ('title', self.title),
            ('teacher_id', self.teacher_id),
            ('description', self.description),
            ('picture', self.picture)
        ])


engine = create_engine('sqlite:///catalog.db')
Base.metadata.create_all(engine)
