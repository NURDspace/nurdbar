import unittest
from nurdbar import model, NurdBar, events
import os
import logging
import traceback

class BaseTest(unittest.TestCase):
    def setUp(self):
        print('Running setUp')
        if os.path.exists(os.path.join('..','test.cfg')):
            self.bar=NurdBar(os.path.join('..','test.cfg'))
        else:
            self.bar=NurdBar('test.cfg')
        global log
        self.log=logging.getLogger(__name__)
        self.log.debug('nurdbar instantiated')
        self.bar.drop_tables()
        self.log.debug('Dropped tables')
        self.bar.create_tables()
        self.log.debug('Created tables')
        self.bar.fill_tables()
        self.log.debug('Finished BaseTest setUp')

    def tearDown(self):
        self.log.debug('Running tearDown')
        try:
            self.bar.session.commit()
            self.bar.session.flush()
        except Exception:
            self.log.error("Error occured during commit:\n%s"%traceback.format_exc())
            self.bar.session.rollback()
            raise
        self.bar.drop_tables()
        for event in events.__all__:
            event.clearHandlers()
        self.log.debug('Finished BaseTest tearDown')
