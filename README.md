# bochk_revised
Convert holding and cash files from BOCHK to Geneva reconciliation purpose

Output csv files have the following columns (similar to nomura package),

For position csv:
portfolio|custodian|date|geneva_investment_id|ISIN|bloomberg_figi|name|currency|quantity


For cash csv:
portfolio|custodian|date|currency|balance


There are two Excel files,

Security Id Lookup: sometimes the security id type is not ISIN, so this file contains the mapping from those security ids to ISIN and Bloomberg FIGI (if ISIN is not available)

AFS Bond in HTM Portfolios: sometimes HTM portfolios contain available for sales or trading positions, then we need to mark those to output ISIN instead of ISIN + HTM as the identifier.