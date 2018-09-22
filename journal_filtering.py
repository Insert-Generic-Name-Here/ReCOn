import pandas as pd

def filter_journals(server_journal, client_journal):
    df = pd.read_csv(server_journal) # , index_col=[0]
    df1 = pd.read_csv(client_journal)

    fn = pd.concat([df,df1],ignore_index=True)

    exp = fn.loc[fn.groupby('src').timestamp.idxmax()]

    # SAVE IF NEEDED

    ## exp.to_csv('res.csv')
    return exp