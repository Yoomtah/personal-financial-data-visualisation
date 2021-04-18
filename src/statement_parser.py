from ofxparse import OfxParser
import yaml
import logging
import pandas as pd
logging.basicConfig(level=logging.INFO)

with open('actual_config.yaml') as config_file:
    config = yaml.load(config_file, Loader=yaml.SafeLoader)


def assign_category(row):
    if row['type'] == "Expense":
        config_key = 'expense-categories'
    else:
        config_key = 'income-categories'
    for item in config[config_key]:
        for category_key in item:
            for target_string in item[category_key]:
                if target_string in row['memo']:
                    return category_key, target_string
    return "Uncategorised", "Uncategorised"


def assign_type(amount):
    if amount >= 0:
        return "Income"
    return "Expense"


def parse_ofx_statements():
    with open(config['debit_filename']) as fileobj:
        debit_ofx = OfxParser.parse(fileobj)

    with open(config['savings_filename']) as fileobj:
        savings_ofx = OfxParser.parse(fileobj)

    debit_account_id = debit_ofx.account.account_id
    savings_account_id = savings_ofx.account.account_id

    debit_transactions = debit_ofx.account.statement.transactions
    logging.debug(len(debit_transactions))
    savings_transactions = savings_ofx.account.statement.transactions
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

    debit_df['account'] = "debit"
    savings_df['account'] = "savings"

    frames = [debit_df, savings_df]
    merged_df = pd.concat(frames)
    merged_df['date_formatted'] = merged_df['date'].apply(lambda d: d.strftime('%Y-%m-%d'))

    merged_df['type'] = pd.Series(dtype='string')

    merged_df['amount'] = merged_df['amount'].astype(float)
    merged_df['type'] = merged_df['amount'].map(assign_type)
    merged_df['category'] = pd.Series(dtype='string')
    merged_df['subcategory'] = pd.Series(dtype='string')

    merged_df['category'], merged_df['subcategory'] = zip(*merged_df.apply(assign_category, axis=1))
    merged_df['category'] = merged_df['category'].fillna("Uncategorised")
    merged_df['subcategory'] = merged_df['subcategory'].fillna("Uncategorised")
   
    return merged_df
