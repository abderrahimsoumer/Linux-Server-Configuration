from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import create_engine
from passlib.apps import custom_app_context as pwd_context
import random, string
from itsdangerous import(TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)


Base = declarative_base()

# unique key to verify the token
secret_key = ''.join(
                     random.choice(string.ascii_uppercase + string.digits)
                     for x in range(32)
                    )


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(60))
    username = Column(String(32), index=True)
    email =  Column(String(255), index=True)
    picture =  Column(String(255))
    provider =  Column(String(32))
    provider_id =  Column(String(32))
    password_hash = Column(String)
    # source = Column(String(60)) # Exemple: google, facebook ...
    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'name'         : self.name,
           'username'     : self.username,
       }

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    # generate auth tokens valid 
    def generate_auth_token(self, expiration=600):
        s = Serializer(secret_key, expires_in = expiration)
        return s.dumps({'id': self.id})

    #verify auth tokens 
    @staticmethod
    def verify_auth_token(token):
        s = Serializer(secret_key)
        try:
            data = s.loads(token)
        except SignatureExpired:
            #Valid token, but expired
            return None
        except BadSignature:
            #Invalid token
            return None
        user_id = data['id']
        return user_id



class Category(Base):
    __tablename__ = "category"
    id = Column(Integer, primary_key=True)
    name = Column(String(60), nullable=False)
    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'id'         : self.id,
           'name'       : self.name
       }

class Item(Base):
    __tablename__ = "c_item" # this table contains the items for a specific category
    id = Column(Integer, primary_key=True)
    title = Column(String(250), nullable=False)
    description = Column(String)
    cat_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category, backref='items')
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'id'         : self.id,
           'title'      : self.title,
           'description': self.description,
           'user_id'    : self.user_id
       }


engine = create_engine(
    'sqlite:///catalogItems.db',
    connect_args={'check_same_thread': False},
    poolclass=StaticPool, echo=True
    )

Base.metadata.create_all(engine)
