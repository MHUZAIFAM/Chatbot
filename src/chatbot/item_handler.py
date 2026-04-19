def extract_item_id(df, id_col, question):

    q = question.lower()

    for item in df[id_col].astype(str):
        if item.lower() in q:
            return item

    return None


def get_item_row(df, id_col, item_id):

    row = df[df[id_col].astype(str) == str(item_id)]

    if row.empty:
        return None

    return row.iloc[0]