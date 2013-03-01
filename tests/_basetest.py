import unittest
from nurdbar import model, NurdBar

class BaseTest(unittest.TestCase):
    def setUp(self):
        self.bar=NurdBar('test.cfg')
        self.bar.create_tables()
        self.bar.fill_tables()

    def tearDown(self):
        self.bar.drop_tables()
