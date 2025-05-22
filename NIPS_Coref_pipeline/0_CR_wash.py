import pandas as pd

df = pd.read_parquet("Conll2012_englishv12/test-00000-of-00001.parquet")

for row in df.values:
    dict_list = row[0]
    for d in dict_list:
        if isinstance(d, dict):
            if 'id' in d:
                d['id'] -= 1

            if 'tokens' in d:
                for token_dict in d['tokens']:
                    if isinstance(token_dict, dict) and 'id' in token_dict:
                        token_dict['id'] -= 1

df.to_parquet('processed_conll_test.parquet')