import pyodbc 
conn = pyodbc.connect('Driver={SQL Server};'
                            'Server=127.0.0.1;'
                            'Database=O2JAM;'
                            'uid=sa;pwd=123;')

cursor = conn.cursor()
cursor.execute('SELECT id,userid,usernick FROM dbo.member')

for row in cursor:
    print(row)