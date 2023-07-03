import sqlalchemy as sq
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import Session
from config import db_url_object

metadata = MetaData()
base = declarative_base()
engine = create_engine(db_url_object)


class Processed(base):
    __tablename__ = 'processed'
    user_id = sq.Column(sq.Integer, primary_key=True)
    searched_id = sq.Column(sq.Integer, primary_key=True)


# Добавляем в БД запись
def add_user(engine, user_id, searched_id):
    with Session(engine) as session:
        to_bd = Processed(user_id=user_id, searched_id=searched_id)
        session.add(to_bd)
        session.commit()


# Извлекаем запись из БД
def check_user(engine, user_id, searched_id):
    with Session(engine) as session:
        from_bd = session.query(Processed).filter(
            Processed.user_id == user_id,
            Processed.searched_id == searched_id
        ).first()
        return True if from_bd else False


if __name__ == '__main__':
    base.metadata.create_all(engine)
