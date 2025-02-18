from jsonlines import jsonlines

from bankmap.data import e_str_ne, e_date, e_date_ne, e_float, e_str_e
from bankmap.logger import logger


# loads apps
# returns array of map
def load_apps(file_name, l_entries, _type):
    l_map = {e.doc_no: e.id for e in l_entries}
    logger.info("loading {}".format(file_name))
    res = []
    with jsonlines.open(file_name) as reader:
        for (i, d) in enumerate(reader):
            if i == 0:
                logger.debug(f"Item: {d}")
            doc = e_str_e(d, 'documentNumber')
            if not doc:
                logger.warning(f"no document number in {d}")
                continue
            cv_no = l_map.get(doc, "")

            date = e_date(d, 'applicationCreatedDateTime')
            if date is None:  # close same day if not set
                date = e_date_ne(d, 'postingDate')
            if cv_no:
                res.append({'type': _type,
                            'apply_date': date,
                            'apply_amount': e_float(d, 'applicationAmount'),
                            'remaining_amount': e_float(d, 'remainingAmount'),
                            'document_number': doc,
                            'cv_number': cv_no
                            })
    logger.info(f"loaded {len(res)} rows in {file_name}")
    return res
