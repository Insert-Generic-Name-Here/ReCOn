import pandas as pd
from os import path
from random import randint,choice

cols = ['timestamp' ,'event' , 'src', 'dest']
sample_time = 1537453981
events = ['modified' , 'moved', 'created', 'deleted']
sample_path = ['/foo/bar'+str(i) for i in range(5)]

for j in range(2):
    new_paths = ['/foo/bar'+str(i) for i in range(5,10)]
    table = []

    for path in sample_path:
        itm = path
        cr_time = 1537453981+randint(1,100)
        mv_time = cr_time+randint(20,40)
        del_time = mv_time+randint(20,40)
        table.append([cr_time, 'created', itm, None])
        for _ in range (randint(1,6)):
            table.append([randint(cr_time+1, mv_time-1),'modified' ,itm , None])
        if randint(1,3) != 2:
            new_path = new_paths.pop()
            table.append([mv_time,'moved' ,itm , new_path])
            for _ in range (randint(1,6)):
                table.append([randint(cr_time+1, mv_time-1),'modified' ,new_path , None])
            itm = new_path
        if randint(1,2) != 2:
            table.append([del_time, 'deleted', itm, None])
            
        

    df = pd.DataFrame(table, columns = cols)
    df.to_csv(f'tst{str(j)}.csv')