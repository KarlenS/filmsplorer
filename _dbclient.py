import pymysql

CLIENT = pymysql.connect(host='localhost',
                         user='root',
                         password='temppass',
                         db='imdb_add',
                         charset='utf8mb4',
                         cursorclass=pymysql.cursors.DictCursor)
