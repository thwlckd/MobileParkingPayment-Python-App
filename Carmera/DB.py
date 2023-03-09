'''
Mobile Parking Control System
DB.py
'''
# mySQL connect
# 데이터베이스의 연결 정보를 저장
import pymysql
def con_and_make_cursor():
    conn = pymysql.connect(host='localhost',
                       user='root', 
                       password='자기 비밀번호',
                       db='parking_service', 
                       charset='utf8')    
    return conn