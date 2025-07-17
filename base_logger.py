# coding=utf-8
import logging

LEVEL = logging.WARN

log = logging
ch = logging.FileHandler(r'openlicita.log', encoding='utf-8')
ch.setLevel = LEVEL
log.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s', handlers = [ch], level=LEVEL, datefmt='%d/%m/%Y %I:%M:%S %p',encoding='utf-8')


logger = logging.getLogger(__name__)
level = logging.getLevelName(LEVEL)
logger.setLevel(level)
