import psycopg2

# 사용자 입력 받기
input_route_number = input("조회하고 싶은 노선 번호를 입력하세요: ")

try:
    # 데이터베이스 연결 설정
    conn = psycopg2.connect(host='192.168.0.2', dbname='postgres', user='postgres', password='root', port=5432)
    cur = conn.cursor()
    # 사용자 입력을 기반으로 해당 route_number만 선택
    cur.execute("SELECT bus_plate_number, route_number, congestion_level FROM bus_congestion_app.bus_congestion WHERE route_number = %s;", (input_route_number,))
    rows = cur.fetchall()
    for row in rows:
        print(row)
    cur.close()
    conn.close()
except psycopg2.DatabaseError as db_err:
    print(db_err)
