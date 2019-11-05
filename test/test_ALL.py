# coding=utf-8
# 

import unittest2
from os.path import join
from nomura.main import getCurrentDirectory, getRawPositions



class TestALL(unittest2.TestCase):

	def __init__(self, *args, **kwargs):
		super(TestALL, self).__init__(*args, **kwargs)



	def testRawPosition(self):
		inputFile = join(getCurrentDirectory(), 'samples', 'Holding _17102019.xlsx')
		positions = list(getRawPositions(inputFile))
		self.assertEqual(23, len(positions))
