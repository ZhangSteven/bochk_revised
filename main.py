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
	{ 'portfolio': p['Custody Account Name']
	, 'custodian': ''
	, 'date': date
	, 'geneva_investment_id': ''
	, 'ISIN': '' 
	, 'bloomberg_figi': ''
	, 'name': p['Securities name']
	, 'currency': p['Market Price Currency']
	, 'quantity': p['Holding']
	}



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


def skip2(it):
	"""
	[Iterable] it => [Iterable] it, with the first 2 elements skipped

	NOT a pure function, the input iterator is changed.
	"""
	pop(it)
	pop(it)
	return it



"""
	[String] file => [String] date (yyyy-mm-dd), [Iterable] positions
"""
getPositions = lambda file: \
	( dateFromFilename(file)\
	, map( partial(addDictValue, 'Portfolio', portfolioFromFileName(file))\
		 , getRawPositions(file))
	)



"""
	[Iterable] group of lines => [Iterable] single line

	For each holding position, the "Holding Details" line contains
	trade day quantity, the "Sub-Total" line contains currency, price.
	We need to merge them into a single line.
"""
consolidate = lambda group: \
	map( lambda t: t[0] if t[0] != '' else t[1]
	   , zip(pop(group), pop(group)))



"""
	[String] file => [Iterable] positions

	position: [Dictionary] header -> value
"""
getRawPositions = compose(
	  lambda t: map(lambda line: dict(zip(t[0], line)), t[1])
	, lambda t: ( t[0]
				, map( lambda keynGroup: consolidate(keynGroup[1])
	   				 , groupby(t[1], lambda line: line[8]))
				)
	, lambda t: ( t[0]
				, filter( lambda line: line[0] != '' and line[4] != 'All'
						, map(list, t[1]))
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
	for p in getRawPositions(inputFile):
		print(p)