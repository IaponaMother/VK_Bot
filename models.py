from peewee import *
db = SqliteDatabase('my_database1.db')


class BaseModel(Model):
    id = PrimaryKeyField(unique=True)

    class Meta:
        database = db
        order_by = 'id'



class Users(BaseModel):
    vkId = IntegerField()
    name = CharField()
    lastname = CharField()

    class Meta:
        db_table = 'Users'



class Genres(BaseModel):
    name = CharField()

    class Meta:
        db_table = 'Genres'



class Preferences(BaseModel):
    userId = ForeignKeyField(Users)
    genreId = ForeignKeyField(Genres)

    class Meta:
        db_table = 'Preferences'