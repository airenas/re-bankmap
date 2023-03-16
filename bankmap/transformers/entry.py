import pandas as pd
from tqdm import tqdm

from bankmap.data import e_str, e_date
from bankmap.logger import logger


# loads data from Customer_Recognitions or Vendor_Recognitions
# returns map or [statement no][[[mapper_internal doss], customer_no]]
# _type = [Cust, Vend]
def load_docs_map(file_name, _type: str):
    logger.info("loading entries {}".format(file_name))
    df = pd.read_csv(file_name, sep=',')
    logger.info("loaded entries {} rows".format(len(df)))
    logger.debug("{}".format(df.head(n=10)))
    logger.debug("Headers: {}".format(list(df)))
    skip = 0
    res = {}
    with tqdm("read entries", total=len(df)) as pbar:
        for i in range(len(df)):
            pbar.update(1)
            id = e_str(df['Statement_External_Document_No_'].iloc[i])
            st_date = e_date(df[_type + '_Posting_Date'].iloc[i])
            doc_date = e_date(df['Applied_' + _type + '_Document_Date'].iloc[i])
            cv = e_str(df['Vend_Vendor_No_' if _type == "Vend" else 'Cust_Customer_No_'].iloc[i])
            if st_date < doc_date:
                skip += 1
                continue
            iid = e_str(df['Applied_' + _type + '_Document_No_'].iloc[i])
            ra = res.get(id, (set(), cv))
            ra[0].add(iid)
            res[id] = ra
    logger.debug("skipped future docs: {}".format(skip))
    return res
