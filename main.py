# coding=utf-8
#
# Read BOCHK holding and cash reports, convert them to Geneva holding and cash
# format.
# 
# Program structure very similar to nomura.main.py
# 

from itertools import chain, groupby
from functools import partial
from datetime import datetime
from utils.utility import dictToValues, writeCsv
from utils.iter import pop, firstOf
from toolz.functoolz import compose
from toolz.itertoolz import groupby as groupbyToolz
from nomura.main import fileToLines, getHeadersnLines, getCashHeaders \
						, getHoldingHeaders, getOutputFileName
from os.path import join, dirname, abspath
import re
import logging
logger = logging.getLogger(__name__)




"""
	[Dictionary] p (raw holding position) => 
		[Dictionary] Geneva holding position
"""
holdingPosition = lambda date, p: \
	(lambda d1, d2: \
		{**d1, **d2}
	)\
	( { 'portfolio': p['Custody Account Name']
	  , 'custodian': ''
	  , 'date': date
	  , 'name': p['Securities name'].strip()
	  , 'currency': p['Market Price Currency']
	  , 'quantity': p['Holding']
	  }
	, (lambda t: \
		{'ISIN': t[0], 'bloomberg_figi': t[1], 'geneva_investment_id': t[2]}
	  )(getSecurityIds(p['Custody Account Name'], p['Securities ID Type'], p['Securities ID']))
	)



"""
	[Dictionary] p (raw cash position) => 
		[Dictionary] Geneva cash position
"""
cashPosition = lambda date, p: \
	{ 'portfolio': p['Account Name']
	, 'custodian': ''
	, 'date': date
	, 'currency': p['Currency']
	, 'balance': p['Current Ledger Balance']
	}



"""
	[String] accountName, [String] idType, [String] idNumber =>
		(isin, bloomberg FIGI, geneva invest id)
"""
getSecurityIds = lambda accountName, idType, idNumber: \
	getSecurityIdsFromISIN(accountName, idNumber) if idType == 'ISIN' else \
	(lambda t: \
		('', t[1], '') if t[0] == '' else getSecurityIdsFromISIN(accountName, t[0])
	)(lookupSecurityId(idType, idNumber))



"""
	[String] accountName, [String] isin =>
		(isin, bloomberg FIGI, geneva invest id)
"""
getSecurityIdsFromISIN = lambda accountName, isin: \
	('', '', isin + ' HTM') if isHTMPortfolio(accountName) and \
		not afsBondinHTM(accountName, isin) else (isin, '', '')



isHTMPortfolio = lambda accountName: \
	True if accountName in \
		[ 'CLT - CLI MACAU BR (CLASS A-MC) TRUST FUND (BOND)'
		, 'CLT - CLI MACAU BR (CLASS A-MC) TRUST FD (BD)-PAR'
		, 'CLT - CLI HK BR (CLASS A-HK) TRUST FD (BOND)- PAR'
		, 'CLT - CLI HK BR (CLASS A-HK) TRUST FUND (BOND)'
		, 'CLT - CLI HK BR (CLASS G-HK) TRUST FUND (BOND)'
		, 'CHINA LIFE FRANKLIN ASSET MANAGEMENT CO LTD'	# 20051
		] \
	else False



def afsBondinHTM(accountName, isin):
	"""
	[String] accountName, [String] isin => [Bool] Yes/No

	HTM portfolios sometimes contain available for sale or trading bonds,
	those bonds are stored in an Excel file for us to lookup.
	"""
	def loadList():
		logger.info('afsBondinHTM(): load mapping from file')
		lines = fileToLines('AFS Bond in HTM Portfolios.xlsx')
		pop(lines)	# skip headers
		return list(map(lambda line: (line[0].strip(), line[1].strip()), lines))

	if not hasattr(afsBondinHTM, 'localList'):
		afsBondinHTM.localList = loadList()

	return (accountName, isin) in afsBondinHTM.localList



def lookupSecurityId(idType, idNumber):
	"""
	[String] idType, [String] idNumber =>
		([String] ISIN, [String] Bloomberg FIGI)

	Read an Excel to lookup the security's ISIN code and Bloomberg FIGI code
	if the security id type is not ISIN.
	"""
	def loadMapping():
		logger.info('lookupSecurityId(): load mapping from file')
		lines = fileToLines('Security Id Lookup.xlsx')
		pop(lines)	# skip headers
		return dict(map( lambda line: ( (line[0].strip(), line[1].strip())
									  , (line[3].strip(), line[4].strip())
									  )
					   , lines))

	if not hasattr(lookupSecurityId, 'localMap'):
		lookupSecurityId.localMap = loadMapping()

	return lookupSecurityId.localMap[(idType, idNumber)]



filenameWithoutPath = lambda filename: \
	filename.split('\\')[-1]



