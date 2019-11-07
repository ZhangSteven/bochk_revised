# bochk_revised
Convert holding and cash files from BOCHK to Geneva reconciliation purpose

Output csv files have the following columns (similar to nomura package),

For position csv:
portfolio|custodian|date|geneva_investment_id|ISIN|bloomberg_figi|name|currency|quantity


For cash csv:
portfolio|custodian|date|currency|balance


Security Id Lookup.xlsx: sometimes the security id type is not ISIN, so this file contains the mapping from those security ids to ISIN and Bloomberg FIGI (if ISIN is not available)