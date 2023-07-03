import sqlalchemy as sq
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import Session

from config import db_url_object

metadata = MetaData()
base = declarative_base()

engine = create_engine(db_url_object)

"""CREATE DATABASE student_diplom
    WITH
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'Russian_Russia.1251'
    LC_CTYPE = 'Russian_Russia.1251'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1
    IS_TEMPLATE = False;
"""


class Processed(base):
    __tablename__ = 'processed'
    user_id = sq.Column(sq.Integer, primary_key=True)
    searched_id = sq.Column(sq.Integer, primary_key=True)


"""CREATE TABLE IF NOT EXISTS public.viewed
(
    profile_id integer NOT NULL,
    worksheet_id integer NOT NULL,
    CONSTRAINT viewed_pkey PRIMARY KEY (profile_id, worksheet_id)
)
"""


# Добавляем в БД запись


def add_user(engine, user_id, searched_id):
    with Session(engine) as session:
        to_bd = Processed(user_id=user_id, searched_id=searched_id)
        session.add(to_bd)
        session.commit()


"""INSERT INTO public.viewed (profile_id, worksheet_id)
   VALUES (1, 123);
"""


# Извлекаем запись из БД

def check_user(engine, user_id, searched_id):
    with Session(engine) as session:
        from_bd = session.query(Processed).filter(
            Processed.user_id == user_id,
            Processed.searched_id == searched_id
        ).first()
        return True if from_bd else False


"""-- Извлечение всех данных из таблицы viewed
SELECT * FROM public.viewed;

-- Извлечение данных только для определенного профиля
SELECT * FROM public.viewed WHERE profile_id = 123;

-- Извлечение данных только для определенного worksheet_id
SELECT * FROM public.viewed WHERE worksheet_id = 456;
"""

if __name__ == '__main__':
    base.metadata.create_all(engine)
