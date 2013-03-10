import unittest
from nurdbar import model, NurdBar
import os
import logging
log=logging.getLogger(__name__)

class BaseTest(unittest.TestCase):
    def setUp(self):
        log.debug('running setUp')
        if os.path.exists(os.path.join('..','test.cfg')):
            self.bar=NurdBar(os.path.join('..','test.cfg'))
        else:
            self.bar=NurdBar('test.cfg')
        self.bar.create_tables()
        self.bar.fill_tables()

    def tearDown(self):
        log.debug('running tearDown')
        self.bar.drop_tables()
