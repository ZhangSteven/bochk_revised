# coding=utf-8
# 

import unittest2
from os.path import join
from utils.iter import firstOf
from bochk_revised.main import getCurrentDirectory, getRawPositions



class TestALL(unittest2.TestCase):

	def __init__(self, *args, **kwargs):
		super(TestALL, self).__init__(*args, **kwargs)



	def testRawPosition(self):
		inputFile = join(getCurrentDirectory(), 'samples', 'Holding _17102019.xlsx')
		positions = list(getRawPositions(inputFile))
		self.assertEqual(19, len(positions))
		self.verifyRawPosition(
			firstOf(lambda p: p['Securities ID'] == 'XS1629465797', positions))



	def verifyRawPosition(self, position):
		self.assertEqual('DIANJIAN HAIYU LTD 3.5 31/05/22', position['Securities name'])
		self.assertEqual( 3000000.00 , position['Holding'])
		self.assertEqual('USD', position['Market Price Currency'])
		self.assertAlmostEqual(100.047, position['Market Unit Price'])
		self.assertEqual('ISIN', position['Securities ID Type'])
		self.assertEqual( 'CHINA LIFE FRANKLIN ASSET MANAGEMENT CO LTD'
						, position['Custody Account Name'])
