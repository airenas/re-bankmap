from jsonlines import jsonlines

from bankmap.data import TextToAccountMap, LType, e_str
from bankmap.logger import logger


def load_text_to_accounts(file_name):
    logger.info("loading {}".format(file_name))
    res = []
    with jsonlines.open(file_name) as reader:
        for (i, d) in enumerate(reader):
            if i == 0:
                logger.debug(f"Item: {d}")
            try:
                if LType.supported(d['balSourceType']):
                    res.append(TextToAccountMap(type_v=LType.from_s(e_str(d['balSourceType'])),
                                                text=e_str(d.get('mappingText')),
                                                account=e_str(d.get('balSourceNumber')),
                                                credit_account=e_str(d.get('creditAccountNumber')),
                                                debit_account=e_str(d.get('debitAccountNumber')),
                                                ))
            except BaseException as err:
                raise RuntimeError(f"wrong data: {str(err)}")

    logger.info(f"loaded {len(res)} rows")
    return res
