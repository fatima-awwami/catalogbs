from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from catalogdb_setup import Base, Category, CategoryItem, User

engine = create_engine('sqlite:///catalog.db',connect_args={'check_same_thread':False},echo=True)
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

# User.__table__.drop()
# Category.__table__.drop()
# CategoryItem.__table__.drop()

#Create dummy user
User1 = User(name="Fatim Alawami", email="fatima.r.alawami@gmail.com",
             picture='https://pbs.twimg.com/profile_images/2671170543/18debd694829ed78203a5a36dd364160_400x400.png')
session.add(User1)
session.commit()

# Soccer Category
category1 = Category(user_id=1, name="Soccer", image="fifa.jpg",status='A')

session.add(category1)
session.commit()

CategoryItem2 = CategoryItem(user_id=1, title="Soccer ball", description="adidas 2018 FIFA World Cup Russia Telstar Glider Soccer Ball",
                     price=20, image='fifa.jpg', category=category1,status='A')

session.add(CategoryItem2)
session.commit()


CategoryItem1 = CategoryItem(user_id=1, title="Goalkeeper Shirt", description="Storelli Youth BodyShield 3/4 Soccer Goalkeeper Shirt",
                      price=30, image='goalkeepershirt.png', category=category1,status='A')

session.add(CategoryItem1)
session.commit()

CategoryItem3 = CategoryItem(user_id=1, title="Pullover", description="Mizuno Men's Elite 1/2-Zip Pullover",
                      price=47, image='pullover.png', category=category1,status='A')

session.add(CategoryItem3)
session.commit()

CategoryItem4 = CategoryItem(user_id=1, title="Soccer Shoes", description="Nike Kids' Tiempo Legend 7 Club Indoor Soccer Shoes",
                      price=60, image='soccer_shoes.jpg', category=category1,status='A')

session.add(CategoryItem4)
session.commit()

CategoryItem6 = CategoryItem(user_id=1, title="backpack", description="Nike Club Team Swoosh Soccer Backpack",
                      price=100, image='backbag.png', category=category1,status='A')

session.add(CategoryItem6)
session.commit()

CategoryItem5 = CategoryItem(user_id=1, title="Duffle Bag", description="Nike Brasilia Large Duffle Bag",
                    price=120, image='dufflebag.png', category=category1,status='A')

session.add(CategoryItem5)
session.commit()

# Items for frisbee
category2 = Category(user_id=1, name="frisbee",image="frisbee.jpg",status='A')

session.add(category2)
session.commit()


CategoryItem1 = CategoryItem(user_id=1, title="Frisbee Board 1", description="Frisbee Board",
                     price=10, image='frisbee.jpg', category=category2,status='A')

session.add(CategoryItem1)
session.commit()

CategoryItem2 = CategoryItem(user_id=1, title="Frisbee Board 2", description="Frisbee Board",
                     price=10, image='frisbee.jpg', category=category2,status='A')

session.add(CategoryItem2)
session.commit()

CategoryItem1 = CategoryItem(user_id=1, title="Frisbee Board 3", description="Frisbee Board",
                     price=10, image='frisbee.jpg', category=category2,status='A')

session.add(CategoryItem1)
session.commit()

CategoryItem2 = CategoryItem(user_id=1, title="Frisbee Board 4", description="Frisbee Board",
                     price=20, image='frisbee.jpg', category=category2,status='A')

session.add(CategoryItem2)
session.commit()
