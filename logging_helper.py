'''
ArwicBot Logging Helper
'''
import logging
import os
import constants



def init_logger(id):
    logger = logging.getLogger(id)
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler("{}{}{}".format(constants.LOG_DIR, id, constants.LOG_EXT))
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s')
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)
    logger.addHandler(ch)
    logger.addHandler(fh)
    return logger