"""
	[String] fn => [String] date (yyyy-mm-dd)

	fn is filename without path

	Date can either appear as yyyy-mm-dd or ddmmyyyy in the file name, like:

	BOC Broker Statement 2019-11-04 (A-MC).xls
	Cash Stt _04112019.xlsx
	BOC Bank Statement 2019-11-01 (Class A-MC BOND) (HKD).xls
"""
dateFromFilename = lambda fn: \
	(lambda m: \
		(lambda s: datetime.strptime(s, '%d%m%Y').strftime('%Y-%m-%d'))(m.group(0)) \
		if m != None else \
		(lambda m2: \
			m2.group(0)	if m2 != None else throwValueError('dateFromFilename(): {0}'.format(fn))
		)(re.search('[0-9]{4}-[0-9]{2}-[0-9]{2}', fn))
	)(re.search('[0-9]{8}', fn))




"""
	[String] filename (full path) => [String] date (yyyy-mm-dd)
"""
dateFromFilenameFull = compose(
	  dateFromFilename
	, filenameWithoutPath
)



def throwValueError(msg):
	raise ValueError(msg)



def skip2(it):
	"""
	[Iterable] it => [Iterable] it, with the first 2 elements skipped

	NOT a pure function, the input iterator is changed.
	"""
	pop(it)
	pop(it)
	return it



isCashFile = lambda inputFile: \
	(lambda fn: \
		fn.startswith('cash stt') or \
		fn.startswith('boc bank statement')
	)(filenameWithoutPath(inputFile).lower())



"""
	[String] inputFile => [Iterable] cash positions for Geneva reconciliation
"""
getCashPositions = lambda inputFile: \
	map( partial(cashPosition, dateFromFilenameFull(inputFile))
	   , getRawCashPositions(inputFile))



"""
	[String] intputFile => [Iterable] positions for Geneva reconciliation
"""
getHoldingPositions = lambda inputFile: \
	map( partial(holdingPosition, dateFromFilenameFull(inputFile))
	   , getRawHoldingPositions(inputFile))



"""
	[String] file => [Iterable] positions

	position: [Dictionary] header -> value
"""
getRawHoldingPositions = compose(
	  lambda t: map(lambda line: dict(zip(t[0], line)), t[1])
	, lambda t: ( t[0]
				, filter( lambda line: line[0] == 'Sub-Total'
						, filter( lambda line: line[0] != '' and line[4] != 'All'
								, t[1]))
				)
	, getHeadersnLines
	, skip2
	, fileToLines
)



"""
	[String] file => [Iterable] cash positions

	We need to handle two challenges here:

	(1) cash belonging to the same account number can show up in multiple
		lines.
	(2) cash of the same currency can belong to multiple accounts.
"""
getRawCashPositions = compose(
	  lambda t: map(lambda line: dict(zip(t[0], line)), t[1])
	, lambda t: ( t[0]
				, map( consolidate
					 , groupbyToolz(lambda line: line[3], t[1]).values())
				)
	, lambda t: ( t[0]
				, map( lambda keynGroup: pop(keynGroup[1])
					 , groupby(t[1], lambda line: line[1]))
				)
	, getHeadersnLines
	, fileToLines
)



def consolidate(lineGroup):
	"""
	[List] lineGroup => [Iterable] line

	where lineGroup is a group of lines of the same currency, we need to
	add up their ledger balance
	"""
	r = lineGroup[0].copy()
	r[7] = sum(map(lambda L: L[7], lineGroup))
	return r



"""
	Get the absolute path to the directory where this module is in.

	This piece of code comes from:

	http://stackoverflow.com/questions/3430372/how-to-get-full-path-of-current-files-directory-in-python
"""
getCurrentDirectory = lambda: \
	dirname(abspath(__file__))



"""
	[String] inputFile, [String] outputDir => [String] output csv file

	side effect: write the output csv file in the output directory
"""
outputCsv = lambda inputFile, outputDir: \
	writeCsv( getOutputFileName( inputFile
							   , '_bochk_' + dateFromFilenameFull(inputFile) + '_cash'
							   , outputDir)
			, chain( [getCashHeaders()]
			   	   , map( partial(dictToValues, getCashHeaders())
			   	   		, getCashPositions(inputFile)))
			, delimiter='|') \
	if isCashFile(inputFile) else \
	writeCsv( getOutputFileName( inputFile
							   , '_bochk_' + dateFromFilenameFull(inputFile) + '_position'
							   , outputDir)
			, chain( [getHoldingHeaders()]
			   	   , map( partial(dictToValues, getHoldingHeaders())
			   	   		, getHoldingPositions(inputFile)))
			, delimiter='|')



if __name__ == '__main__':
	import logging.config
	logging.config.fileConfig('logging.config', disable_existing_loggers=False)

	print(outputCsv(join(getCurrentDirectory(), 'samples', 'Cash Stt _04112019.xlsx'), ''))
	print(outputCsv(join(getCurrentDirectory(), 'samples', 'BOC Broker Statement 2019-11-01.xls'), ''))
	print(outputCsv(join(getCurrentDirectory(), 'samples', 'Holding _17102019.xlsx'), ''))
	print(outputCsv(join(getCurrentDirectory(), 'samples', 'BOC Bank Statement 2019-11-05 (Class A-HK BOND) - Par (USD).xls'), ''))