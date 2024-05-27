import socketserver
import threading
import time
import pymysql
from datetime import datetime
import pickle
import numpy as np
import cv2
HOST = ('192.168.31.57'
        '')
PORT = 9900
lock = threading.Lock()

sql_conn = pymysql.connect(host='127.0.0.1', user='root', password='0000', db='kakao', charset='utf8')

def refresh_connection():
    # 이전 연결을 닫습니다 (있는 경우).
    global sql_conn
    try:
        sql_conn.close()
    except:
        pass

    sql_conn = pymysql.connect(host='127.0.0.1', user='root', password='0000', db='kakao', charset='utf8')
    return sql_conn
class UserManager:
    def __init__(self):
        self.users = {} #클라이언트 사이드를 통해 접속한 유저 객체를 담는 변수
        self.data_buffers = {}
    def addUser(self, username, conn, addr,rows): #username은
        if username in self.users:
            conn.send('already exist.\n'.encode()) #encode utf-8로 인코딩된 문자열 반환
            return None
        cur = refresh_connection().cursor()
        sql = """SELECT p.*
             FROM personal p
             JOIN friend f ON p.phone = f.friend_phone
             WHERE f.my_phone IN (
                 SELECT phone FROM personal WHERE ID = %s
             )
             ORDER BY p.name ASC"""
        cur.execute(sql, (username,))
        friends_info = cur.fetchall()

        lock.acquire() #쓰레드의 락개체는 공유데이터를 다룰때 스레드를 독립성을 보장
        self.users[username] = (conn, addr)
        self.data_buffers[username] = b''
        lock.release() #독립성 보장해야하는 작업이 끝나면 release로 풀어줌

        header_text = '[login]'
        # 모든 정보를 리스트에 담음
        all_info_container = [header_text, rows, friends_info]

        # 한 번에 직렬화
        all_info_serialized = pickle.dumps(all_info_container)

        # 네트워크를 통해 직렬화된 데이터 전송
        self.users[username][0].send(all_info_serialized)
        # self.sendMessageToAll('[시스템] [%s] 입장' % username)
        return username

    # def user_list(self):
    #     userListMessage = 'userlist: ' + ','.join(self.users.keys())
    #     for conn, _ in self.users.values():
    #         conn.send(userListMessage.encode())
    def removeUser(self, username):
        if username not in self.users:
            return
        lock.acquire()
        del self.users[username]
        if username in self.data_buffers:
            del self.data_buffers[username]
        lock.release()
        self.sendMessageToAll('[시스템] [%s] 퇴장.' % username)
    def messageHandler(self, username, msg):
        if msg.startswith(b"[pri_chat_room]"):#개인톡
            try:
                msg_parts = msg.split(b',')
                room_id = msg_parts[1].decode()
                users_bytes = msg_parts[2:]

                users_list = sorted(user.decode() for user in users_bytes)
                users = ','.join(users_list)
                cur=refresh_connection().cursor()
                sql_check = "SELECT room_id FROM chat_room WHERE users = %s"
                cur.execute(sql_check, (users,))
                existing_room = cur.fetchone()

                if existing_room:
                    print(f"Room with users {users} already exists. Skipping creation.")
                else:
                    sql = """INSERT INTO chat_room (room_id, users) VALUES (%s, %s)"""
                    cur.execute(sql, (room_id, users))
                    sql_conn.commit()

                    print(f"Room {room_id} with users {users} added successfully.")
            except Exception as e:
                print(f"Failed to add room {room_id} with users {users}: {e}")
            finally:
                cur.close()

        elif msg.startswith(b'[friend_add],'):
            info=msg.decode().split(',')
            my_phone= info[1]
            friend_phone=info[2]
            cur = refresh_connection().cursor()

            try:
                sql="SELECT * FROM personal where phone=%s"
                cur.execute(sql,(friend_phone,))
                personal = cur.fetchone()
                if personal:
                    sql_check = "SELECT * FROM friend WHERE my_phone=%s AND friend_phone=%s"
                    cur.execute(sql_check, (my_phone, friend_phone))
                    result = cur.fetchone()
                    if result:
                        print("이미등록된친구")
                    elif my_phone == friend_phone:
                        print("이미등록된 친구")
                    else:
                        sql_insert = "INSERT INTO friend (my_phone, friend_phone) VALUES (%s, %s)"
                        cur.execute(sql_insert, (my_phone, friend_phone))
                        cur.execute(sql_insert, (friend_phone, my_phone))
                        sql_conn.commit()
                        print("등록완료")
                        cur = refresh_connection().cursor()

                        sql = """SELECT p.*
                                     FROM personal p
                                     JOIN friend f ON p.phone = f.friend_phone
                                     WHERE f.my_phone IN (
                                         SELECT phone FROM personal WHERE ID = %s
                                     )
                                     ORDER BY p.name ASC"""
                        cur.execute(sql, (username,))
                        friends_info = cur.fetchall()
                        header_text = '[add_friend]'
                        # 모든 정보를 리스트에 담음
                        all_info_container = [header_text, friends_info]
                        # 한 번에 직렬화
                        all_info_serialized = pickle.dumps(all_info_container)

                        curr = refresh_connection().cursor()
                        sqll="""select ID from personal where phone=%s"""
                        curr.execute(sqll,(friend_phone,))
                        friend_id=curr.fetchone()
                        print(friend_id)
                        currr = refresh_connection().cursor()
                        sqll = """SELECT p.*
                                                             FROM personal p
                                                             JOIN friend f ON p.phone = f.friend_phone
                                                             WHERE f.my_phone IN (
                                                                 SELECT phone FROM personal WHERE ID = %s
                                                             )
                                                             ORDER BY p.name ASC"""
                        currr.execute(sqll, (friend_id,))
                        info = currr.fetchall()
                        info_container = [header_text, info]
                        info_serialized = pickle.dumps(info_container)

                        self.users[username][0].send(all_info_serialized)
                        self.users[friend_id[0]][0].send(info_serialized)
            except Exception as e:
                print(e)
        elif msg.startswith(b'[birthday],'):
            info=msg.split(b',')
            my_phone=info[1]
            cur = refresh_connection().cursor()
            sql = "SELECT friend_phone, personal.birthday, name, profile_picture FROM friend left join personal ON friend.friend_phone=personal.phone where personal.birthday is not null and my_phone = %s;"
            cur.execute(sql, (my_phone,))
            header="[birth]"
            frd_birthdays = cur.fetchall()
            all=[header,my_phone,frd_birthdays]
            all_box=pickle.dumps(all)
            self.users[username][0].send(all_box)

        elif msg.startswith(b'\x80\x04')and b'[change_picture]' in msg:
            info=pickle.loads(msg)
            number=info[1]
            blob_data=info[2]
            try:
                cur = refresh_connection().cursor()
                sql = "UPDATE personal SET profile_picture = %s WHERE phone = %s"
                cur.execute(sql, (blob_data, number))
                sql_conn.commit()
                curr = refresh_connection().cursor()
                sqll = "select * from personal where phone = %s"
                curr.execute(sqll,(number,))
                my_info= curr.fetchone()

                header="[my_info]"
                ab=(header,my_info)
                print(ab)
                aa=pickle.dumps(ab)
                print(aa)
                self.users[username][0].send(aa)
            finally:
                cur.close()

        elif msg.startswith(b'\x80\x04')and b'[group_chat]' in msg:#그룹톡 등록
            try:
                info=pickle.loads(msg)
                room_id = info[1]
                users_bytes = []
                users=info[2]
                for user in users:
                    users_bytes.append(user.strip())
                users_list = sorted(user for user in users_bytes)
                users = ','.join(users_list)
                cur=refresh_connection().cursor()
                sql_check = "SELECT room_id FROM chat_room WHERE room_id = %s"
                cur.execute(sql_check, (room_id,))
                existing_room = cur.fetchone()

                if existing_room:
                    print(f"Room with users {users} already exists. Skipping creation.")
                else:
                    sql = """INSERT INTO chat_room (room_id, users) VALUES (%s, %s)"""
                    cur.execute(sql, (room_id, users))
                    sql_conn.commit()

                    print(f"Room {room_id} with users {users} added successfully.")
            except Exception as e:
                print(f"Failed to add room {room_id} with users {users}: {e}")
            finally:
                pass

        elif msg.startswith(b"[chat]"): #chat="[chat],"+room_id+','+friend_info[3]+','+my_info[3]+','+self.send_entry.get()
            try:
                room_id=msg.split(b',')[1]
                if room_id.startswith(b"P"): # 개인톡일경우
                    msg_parts = msg.split(b',',4)
                    friend=msg.split(b',')[2]
                    users_bytes = msg_parts[2:4]  # 첫 번째와 두 번째 부분이 사용자 정보
                    users_list = sorted(user.decode('utf-8') for user in users_bytes)
                    users = ','.join(users_list)
                    chat_detail = b','.join(msg_parts[4:]) # 채팅 내용
                    # 현재 시간을 '오후 4:30'과 같은 형식으로 변환
                    time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                    cur = refresh_connection().cursor()
                    # 해당 사용자를 포함하는 채팅방 조회
                    sql_check = "SELECT room_id FROM chat_room WHERE users = %s"
                    cur.execute(sql_check, (users,))
                    room = cur.fetchone()
                    if room:
                        cur2 = refresh_connection().cursor()
                        room_id = room[0]
                        # 채팅 로그 삽입
                        sql_insert_log = """INSERT INTO chat_log (room_key, id, time, chat_detail) VALUES (%s, %s, %s, %s)"""
                        cur2.execute(sql_insert_log, (room_id, username,time,chat_detail))
                        sql_conn.commit()
                        curr = refresh_connection().cursor()
                        # 동일한 방키를 가진 모든 채팅 로그 조회
                        sql_get_logs = "SELECT * FROM chat_log WHERE room_key = %s"
                        curr.execute(sql_get_logs, (room_id,))
                        logs = curr.fetchall()
                        # 클라이언트로 보낼 메시지 준비
                        header_textt = '[chat_detail]'
                        # 모든 정보를 리스트에 담음
                        all_info_container = [header_textt, logs]
                        # 한 번에 직렬화
                        all_info_serialized = pickle.dumps(all_info_container)
                        self.users[username][0].send(all_info_serialized)
                        if friend.decode() in self.users and self.users[friend.decode()][1]:
                            self.users[friend.decode()][0].send(all_info_serialized)
                        else:
                            print("친구접속안하는중")
            except Exception as e:
                print(f"Failed to process chat message: {e}")

        elif msg.startswith(b'\x80\x04')and b'[group_send]' in msg:
            try:
                info = pickle.loads(msg)
                room_id=info[1]
                friends = info[2]
                my_id=info[3]
                chat_detail = info[4]
                users = ','.join(friends)
                # 현재 시간을 '오후 4:30'과 같은 형식으로 변환
                time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                cur = refresh_connection().cursor()
                # 해당 사용자를 포함하는 채팅방 조회
                sql_check = "SELECT room_id FROM chat_room WHERE room_id = %s"
                cur.execute(sql_check, (room_id,))
                room = cur.fetchone()
                if room:
                    cur2 = refresh_connection().cursor()
                    room_id = room[0]
                    # 채팅 로그 삽입
                    sql_insert_log = """INSERT INTO chat_log (room_key, id, time, chat_detail) VALUES (%s, %s, %s, %s)"""
                    cur2.execute(sql_insert_log, (room_id, username, time, chat_detail))
                    sql_conn.commit()
                    curr = refresh_connection().cursor()
                    # 동일한 방키를 가진 모든 채팅 로그 조회
                    sql_get_logs = "SELECT * FROM chat_log WHERE room_key = %s"
                    curr.execute(sql_get_logs, (room_id,))
                    logs = curr.fetchall()
                    header_textt = '[group_detail]'
                    # 모든 정보를 리스트에 담음
                    all_info_container = [header_textt, logs]
                    # 한 번에 직렬화
                    all_info_serialized = pickle.dumps(all_info_container)
                    self.users[username][0].send(all_info_serialized)
                    emails = friends[0].split(", ")
                    for friend in emails:
                        print(friend)
                        if friend in self.users:
                            self.users[friend][0].send(all_info_serialized)
                        else:
                            print("친구접속안하는중")
            except Exception as e:
                print(f"Failed to process group message: {e}")

        elif msg.startswith(b"[start_video]"):
            if msg.endswith(b'[end_video]'):
                parts = msg.split(b',', 2)
                friend_name = parts[1]
                frame_data = parts[2].rsplit(b',', 1)[0]
                self.users[friend_name.decode()][0].send(b'[end_call],' + frame_data)

        elif msg.startswith(b"[call]"):
            head_text=b'[send]'
            friend_id = msg.split(b',')[1]
            my_name= msg.split(b',')[2]
            my_id=msg.split(b',')[3]
            send = [head_text,my_name,my_id,friend_id]
            all_info_serialized = pickle.dumps(send)
            if friend_id.decode() in self.users and self.users[friend_id.decode()][1]:
                self.users[friend_id.decode()][0].send(all_info_serialized)
                print("친구접속중")
            else:
                print("친구접속안하는중")

        elif msg.startswith(b"[answer]"):
            friend_id = msg.split(b',')[1].decode()
            id2=msg.split(b',')[2].decode()
            aa=b'[startcall]'
            self.users[friend_id][0].send(aa) #전화건사람한테 옴 여기다 상대방의 데이터를 줌
            self.users[id2][0].send(aa)
            #여기엔 전화받은사람에게 내데이터를 보내줘야함

        elif msg.startswith(b"[chat_fill]"):
            room_id=msg.split(b',')[1]
            cur4 = refresh_connection().cursor()
            # 동일한 방키를 가진 모든 채팅 로그 조회
            sql_get_logs = "SELECT * FROM chat_log WHERE room_key = %s"
            cur4.execute(sql_get_logs, (room_id,))
            logs = cur4.fetchall()
            header_textt = '[first_chat_list]'
            # 모든 정보를 리스트에 담음
            all_info_container = [header_textt, logs]
            # 한 번에 직렬화
            all_info_serialized = pickle.dumps(all_info_container)
            self.users[username][0].send(all_info_serialized)

        elif msg.startswith(b"[group_chat_fill]"):
            room_id=msg.split(b',')[1]
            cur4 = refresh_connection().cursor()
            # 동일한 방키를 가진 모든 채팅 로그 조회
            sql_get_logs = "SELECT * FROM chat_log WHERE room_key = %s"
            cur4.execute(sql_get_logs, (room_id,))
            logs = cur4.fetchall()
            header_textt = '[first_group_list]'
            # 모든 정보를 리스트에 담음
            all_info_container = [header_textt, logs]
            # 한 번에 직렬화
            all_info_serialized = pickle.dumps(all_info_container)
            self.users[username][0].send(all_info_serialized)

        elif msg.startswith(b"[room_list]"):
            #룸키 가져오기
            cur = refresh_connection().cursor()
            sql = """
                SELECT room_id, users
                FROM chat_room
                WHERE users LIKE %s OR
                      users LIKE %s OR
                      users LIKE %s OR
                      users LIKE %s
            """
            like_param1 = f'%{username}'  # ID가 문자열의 시작에 있을 경우
            like_param2 = f'%{username},%'  # ID가 문자열의 중간에 있을 경우
            like_param3 = f'{username},%'  # ID가 문자열의 중간에 있을 경우
            like_param4 = f'%,{username}'  # ID가 문자열의 끝에 있을 경우

            # SQL 쿼리 실행
            cur.execute(sql, (like_param1, like_param2, like_param3, like_param4))

            # 결과 가져오기
            rooms = cur.fetchall()
            header_textt = '[chat_log]'

            all_info=[]
            all_list=[]
            for room in rooms:
                result_list = []
                curr = refresh_connection().cursor()
                room_id = room[0]
                if room_id[0]=="P":
                    # 2. 각 방에서 가장 최근의 메시지 정보와 사용자 정보 조회
                    sql = """
                            SELECT p.name AS sender_name, r.profile_picture AS receiver_picture, 
                           r.ID AS receiver_id,r.name AS receiver_name, cl.room_key,cl.time, cl.chat_detail
                            FROM chat_log cl
                            JOIN personal p ON p.id = cl.id
                            JOIN chat_room cr ON cr.room_id = cl.room_key
                            JOIN personal r ON r.ID = (
                                SELECT CASE
                                    WHEN SUBSTRING_INDEX(SUBSTRING_INDEX(cr.users, ',', 1), ',', -1) = %s 
                                     THEN SUBSTRING_INDEX(SUBSTRING_INDEX(cr.users, ',', 2), ',', -1)
                                    ELSE SUBSTRING_INDEX(SUBSTRING_INDEX(cr.users, ',', 1), ',', -1)
                                END
                                FROM chat_room
                                WHERE room_key = cl.room_key
                                LIMIT 1
                            )
                            WHERE cl.room_key = %s AND TRIM(cl.chat_detail) != '' AND LENGTH(TRIM(cl.chat_detail)) > 0
                            ORDER BY cl.time DESC
                            LIMIT 1
                            """
                    curr.execute(sql, (username, room_id,))


                    message = curr.fetchone()

                    if not message == None:
                        result_list.append(message)
                    all_list.append(result_list)

                elif room_id[0]=="G":
                    cur = refresh_connection().cursor()
                    # 사용자 정보와 채팅 정보를 가져오는 SQL 쿼리
                    sql = """
                            SELECT room_id, users
                            FROM chat_room
                            WHERE room_id = %s
                        """
                    cur.execute(sql, (room_id,))
                    rooms = cur.fetchall()
                    user_list = rooms[0][1].split(',')
                    filtered_users = [user.strip() for user in user_list if user.strip() != username]
                    all_info = []
                    # 친구의 이름, 사진, ID 가져오기
                    if filtered_users:
                        cur = refresh_connection().cursor()
                        placeholders = ', '.join(['%s'] * len(filtered_users))
                        sql = f"""
                               SELECT name, profile_picture, ID
                               FROM personal
                               WHERE ID IN ({placeholders})
                           """
                        cur.execute(sql, filtered_users)
                        friends_info = cur.fetchall()
                        friend_names = [info[0] for info in friends_info]
                        profile_pictures = [info[1] for info in friends_info]
                        friend_ids = [info[2] for info in friends_info]

                        curr = refresh_connection().cursor()
                        sql = """
                               SELECT time, chat_detail
                               FROM chat_log
                               WHERE room_key = %s
                               ORDER BY time DESC
                               LIMIT 1
                           """
                        curr.execute(sql, (room_id,))
                        last_chat = curr.fetchone()
                        if last_chat is not None:  # 채팅 정보가 존재하면 추가
                            last_chat_time, last_chat_detail = last_chat
                            all_info.extend(
                                [username, profile_pictures, friend_ids, friend_names, room_id, last_chat_time,
                                 last_chat_detail])
                            all_list.append([tuple(all_info)])
                        else:  # 채팅 정보가 없으면 채팅 정보 없이 추가
                            pass

            all_info_container=[header_textt,all_list]

            all_info_serialized=pickle.dumps(all_info_container)
            self.users[username][0].send(all_info_serialized)
        else:
            pass
            # self.sendMessageToAll('[%s] %s' % (username, msg))

    def sendMessageToAll(self, msg): #전체에게 메시지
        for conn, addr in self.users.values():
            conn.send(msg.encode())
