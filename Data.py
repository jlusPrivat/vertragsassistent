from peewee import *


db = SqliteDatabase(None)


def create_tables() -> None:
    db.create_tables([Contract, ContractPricing, ContractDocument, ContractTag, ContractTagConnection])


class BaseModel(Model):
    class Meta:
        database = db


class Contract(BaseModel):
    name = CharField()
    company = CharField()
    notes = TextField()
    reminder = DateField(null=True)


class ContractPricing(BaseModel):
    contract = ForeignKeyField(Contract, backref='contract')
    price = DecimalField()
    payment_interval_days = IntegerField()
    start_date = DateField()
    end_date = DateField(null=True)


class ContractTag(BaseModel):
    name = CharField()


class ContractTagConnection(BaseModel):
    contract = ForeignKeyField(Contract, backref='tag')
    tag = ForeignKeyField(ContractTag, backref='tag')


class ContractDocument(BaseModel):
    contract = ForeignKeyField(Contract, backref='contract')
    file = CharField()
    description = CharField()
    date = DateField()
