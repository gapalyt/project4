import sqlite3

# DB에 연결
conn = sqlite3.connect('login.db')
c = conn.cursor()

# 모든 사용자 정보 조회 쿼리 실행
c.execute('SELECT * FROM userstable')

# 결과 가져오기
rows = c.fetchall()

# 결과 출력
for row in rows:
    print(row)

# DB 연결 종료
conn.close()