class MyTcpHandler(socketserver.BaseRequestHandler): #모든 요청 핸들러 객체의 클래스 상속받음 괄호안거의 내용을 MyTcpHandler가 상속받음
    userman = UserManager() #생성자불러서 userman에 넣기
    def handle(self):
        try:
            username = self.registerUsername()
            while True:
                msg = self.request.recv(200000)
                if self.userman.messageHandler(username, msg) == -1:
                    self.request.close()
                    break
        except Exception as e:
            print(e)
        self.userman.removeUser(username)
        print('[%s] 종료' % self.client_address[0])
    def registerUsername(self):
        try:
            username = self.request.recv(1024)  # 클라이언트로부터 데이터 수신
            print(username)
            if username.startswith(b'\x80\x04') and b'[register]' in username:
                print("들어옴")
                info = pickle.loads(username)
                curr = refresh_connection().cursor()
                sqll = "INSERT INTO personal (name, phone, profile_picture, ID, password, back_picture, profile_time, birthday) VALUES (%s, %s, '-', %s, %s, '-', NULL, %s);"
                curr.execute(sqll, (info[1], info[2], info[3], info[4], info[5]))
                sql_conn.commit()

            else:
                print("dsafasdf")
                username = username.decode().strip()  # 받은 데이터 디코딩
                ID = username.split(',')[1]  # ID 추출
                pw = username.split(',')[2]  # 패스워드 추출
                cur = refresh_connection().cursor()
                sql="SELECT * FROM personal"
                cur.execute(sql)
                rows = cur.fetchall()
                for row in rows:
                    if ID == row[3] and pw == row[4]:
                        if self.userman.addUser(ID, self.request, self.client_address, row):
                            return ID
        except Exception as e:
            print(f"Error during username registration: {e}")
        finally:
            pass
class ChatingServer(socketserver.ThreadingMixIn, socketserver.TCPServer):#쓰레딩믹스인->쓰레드 자동배분
    pass #채팅서버는 괄호안 두가지 클래스 상속받은 클래스
def runServer():
    try:
        server = ChatingServer((HOST, PORT), MyTcpHandler) #server는 채팅서버의 인스턴스
        server.serve_forever()#어떠한 요청이있을때까지 요청처리 채팅서버 괄호안 두개의 클래스중 뒤에것의 메서드
        #두번째인자가 클라이언트 연결마다 호출될 요청 핸들러 클래스임 인자들은 소켓서버 티시피서버의 인자
    except KeyboardInterrupt:
        print('서버종료')
        server.shutdown()
        server.server_close()
runServer()