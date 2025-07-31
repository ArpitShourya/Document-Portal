import traceback,sys
from logger.custom_logger import CustomLogger
logger=CustomLogger().get_logger(__file__)

class DocumentPortalException(Exception):
    def __init__(self, error_msg):
        exc_type,exc_value,exc_tb=sys.exc_info()
        self.file_name=exc_tb.tb_frame.f_code.co_filename
        self.line_no=exc_tb.tb_lineno
        self.error_msg=str(error_msg)
        self.traceback_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))

    def __str__(self):
        return f""" Error in [{self.file_name}] at line [{self.line_no}]
        Message: {self.error_msg}
        Traceback:
        {self.traceback_str}"""
    
if __name__ == "__main__":
    try:
        # Simulate an error
        a = 1 / 0
        print(a)
    except Exception as e:
        app_exc=DocumentPortalException(e)
        logger.error(app_exc)
        raise app_exc