from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship

Base = declarative_base()


class MixIdUrl:
    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String, nullable=False, unique=True)


tag_post = Table(
    'tag_post',
    Base.metadata,
    Column('post_id', Integer, ForeignKey('post.id')),
    Column('tag_id', Integer, ForeignKey('tag.id'))
)


class Post(Base, MixIdUrl):
    __tablename__ = 'post'
    title = Column(String, nullable=False)
    post_datetime = Column(DateTime, nullable=False)
    image = Column(String)
    author_id = Column(Integer, ForeignKey('author.id'))
    author = relationship('Author')
    tags = relationship('Tag', secondary=tag_post)
    comment = relationship('Comment')


class Author(Base, MixIdUrl):
    __tablename__ = 'author'
    name = Column(String, nullable=False)
    posts = relationship('Post')


class Tag(Base, MixIdUrl):
    __tablename__ = 'tag'
    name = Column(String, nullable=False)
    posts = relationship('Post', secondary=tag_post)


class Comment(Base):
    __tablename__ = 'comment'
    id = Column(Integer, primary_key=True, autoincrement=True)
    gb_id = Column(Integer, nullable=False)
    post_id = Column(Integer, ForeignKey('post.id'))
    parent_id = Column(Integer, ForeignKey("comment.id"))
    parent = relationship("Comment")
    author = Column(String, nullable=False)
    body = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    posts = relationship('Post')

