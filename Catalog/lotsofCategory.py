from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from models import Base, Category

engine = create_engine(
    'sqlite:///catalogItems.db',
    connect_args={'check_same_thread': False},
    poolclass=StaticPool, echo=True
    )

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)

session = DBSession()

category1 = Category(name="World")
session.add(category1)
session.commit()

category2 = Category(name="Programming")
session.add(category2)
session.commit()

category3 = Category(name="Culture")
session.add(category3)
session.commit()

category4 = Category(name="Tech")
session.add(category4)
session.commit()

category5 = Category(name="Startups")
session.add(category5)
session.commit()

category6 = Category(name="Self")
session.add(category6)
session.commit()

category7 = Category(name="Politics")
session.add(category7)
session.commit()

category8 = Category(name="Design")
session.add(category8)
session.commit()

category9 = Category(name="Health")
session.add(category9)
session.commit()

category10 = Category(name="Science")
session.add(category10)
session.commit()

category11 = Category(name="Popular")
session.add(category11)
session.commit()

category12 = Category(name="Collections")
session.add(category12)
session.commit()


print("Categories added")
