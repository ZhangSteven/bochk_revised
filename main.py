# coding=utf-8
#
# Read BOCHK holding and cash reports, convert them to Geneva holding and cash
# format.
# 
# Program structure very similar to nomura.main.py
# 

from itertools import chain, groupby
from functools import partial
from utils.utility import dictToValues, writeCsv
from utils.iter import pop
from toolz.functoolz import compose
from nomura.main import fileToLines, getHeadersnLines, getCashHeaders \
						, getHoldingHeaders, getOutputFileName
from os.path import join, dirname, abspath
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
	  , 'name': p['Securities name']
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
	{ 'portfolio': p['Portfolio']\
	, 'custodian': ''\
	, 'date': date\
	, 'currency': p['account_ccy_code']\
	, 'balance': stringToFloat(p['ledger_bal_in_acct_ccy'])\
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



def skip2(it):
	"""
	[Iterable] it => [Iterable] it, with the first 2 elements skipped

	NOT a pure function, the input iterator is changed.
	"""
	pop(it)
	pop(it)
	return it



"""
	[Iterable] group of lines => [Iterable] single line

	For each holding position, the "Holding Details" line (1st line in group) 
	contains trade day quantity, the "Sub-Total" line (2nd line in group) 
	contains currency, price etc. We need to merge them into a single line.
"""
consolidate = lambda group: \
	map( lambda t: t[0] if t[0] != '' else t[1]
	   , zip(pop(group), pop(group)))



"""
	[String] file => [Iterable] positions

	position: [Dictionary] header -> value
"""
getRawHoldingPositions = compose(
	  lambda t: map(lambda line: dict(zip(t[0], line)), t[1])
	, lambda t: ( t[0]
				, map( lambda keynGroup: consolidate(keynGroup[1])
	   				 , groupby(t[1], lambda line: line[8]))
				)
	, lambda t: ( t[0]
				, filter(lambda line: line[0] != '' and line[4] != 'All', t[1])
				)
	, getHeadersnLines
	, skip2
	, fileToLines
)



"""
	Get the absolute path to the directory where this module is in.

	This piece of code comes from:

	http://stackoverflow.com/questions/3430372/how-to-get-full-path-of-current-files-directory-in-python
"""
getCurrentDirectory = lambda: \
	dirname(abspath(__file__))




if __name__ == '__main__':
	import logging.config
	logging.config.fileConfig('logging.config', disable_existing_loggers=False)

	inputFile = join(getCurrentDirectory(), 'samples', 'Holding _17102019.xlsx')
	for p in map( partial(holdingPosition, '2019-10-17')
				, getRawHoldingPositions(inputFile)):
		print(p)