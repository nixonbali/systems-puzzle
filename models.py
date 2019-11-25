from database import Base
from sqlalchemy import Column, Integer, String, Table
from sqlalchemy.types import DateTime
from sqlalchemy.orm import mapper

class Items(Base):
    """
    Items table
    """
    __tablename__ = 'items'
    id = Column(Integer, primary_key=True)
    name = Column(String(256))
    quantity = Column(Integer)
    description = Column(String(256))
    date_added = Column(DateTime())
    #def __init__(self, name, quantity, description, date_added):
#        self.name = name
#        self.quantity = quantity
#        self.description = description
#        self.date_added = date_added
