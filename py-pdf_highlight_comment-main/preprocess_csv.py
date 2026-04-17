import pandas as pd
from config import config

def remove_col():
    df = pd.read_csv(config['keywords_list'])
    df = df.drop('color', axis=1)
    print(df.head(10))

    df.to_csv('input_folder/processed.csv', index=False)