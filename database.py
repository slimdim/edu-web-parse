from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import models


class Database:
    def __init__(self, db_url):
        engine = create_engine(db_url)
        models.Base.metadata.create_all(bind=engine)
        self.session_m = sessionmaker(bind=engine)

    @staticmethod
    def get_or_create(session, model, is_comment=False, **data):
        if is_comment:
            db_model = session.query(model).filter(model.gb_id == data['gb_id']).first()
            if not db_model:
                db_model = model(**data)
            return db_model
        else:
            db_model = session.query(model).filter(model.url == data['url']).first()
            if not db_model:
                db_model = model(**data)
            return db_model

    def create_post(self, data: dict):
        session = self.session_m()
        tags = map(lambda tag_data: self.get_or_create(session, models.Tag, **tag_data), data['tags'])
        comments = map(lambda comment_data: self.get_or_create(session, models.Comment, True, **comment_data),
                       data['comments'])
        author = self.get_or_create(session, models.Author, **data['author'])
        post = self.get_or_create(session, models.Post, **data['post_data'])
        post.author = author
        post.tags.extend(tags)
        post.comment.extend(comments)
        session.add(post)

        try:
            session.commit()
        except Exception as e:
            print(e)
            session.rollback()
        finally:
            print(post.title)
            session.close()
