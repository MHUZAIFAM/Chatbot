import pandas as pd

def load_dataset(csv_path):
    df = pd.read_csv(csv_path)
    df = df.drop_duplicates().reset_index(drop=True)
    return df


def detect_column(df, possible_names):
    for col in df.columns:
        for name in possible_names:
            if name.lower() in col.lower():
                return col
    return None