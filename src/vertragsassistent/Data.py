from peewee import *
import datetime
import os.path


db = SqliteDatabase(None)


def create_tables() -> None:
    db.create_tables([Contract, ContractPricing, ContractDocument, ContractTag,
                      ContractTag.contracts.get_through_model()])


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

    @property
    def is_active(self) -> bool:
        today = datetime.date.today()
        return today >= self.start_date and (self.end_date is None or today <= self.end_date)


class ContractTag(BaseModel):
    name = CharField()
    contracts = ManyToManyField(Contract, backref='tags')


class ContractDocument(BaseModel):
    contract = ForeignKeyField(Contract, backref='contract')
    file = TextField()
    description = CharField()
    date = DateField()

    @property
    def absolute_file(self):
        return os.path.join(os.path.dirname(db.database), str(self.file))

    @property
    def file_exists(self):
        return os.path.isfile(self.absolute_file)
