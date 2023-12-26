import pandas as pd
import sqlite3

# xlsx 파일을 Pandas DataFrame으로 읽기
df = pd.read_excel('sample.xlsx')

# SQLite3 데이터베이스에 연결 ('user.db' 파일로 저장)
conn = sqlite3.connect('user.db')

# DataFrame을 SQLite 테이블로 저장
df.to_sql('your_table', conn, index=False, if_exists='replace')

# 변경사항을 커밋
conn.commit()

# 연결 종료
conn.close()

