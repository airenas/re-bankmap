import pandas as pd

from bankmap.data import TextToAccountMap
from bankmap.logger import logger

text_to_account_map_cols = ['Text', 'Type', 'Account', 'Credit_Account', 'Debit_Account']


def load_text_to_accounts(file_name):
    logger.info("loading text_to_accounts {}".format(file_name))
    df = pd.read_csv(file_name, sep=',', dtype={x: 'str' for x in
                                                ['Mapping_Text', 'Bal__Source_Type', 'Bal__Source_No_',
                                                 'Credit_Acc__No_', 'Debit_Acc__No_']})
    return load_text_to_accounts_df(df)


def load_text_to_accounts_df(df):
    res_data = []
    data = df.to_dict('records')
    for d in data:
        res_data.append([d['Mapping_Text'], d['Bal__Source_Type'], d['Bal__Source_No_'], d['Credit_Acc__No_'],
                         d['Debit_Acc__No_']])
    res = [TextToAccountMap(d) for d in pd.DataFrame(res_data, columns=text_to_account_map_cols).to_dict('records')]
    res.sort(key=lambda e: -len(e.text))
    return res
