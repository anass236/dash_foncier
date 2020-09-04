import pandas as pd


def number_sales_pieces(dictdf, type_local):
    count_mutation = []
    for key, df in dictdf.items():
        val_count = df[df['Nature mutation'] == 'Vente'][df['Type local'] == type_local][
            'Nombre pieces principales'].value_counts()
        count_mutation.append(pd.DataFrame(
            {'year': key, 'Nombre pieces principales vendues': val_count.index, 'Count': val_count.values}))

    return pd.concat(count_mutation)
