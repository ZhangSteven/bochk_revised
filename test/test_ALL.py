# coding=utf-8
# 

import unittest2
from os.path import join
from utils.iter import firstOf
from functools import partial
from bochk_revised.main import getCurrentDirectory, getRawHoldingPositions\
								, holdingPosition, dateFromFilenameFull\
								, filenameWithoutPath, cashPosition\
								, getRawCashPositions



class TestALL(unittest2.TestCase):

	def __init__(self, *args, **kwargs):
		super(TestALL, self).__init__(*args, **kwargs)



	def testRawPosition(self):
		inputFile = join(getCurrentDirectory(), 'samples', 'Holding _17102019.xlsx')
		positions = list(getRawHoldingPositions(inputFile))
		self.assertEqual(19, len(positions))
		self.verifyRawPosition(
			firstOf(lambda p: p['Securities ID'] == 'XS1629465797', positions))



	def testDateFromFilename(self):
		self.assertEqual( '2019-11-04'
						, dateFromFilenameFull('BOC Broker Statement 2019-11-04 (A-MC).xls'))
		self.assertEqual( '2019-11-04'
						, dateFromFilenameFull('Cash Stt _04112019.xlsx'))
		self.assertEqual( '2019-11-01'
						, dateFromFilenameFull('BOC Bank Statement 2019-11-01 (Class A-MC BOND) (HKD).xls'))



	def testDateFromFilenameError(self):
		try:
			dateFromFilenameFull('BOC Broker Statement 12312019')
		except ValueError:	# date format should be ddmmyyyy instead of mmddyyyy
			pass
		else:
			self.fail('Error should have occurred')



	def testDateFromFilenameError2(self):
		try:
			dateFromFilenameFull('BOC Broker Statement 2019-1130')
		except ValueError:	# no pattern of date found in file name
			pass
		else:
			self.fail('Error should have occurred')



	def testHoldingPosition(self):
		inputFile = join(getCurrentDirectory(), 'samples', 'Holding _17102019.xlsx')
		positions = list(map( partial(holdingPosition, dateFromFilenameFull(inputFile))
							, getRawHoldingPositions(inputFile)))
		self.assertEqual(19, len(positions))
		self.verifyPosition(
			firstOf(lambda p: p['name'] == 'CMHI FINA BVI CO 06/08/2023', positions))
		self.verifyPosition2(
			firstOf(lambda p: p['name'] == 'CHINA CINDA FINANCE 4.25 23/04/25', positions))



	def testHoldingPosition2(self):
		inputFile = join(getCurrentDirectory(), 'samples', 'BOC Broker Statement 2019-11-01.xls')
		positions = list(map( partial(holdingPosition, dateFromFilenameFull(inputFile))
							, getRawHoldingPositions(inputFile)))
		self.assertEqual(159, len(positions))
		self.verifyPosition3(
			firstOf(lambda p: p['name'] == 'NWD MTN LTD 6 18/09/2023', positions))



	def testHoldingPosition3(self):
		inputFile = join(getCurrentDirectory(), 'samples', 'BOC Broker Statement 2019-11-04 (A-MC).xls')
		positions = list(map( partial(holdingPosition, dateFromFilenameFull(inputFile))
							, getRawHoldingPositions(inputFile)))
		self.assertEqual(55, len(positions))
		self.verifyPosition4(
			firstOf(lambda p: p['name'] == 'CHINA STATE CON 6 31/12/49', positions))



	def testCashPosition(self):
		inputFile = join(getCurrentDirectory(), 'samples', 'Cash Stt _04112019.xlsx')
		positions = list(map( partial(cashPosition, dateFromFilenameFull(inputFile))
							, getRawCashPositions(inputFile)))
		self.assertEqual(4, len(positions))
		self.verifyCashPosition(
			firstOf(lambda p: p['currency'] == 'CNY', positions))
		self.verifyCashPosition2(
			firstOf(lambda p: p['currency'] == 'USD', positions))
		self.verifyCashPosition3(
			firstOf(lambda p: p['currency'] == 'HKD', positions))



	def testCashPosition2(self):
		inputFile = join( getCurrentDirectory()
						, 'samples', 'BOC Bank Statement 2019-11-05 (Class A-HK BOND) - Par (USD).xls')
		positions = list(map( partial(cashPosition, dateFromFilenameFull(inputFile))
							, getRawCashPositions(inputFile)))
		self.assertEqual(1, len(positions))
		self.verifyCashPosition4(positions[0])



	def verifyRawPosition(self, position):
		self.assertEqual('DIANJIAN HAIYU LTD 3.5 31/05/22', position['Securities name'])
		self.assertEqual(3000000.00 , position['Holding'])
		self.assertEqual('USD', position['Market Price Currency'])
		self.assertAlmostEqual(100.047, position['Market Unit Price'])
		self.assertEqual('ISIN', position['Securities ID Type'])
		self.assertEqual( 'CHINA LIFE FRANKLIN ASSET MANAGEMENT CO LTD'
						, position['Custody Account Name'])



	def verifyPosition(self, position):
		self.assertEqual('CHINA LIFE FRANKLIN ASSET MANAGEMENT CO LTD', position['portfolio'])
		self.assertEqual('', position['custodian'])
		self.assertEqual('2019-10-17', position['date'])
		self.assertEqual('USD', position['currency'])
		self.assertEqual(3000000.00, position['quantity'])
		self.assertEqual('XS1856799421', position['ISIN'])
		self.assertEqual('', position['bloomberg_figi'])
		self.assertEqual('XS1856799421 HTM', position['geneva_investment_id'])



	def verifyPosition2(self, position):
		self.assertEqual('CHINA LIFE FRANKLIN ASSET MANAGEMENT CO LTD', position['portfolio'])
		self.assertEqual('', position['custodian'])
		self.assertEqual('2019-10-17', position['date'])
		self.assertEqual('USD', position['currency'])
		self.assertEqual(1000000.00, position['quantity'])
		self.assertEqual('USG21184AB52', position['ISIN'])
		self.assertEqual('', position['bloomberg_figi'])
		self.assertEqual('USG21184AB52 HTM', position['geneva_investment_id'])



	def verifyPosition3(self, position):
		self.assertEqual('CLT - CLI HK BR (CLASS A-HK) TRUST FD (BOND)- PAR', position['portfolio'])
		self.assertEqual('', position['custodian'])
		self.assertEqual('2019-11-01', position['date'])
		self.assertEqual('HKD', position['currency'])
		self.assertEqual(200000000, position['quantity'])
		self.assertEqual('HK0000163607', position['ISIN'])
		self.assertEqual('', position['bloomberg_figi'])
		self.assertEqual('HK0000163607 HTM', position['geneva_investment_id'])



	def verifyPosition4(self, position):
		self.assertEqual('CLT - CLI MACAU BR (CLASS A-MC) TRUST FUND (BOND)', position['portfolio'])
		self.assertEqual('', position['custodian'])
		self.assertEqual('2019-11-04', position['date'])
		self.assertEqual('USD', position['currency'])
		self.assertEqual(20000000, position['quantity'])
		self.assertEqual('XS1912494538', position['ISIN'])
		self.assertEqual('', position['bloomberg_figi'])
		self.assertEqual('XS1912494538 HTM', position['geneva_investment_id'])



	def verifyCashPosition(self, position):
		self.assertEqual('CHINA LIFE FRANKLIN ASSET MANAGEMENT CO LTD', position['portfolio'])
		self.assertEqual('', position['custodian'])
		self.assertEqual('2019-11-04', position['date'])
		self.assertAlmostEqual(6.91, position['balance'])



	def verifyCashPosition2(self, position):
		self.assertEqual('CHINA LIFE FRANKLIN ASSET MANAGEMENT CO LTD', position['portfolio'])
		self.assertEqual('', position['custodian'])
		self.assertEqual('2019-11-04', position['date'])
		self.assertAlmostEqual(148465.26, position['balance'])



	def verifyCashPosition3(self, position):
		self.assertEqual('CHINA LIFE FRANKLIN ASSET MANAGEMENT CO LTD', position['portfolio'])
		self.assertEqual('', position['custodian'])
		self.assertEqual('2019-11-04', position['date'])
		self.assertAlmostEqual(38.52, position['balance'])



	def verifyCashPosition4(self, position):
		self.assertEqual('CLT - CLI HK BR (CLASS A-HK) TRUST FUND (BOND)- PAR', position['portfolio'])
		self.assertEqual('', position['custodian'])
		self.assertEqual('2019-11-05', position['date'])
		self.assertEqual('USD', position['currency'])
		self.assertAlmostEqual(79130312.05, position['balance'])