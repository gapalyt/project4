import sqlite3

# DB에 연결
conn = sqlite3.connect('login.db')
c = conn.cursor()

# 삭제할 사용자의 이름
username_to_delete = "admin"

# 사용자 삭제 쿼리 실행
c.execute('DELETE FROM userstable WHERE username = ?', (username_to_delete,))

# 변경 사항 저장
conn.commit()

# DB 연결 종료
conn.close()
