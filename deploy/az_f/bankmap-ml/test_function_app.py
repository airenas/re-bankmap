import backoff

from bankmap.logger import logger


def test_pass_to_ml_retry():
    attempts = 0
    @backoff.on_exception(backoff.expo, exception=Exception, max_tries=3)
    def invoke_ml():
        nonlocal attempts
        try:
            attempts += 1
            logger.info(f'attempts: {attempts}')
            raise RuntimeError("error")
        except BaseException as err:
            logger.exception(f'FAIL ML {attempts}: {err}')
            raise

    invoke_ml()
