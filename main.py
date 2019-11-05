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



def skip2(it):
	"""
	[Iterable] it => [Iterable] litiitnes

	Skip the first 2 items in iterator "it"
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
	[Iterable] lines => [Iterable] holding lines

	In the BOCHK position file, a position has multiple lines, represent its
	quantity on trade day basis, settlement day basis, and in transit.

	We only the trade day quantity.
"""
consolidate = lambda lines: \
	map( lambda t: pop(t[1])\
	   , groupby(lines, lambda line: line[3]))



"""
	[String] file => [Iterable] positions

	position: [Dictionary] header -> value
"""
getRawPositions = compose(
	  lambda t: map(lambda line: dict(zip(t[0], line)), t[1])\
	, lambda t: ( t[0]\
				, map( lambda keynGroup: pop(keynGroup[1])\
	   				 , groupby(t[1], lambda line: line[8]))\
				)\
	, lambda t: ( t[0]\
				, filter( lambda line: line[0] != '' and line[4] != 'All'\
						, map(list, t[1]))\
				)
	, getHeadersnLines\
	, skip2\
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