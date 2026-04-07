from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker

# Create SQLite database (file will be created automatically)
engine = create_engine("sqlite:///example.db", echo=True)

Base = declarative_base()

# Define table
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    age = Column(Integer)

# Create table
Base.metadata.create_all(engine)

# Create session
Session = sessionmaker(bind=engine)
session = Session()

# Insert sample data (only once)
if session.query(User).count() == 0:
    users = [
        User(name="Alice", age=22),
        User(name="Bob", age=25),
        User(name="Charlie", age=30)
    ]
    session.add_all(users)
    session.commit()

# ✅ SELECT query
results = session.query(User).all()

print("\nUsers in database:")
for user in results:
    print(user.id, user.name, user.age)