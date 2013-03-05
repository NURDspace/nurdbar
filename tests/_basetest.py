import unittest
from nurdbar import model, NurdBar
import os

class BaseTest(unittest.TestCase):
    def setUp(self):
        if os.path.exists(os.path.join('..','test.cfg')):
            self.bar=NurdBar(os.path.join('..','test.cfg'))
        else:
            self.bar=NurdBar('test.cfg')
        self.bar.create_tables()
        self.bar.fill_tables()

    def tearDown(self):
        self.bar.drop_tables()
