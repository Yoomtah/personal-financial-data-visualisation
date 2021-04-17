from ofxparse import OfxParser
from ofxparse.ofxparse import Transaction
import yaml
import logging
import pandas as pd

logging.basicConfig(level=logging.INFO)

with open('config.yaml') as config_file:
    config = yaml.load(config_file, Loader=yaml.SafeLoader)


with open(config['debit_filename']) as fileobj:
    debit_ofx = OfxParser.parse(fileobj)

with open(config['savings_filename']) as fileobj:
    savings_ofx = OfxParser.parse(fileobj)

debit_account = debit_ofx.account
debit_account_id = debit_account.account_id

savings_account = savings_ofx.account
savings_account_id = savings_account.account_id


debit_transactions = debit_account.statement.transactions
logging.debug(len(debit_transactions))

savings_transactions = savings_account.statement.transactions
logging.debug(len(savings_transactions))


debit_df = pd.DataFrame([o.__dict__ for o in debit_transactions], columns=dir(debit_transactions[0]))
debit_df.drop(columns=['__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__',
       '__format__', '__ge__', '__getattribute__', '__gt__', '__hash__',
       '__init__', '__init_subclass__', '__le__', '__lt__', '__module__',
       '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__',
       '__setattr__', '__sizeof__', '__str__', '__subclasshook__',
       '__weakref__'], inplace=True)

savings_df = pd.DataFrame([o.__dict__ for o in savings_transactions], columns=dir(savings_transactions[0]))
savings_df.drop(columns=['__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__',
       '__format__', '__ge__', '__getattribute__', '__gt__', '__hash__',
       '__init__', '__init_subclass__', '__le__', '__lt__', '__module__',
       '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__',
       '__setattr__', '__sizeof__', '__str__', '__subclasshook__',
       '__weakref__'], inplace=True)


# Remove transfers between accounts
# Sometimes first digit of account no. is replaced with a space
debit_pattern = f"INTERNET TRANSFER CREDIT FROM (?: {savings_account_id[1:]}|{savings_account_id}) REF NO \\d*"
debit_filter = debit_df['memo'].str.contains(debit_pattern)
debit_df = debit_df[~debit_filter]

savings_pattern = f"INTERNET TRANSFER DEBIT TO (?: {debit_account_id[1:]}|{debit_account_id}) REFERENCE NO \\d*"
savings_filter = savings_df['memo'].str.contains(savings_pattern)
savings_df = savings_df[~savings_filter]

debit_df['expense_category'] = pd.Series(dtype='string')

def assign_expense_category(row):
    for item in config['expense-categories']:
        for category_key in item:
            for target_string in item[category_key]:
                if target_string in row['memo']:
                    return category_key


debit_df['expense_category'] = debit_df.apply(assign_expense_category, axis=1)
debit_df['expense_category'] = debit_df['expense_category'].fillna("Uncategorised")


logging.info(debit_df.groupby(['expense_category']).count())