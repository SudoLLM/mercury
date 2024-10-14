import datetime
import os

import databases
import ormar
import sqlalchemy

DATABASE_URL = os.getenv("DATABASE_URL")

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()
engine = sqlalchemy.create_engine(DATABASE_URL)

base_ormar_config = ormar.OrmarConfig(database=database, metadata=metadata, engine=engine)


class BaseModel(ormar.Model):
    ormar_config = base_ormar_config.copy(abstract=True)

    id: int = ormar.Integer(primary_key=True, autoincrement=True)
    create_time: datetime.datetime = ormar.DateTime(default=datetime.datetime.now)
