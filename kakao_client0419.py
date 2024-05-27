import tkinter as tk #파이썬 내장 GUI 개발 라이브러리
from PIL import Image, ImageTk, ImageDraw, ImageOps
import tkinter.messagebox as msgbox
import io
from tkinter import filedialog
import platform
from tkinter import ttk
import socket #통신소켓 TCP/UDP서버 만듦
import threading
from threading import Thread #동시처리를 위해서 thread사용
import pickle
import time
import tkinter #파이썬 내장 GUI 개발 라이브러리
from tkinter import font
import cv2
import PIL.ImageTk
import numpy as np
import queue
from datetime import datetime
import datetime
HOST = '192.168.31.57'
PORT = 9900
global sock
face_cascade=cv2.CascadeClassifier('haarcascade_frontalface_alt.xml')

current_toCall_instance = None
mycam_queue = queue.Queue()
global abc
friend_queue=queue.Queue()

first_chat=None

group_chat=None

vid_friend_id=""

chat_windows={}
friend_profile_windows={}
interface_states={"start_call":False, "fromCall": False, "toCall":False}



main_windows=None

group_talk_windows=False

birth_windows=False

my_profile_windows=False

plus_windows=False
def open_start_call():
    global current_toCall_instance
    if current_toCall_instance:
        current_toCall_instance.toCall_end()  # 창을 닫는 메서드 호출
        current_toCall_instance = None
    aa = tk.Toplevel()
    f = start_call(aa)
    f.run()
def rcvMsg(sock):
    global main_windows
    while True:
        try:
            data = sock.recv(200000) #소켓에서 데이터 수신 한번에 수신할 최대 데이터양(bufsize) 지정
            #지정한 값으로 자른 데이터 받음
            if not data: #데이터 없으면
                break#나감
            if data.startswith(b'\x80\x04')and b'[login]' in data:
                try:
                    info = pickle.loads(data)
                    user_info = info[1]
                    friend_info = info[2]
                    app.open_main_window(user_info,friend_info)
                except Exception as e:
                    print("피클 데이터 처리 중 오류 발생:", e)

            elif data.startswith(b'\x80\x04')and b'[add_friend]' in data:
                print("들어오긴해")
                info=pickle.loads(data)
                a=info[1]

                root.after(0, main_windows.update_friend_list, a)
                root.after(0, main_windows.friend_list_update)
            elif data.startswith(b'\x80\x04') and b'[my_info]' in data:
                info=pickle.loads(data)
                print("들어옴!")
                my_info=info[1]
                root.after(0, main_windows.update_my_info, my_info)
            elif data.startswith(b'\x80\x04')and b'[send]' in data:
                info2 = pickle.loads(data)
                my_name=info2[1]
                my_id=info2[2]
                friend_id=info2[3]
                for state in interface_states.values():
                    if state:
                        return
                call = tk.Toplevel()
                f = fromCall(call,my_name,my_id,friend_id)
                f.run()

            elif data.startswith(b'[startcall]'):
                global current_toCall_instance
                if current_toCall_instance:
                    root.after(0, open_start_call)
                else:
                    aa = tk.Toplevel()
                    f = start_call(aa)
                    f.run()

            elif data.startswith(b'[end_call],'):
                frame=data[11:]
                friend_queue.put(frame)

            elif data.startswith(b'\x80\x04')and b'[first_chat_list]' in data:
                global first_chat
                info = pickle.loads(data)
                room_id = info[1][0][0]
                detail=info[1]
                first_chat=detail
                if room_id in chat_windows:  # 챗윈도우 키는 룸아이디
                    chat_instance = chat_windows[room_id]
                    root.after(0, chat_instance.fill_chat, detail)

            elif data.startswith(b'\x80\x04')and b'[first_group_list]' in data:
                global group_chat
                info = pickle.loads(data)
                room_id = info[1][0][0]
                detail=info[1]
                group_chat=detail
                if room_id in chat_windows:  # 챗윈도우 키는 룸아이디
                    chat_instance = chat_windows[room_id]
                    root.after(0, chat_instance.fill_group_chat, detail)

            elif data.startswith(b'\x80\x04')and b'[chat_detail]' in data:
                # 인덱스/ 1 룸키 /2 보낸사람아이디 /3 내용 /4시간
                info = pickle.loads(data)
                room_id=info[1][0][0]
                detail=info[1]
                if room_id in chat_windows: #챗윈도우 키는 룸아이디
                    chat_instance=chat_windows[room_id]
                    root.after(0, chat_instance.fill_chat, detail)
                # else: #창안켜져있으면
                #     pass
            elif data.startswith(b'\x80\x04') and b'[chat_log]' in data:
                info = pickle.loads(data)
                root.after(0, main_windows.chat_list_update, info)

            elif data.startswith(b'\x80\x04') and b'[group_detail]' in data:
                info = pickle.loads(data)
                room_id = info[1][0][0]
                detail = info[1]
                if room_id in chat_windows:  # 챗윈도우 키는 룸아이디
                    chat_instance = chat_windows[room_id]
                    root.after(0, chat_instance.fill_group_chat, detail)

            elif data.startswith(b'\x80\x04')and b'[birth]' in data:

                info=pickle.loads(data)
                my_phone=info[1]
                birth_info=info[2]
                # bb = tk.Toplevel()
                # my_profile_windowa = showBirthday(bb, my_phone,birth_info)
                root.after(0, main_windows.create_birth_window,my_phone,birth_info)
            else:
                pass

        except Exception as e:
            print("Exception: ", e)
            pass

def runChat():
    global sock
    sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # 소켓만들기 AF_INET=주소패밀리 SOCK_STREAM=유형 두개다 상수
    sock.connect((HOST, PORT))  # 주소패밀리 양식 따르기 호스트와 포트

    t = Thread(target=rcvMsg, args=(sock,))  # 쓰레드 생성 쓰레드로 rcvMsg함수를 구동 매개변수는 소켓객체지정
    # 메시지 들어왔는지 체크
    t.daemon = True  # 데몬스레드로 설정해서 메인스레드가 종료되면 자동으로 함께 종료, 프로세스 묶이는 문제 방지
    t.start()

class login:
    def __init__(self,window):
        self.window = window
        self.window.configure(bg='#FEE500')
        self.window.resizable(0, 0)
        self.window.geometry("360x590+810+200")
        self.window.overrideredirect(True)
        self.window.bind("<Button-1>", self.start_move)  # 마우스 버튼 누름
        self.window.bind("<ButtonRelease-1>", self.stop_move)  # 마우스 버튼 뗌
        self.window.bind("<B1-Motion>", self.on_move)
        self.x = None
        self.y = None

        self.close_image = ImageTk.PhotoImage(file="login_close.png")
        self.close = tk.Label(self.window, image=self.close_image, borderwidth=0)
        self.close.place(x=341,y=9)
        self.close.bind("<Button-1>",self.login_close)

        self.mini_image = ImageTk.PhotoImage(file="login_mini.png")
        self.mini = tk.Label(self.window, image=self.mini_image, borderwidth=0)
        self.mini.place(x=318,y=9)

        self.photo = ImageTk.PhotoImage(file="logo.png")
        self.logo = tk.Label(self.window, image=self.photo,borderwidth=0)
        self.logo.place(x=130,y=76)

        self.main_frame=tk.Frame(self.window,width=242,height=76,bg="#E4CE00")
        self.main_frame.place(x=59,y=197)

        self.id_frame=tk.Frame(self.main_frame,width=240,height=37,borderwidth=0,bg="white")
        self.id_frame.place(x=1,y=1)
        self.id=tk.Entry(self.id_frame,relief="flat",width=200,fg="#C8C8C8")
        self.id_default_text = "카카오계정 (이메일 또는 전화번호)"
        self.id.insert(0,self.id_default_text)
        self.id.bind("<FocusIn>", self.clear_id)
        self.id.bind("<FocusOut>", self.reset_id)
        self.id.place(x=8,y=11)

        self.main_line = tk.Frame(self.main_frame, borderwidth=0, bg="#F2F2F2",width=240,height=1)
        self.main_line.place(x=1, y=38)

        self.pw_frame = tk.Frame(self.main_frame, width=240, height=36, borderwidth=0,bg="white")
        self.pw_frame.place(x=1, y=39)
        self.pw = tk.Entry(self.pw_frame, relief="flat",fg="#C8C8C8")
        self.pw_default_text = "비밀번호"
        self.pw.insert(0, self.pw_default_text)
        self.pw.bind("<FocusIn>", self.clear_pw)
        self.pw.bind("<FocusOut>", self.reset_pw)
        self.pw.bind("<Return>",self.onEnter)
        self.pw.place(x=8, y=10)

        self.id_has_input = False
        self.pw_has_input = False

        self.login_button_frame = tk.Frame(self.window,width=242,height=40,bg="#E4CE00", borderwidth=0)
        self.login_button_frame.place(x=59,y=277)

        self.Button_frame = tk.Frame(self.login_button_frame, width=240, height=38, borderwidth=0,bg="#F6F6F6")
        self.Button_frame.pack_propagate(False)
        self.Button_frame.place(x=1, y=1)

        self.login_button = tk.Label(self.Button_frame, text="로그인", bg="#F6F6F6",relief="flat",fg="#C8C8C8")
        self.login_button.bind("<Button-1>",self.login_check)
        self.login_button.pack(expand=True, fill='both')  # 버튼을 프레임 내에 가득 채움

        self.main_line2_image = ImageTk.PhotoImage(file="login_line2.png")
        self.main_line2 = tk.Label(self.window,image=self.main_line2_image,borderwidth=0)
        self.main_line2.place(x=59,y=331)

        self.register_frame = tk.Frame(self.window, width=242, height=40, bg="#E4CE00", borderwidth=0)
        self.register_frame.place(x=59, y=357)

        self.reg_Button_frame = tk.Frame(self.register_frame, width=240, height=38, borderwidth=0, bg="#F6F6F6")
        self.reg_Button_frame.pack_propagate(False)
        self.reg_Button_frame.place(x=1, y=1)

        self.reg_button = tk.Label(self.reg_Button_frame, text="회원가입", bg="#F6F6F6", relief="flat")
        self.reg_button.bind("<Button-1>",self.open_register_window)
        self.reg_button.pack(expand=True, fill='both')


    def login_check(self,event):
        message='[login]'+','+self.id.get()+','+self.pw.get()
        sock.send(message.encode())

    def open_main_window(self,info,f_info):
        try:
            self.window.withdraw()
            def create_new_window():
                global main_windows
                aa = tk.Toplevel()
                second_window = main_window(aa, user_info=info, friend_info=f_info)
                main_windows = second_window
                second_window.run()
            self.window.after(0, create_new_window)
        except Exception as e:
            print("Exception occurred:", e)
    def open_register_window(self,event):
        register = tk.Tk()
        bb = register_window(register)
        bb.run()
    def onEnter(self,event):
        self.login_check(event)
    def login_close(self, event):
        self.window.destroy()

    def start_move(self, event):
        if event.widget == self.id or event.widget == self.pw:
            return
        self.x = event.x
        self.y = event.y

    def stop_move(self, event):
        self.x = None
        self.y = None

    def on_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.window.winfo_x() + deltax
        y = self.window.winfo_y() + deltay
        self.window.geometry(f"+{x}+{y}")
    def clear_id(self, event=None):
        if not self.id_has_input:
            self.id.delete(0, tk.END)
            self.id.config(fg="black")
            self.id_has_input = True

    def reset_id(self, event=None):
        if not self.id.get():
            self.id.insert(0, self.id_default_text)
            self.id.config(fg="#C8C8C8")
            self.id_has_input = False

    def clear_pw(self, event=None):
        if not self.pw_has_input:
            self.pw.delete(0, tk.END)
            self.pw.config(show="*", fg="black")
            self.pw_has_input = True

    def reset_pw(self, event=None):
        if not self.pw.get():
            self.pw.insert(0, self.pw_default_text)
            self.pw.config(show="", fg="#C8C8C8")
            self.pw_has_input = False

class main_window:
    def __init__(self,main_window,user_info,friend_info):
        self.user_info = user_info
        print(self.user_info)
        self.my_name=user_info[0]
        self.user_number = user_info[1]
        self.my_id=user_info[3]
        self.friend_info=friend_info
        self.main_window = main_window
        self.main_window.geometry("392x642+810+200")
        self.main_window.overrideredirect(True)
        self.room_id=""
        self.is_clicked = False


        ######################                   왼쪽메뉴               ############################
        self.left_menu = tk.Frame(self.main_window, background="#ececed", width=65, borderwidth=0)
        self.left_menu.pack(side='left', fill='y', expand=False)
        self.left_menu.pack_propagate(False)  # 지정된 폭 유지

        self.main_friend_image = tk.PhotoImage(file="main_friend.png")
        self.main_friend=tk.Label(self.left_menu, image=self.main_friend_image,borderwidth=0)
        self.main_friend.bind("<Button-1>", self.click_main)
        self.main_friend.place(x=22,y=47)

        self.main_talk_image = tk.PhotoImage(file="main_talk.png")
        self.main_talk = tk.Label(self.left_menu, image=self.main_talk_image,borderwidth=0)
        self.talk_bind()
        self.main_talk.bind("<Button-1>",self.click_talk)
        self.main_talk.place(x=22, y=108)

        ######################                   위쪽메뉴               ############################
        self.top_menu = tk.Frame(self.main_window, background="white", height=78,borderwidth=0)
        self.top_menu.pack(side='top', fill='x')
        self.top_menu.bind("<Button-1>", self.start_move)  # 마우스 버튼 누름
        self.top_menu.bind("<ButtonRelease-1>", self.stop_move)  # 마우스 버튼 뗌
        self.top_menu.bind("<B1-Motion>", self.on_move)  # 마우스 드래그

        # 창 이동 상태
        self.x = None
        self.y = None

        self.main_text_image=tk.PhotoImage(file="main_text.png")
        self.main_text=tk.Label(self.top_menu, image=self.main_text_image,background="white",borderwidth=0)
        self.main_text.place(x=21,y=49)

        self.main_convex_image = tk.PhotoImage(file="main_convex.png")
        self.main_convex = tk.Label(self.top_menu, image=self.main_convex_image, bg="white",borderwidth=0)
        self.main_convex.place(x=244,y=48)

        self.main_plus_image = tk.PhotoImage(file="main_plus.png")
        self.main_plus = tk.Label(self.top_menu, image=self.main_plus_image, bg="white",borderwidth=0)
        self.main_plus.bind("<Button-1>",self.plus_window)
        self.main_plus.place(x=281,y=48)

        self.close_image = tk.PhotoImage(file="close_button.png")
        self.close=tk.Label(self.top_menu, image=self.close_image, bg="white",borderwidth=0)
        self.close.place(x=306,y=10)
        self.close.bind("<Button-1>",self.close_window)

        self.mini_image = tk.PhotoImage(file="mini_button.png")
        self.mini = tk.Label(self.top_menu, image=self.mini_image, bg="white", borderwidth=0)
        self.mini.place(x=260, y=10)
        self.mini.bind("<Button-1>", self.minimize_window)

        self.big_image = tk.PhotoImage(file="big_button.png")
        self.big = tk.Label(self.top_menu, image=self.big_image, bg="white", borderwidth=0)
        self.big.place(x=284, y=10)
        self.big.bind("<Button-1>", self.toggle_maximize)

        self.chat_text_image = tk.PhotoImage(file="chat_text.png")

        #친구목록창
        self.scroll_frame = tk.Frame(self.main_window,borderwidth=0)
        self.scroll_frame.pack(side='left', fill='both', expand=True)


        # 전체 캔버스
        self.scroll_area = tk.Canvas(self.scroll_frame, borderwidth=0, bg="white",highlightthickness=0)

        #스크롤바
        self.scrollbar = tk.Scrollbar(self.scroll_frame, command=self.scroll_area.yview, borderwidth=0)
        self.scroll_area.configure(yscrollcommand=self.scrollbar.set, scrollregion=self.scroll_area.bbox("all"))

        self.scrollbar.pack(side="right", fill="y")

        self.scroll_area.pack(side="left", fill="both", expand=True)

        # 채팅목록창

        self.inner_frame= tk.Frame(self.scroll_area) #, borderwidth=2, relief="solid"

        self.scroll_area_window=self.scroll_area.create_window(0,0, window=self.inner_frame, anchor="nw")

        self.inner_frame.bind("<Configure>",self.onFrameConfigure)
        self.scroll_area.bind("<Configure>",self.onCanvasConfigure)
        self.inner_frame.bind('<Enter>', self.onEnter)  # bind wheel events when the cursor enters the control
        self.inner_frame.bind('<Leave>', self.onLeave)


        self.create_main_chat_window()
        self.friend_list_update()
        self.is_maximized = False

    def update_friend_list(self,info):
        self.friend_info=info
    def update_my_info(self,info):
        self.user_info=info
    def minimize_window(self, event):
        self.main_window.iconify()

    def toggle_maximize(self, event):
        if not self.is_maximized:
            # self.main_window.wm_attributes('-zoomed', True)  # Linux와 일부 시스템에서 동작
            self.main_window.state('zoomed')  # Windows에서 동작
            self.is_maximized = True
        else:
            # self.main_window.wm_attributes('-zoomed', False)  # Linux와 일부 시스템에서 동작
            self.main_window.state('normal')  # Windows에서 창을 일반 크기로 돌립니다.
            self.is_maximized = False
    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def stop_move(self, event):
        self.x = None
        self.y = None

    def on_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.main_window.winfo_x() + deltax
        y = self.main_window.winfo_y() + deltay
        self.main_window.geometry(f"+{x}+{y}")
    def close_window(self,event):
        self.main_window.destroy()
    def onFrameConfigure(self, event):
        '''Reset the scroll region to encompass the inner frame'''
        self.scroll_area.configure(scrollregion=self.scroll_area.bbox(
            "all"))
    def onCanvasConfigure(self, event):
        '''Reset the canvas window to encompass inner frame when required'''
        canvas_width = event.width
        self.scroll_area.itemconfig(self.scroll_area_window,
                               width=canvas_width)
    def onMouseWheel(self, event):  # cross platform scroll wheel event
        if platform.system() == 'Windows':
            self.scroll_area.yview_scroll(int(-1 * (event.delta / 120)), "units")
        elif platform.system() == 'Darwin':
            self.scroll_area.yview_scroll(int(-1 * event.delta), "units")
        else:
            if event.num == 4:
                self.scroll_area.yview_scroll(-1, "units")
            elif event.num == 5:
                self.scroll_area.yview_scroll(1, "units")

    def onEnter(self, event):  # bind wheel events when the cursor enters the control
        if platform.system() == 'Linux':
            self.scroll_area.bind_all("<Button-4>", self.onMouseWheel)
            self.scroll_area.bind_all("<Button-5>", self.onMouseWheel)
        else:
            self.scroll_area.bind_all("<MouseWheel>", self.onMouseWheel)

    def onLeave(self, event):  # unbind wheel events when the cursorl leaves the control
        if platform.system() == 'Linux':
            self.scroll_area.unbind_all("<Button-4>")
            self.scroll_area.unbind_all("<Button-5>")
        else:
            self.scroll_area.unbind_all("<MouseWheel>")
    def open_birth_window(self,event):
        header="[birthday],".encode()
        phone=self.user_info[1].encode()
        sock.send(header+phone)

    def create_birth_window(self,my_phone,birth_info):
        global birth_windows
        if not birth_windows:
            birth_windows = True
            bb = tk.Toplevel()
            my_profile_windowa = showBirthday(bb, my_phone, birth_info)
            my_profile_windowa.run()

    def open_friend_profile_window(self, event, user_info):  # 메인 윈도우에 넣기
        user_info = user_info
        user_name = user_info[0]
        user_picture = user_info[2]
        if user_name in friend_profile_windows:
            friend_profile_windows[user_name].main_window_friend_profile.lift()
            return
        bb = tk.Toplevel()
        friend_profile_windowa = friend_profile_window(bb, user_name, user_picture)
        if user_name not in friend_profile_windows:
            friend_profile_windows[user_name] = friend_profile_windowa
        friend_profile_windowa.run()
    def create_main_chat_window(self):
        # 프사와 내이름 들어간 박스
        self.my_info = tk.Frame(self.inner_frame, width=311, height=84, background="white", borderwidth=0)
        self.my_info.bind("<Button-1>", self.my_info_click)
        self.my_info.bind("<Enter>", self.my_info_focus)
        self.my_info.bind("<Leave>", self.my_info_focus_out)
        self.my_info.pack(side="top")

        # 프로필사진관련
        self.profile_picture = tk.PhotoImage(file="common_image.png")
        self.chat_profile=tk.PhotoImage(file="chat_profile.png")
        self.profile_picture_box = tk.Label(self.my_info, bg="white", borderwidth=0, width=54, height=54)
        self.profile_picture_box.place(x=19, y=13)
        self.set_profile_picture(self.user_info[2])
        self.profile_picture_box.bind("<Button-1>", self.open_my_profile_window)

        # 내이름
        self.profile_name = tk.Label(self.my_info, text=self.user_info[0], bg="white", borderwidth=0)
        self.profile_name.place(x=85, y=34)

        self.line_image = tk.PhotoImage(file="line.png")
        self.line_1 = tk.Label(self.inner_frame, image=self.line_image, bg="white", borderwidth=0)
        self.line_1.pack(side="top")

        # 업데이트한 프로필
        self.update_profile_list = tk.Frame(self.inner_frame, background="white", width=311, height=117, borderwidth=0)
        self.update_profile_list.pack(side="top")

        self.update_profile_list_head_line = tk.PhotoImage(file="update_profile.png")
        self.update_profile_list_head_line_box = tk.Label(self.update_profile_list,
                                                          image=self.update_profile_list_head_line, bg="white",
                                                          borderwidth=0)
        self.update_profile_list_head_line_box.place(x=16, y=13)
        self.update_profile_list_count = tk.Label(self.update_profile_list, text="1", bg="white", padx=0, pady=0,
                                                  borderwidth=0, highlightthickness=0, fg='gray')
        self.update_profile_list_count.place(x=119, y=13)

        self.line_2 = tk.Label(self.inner_frame, image=self.line_image, bg="white", borderwidth=0)
        self.line_2.pack(side="top")

        # 생일인 친구
        self.birth_frame = tk.Frame(self.inner_frame, background="white", width=311, height=94, borderwidth=0)
        self.birth_frame.pack(side="top")
        self.birth_frame.bind("<Double-Button-1>",self.open_birth_window)

        self.birth_head_image = tk.PhotoImage(file="birth.png")
        self.birth_head = tk.Label(self.birth_frame, image=self.birth_head_image, bg="white")
        self.birth_head.place(x=17, y=13)

        self.birth_icon_image = tk.PhotoImage(file="birth_icon.png")
        self.birth_icon = tk.Label(self.birth_frame, image=self.birth_icon_image, bg="white", borderwidth=0)
        self.birth_icon.place(x=20, y=39)

        self.birth_text_image = tk.PhotoImage(file="birth_text.png")
        self.birth_text = tk.Label(self.birth_frame, image=self.birth_text_image, bg="white", borderwidth=0)
        self.birth_text.place(x=72, y=54)
        self.birth_count = tk.Label(self.birth_frame, text="1", bg="white", padx=0, pady=0,
                                    borderwidth=0, highlightthickness=0, fg='gray')
        self.birth_count.place(x=237, y=52)

        self.line_3 = tk.Label(self.inner_frame, image=self.line_image, bg="white", borderwidth=0)
        self.line_3.pack(side="top")

        # 친구창
        self.friend_frame = tk.Frame(self.inner_frame, background="white", width=311, height=46, borderwidth=0)
        self.friend_frame.pack(side="top")
        self.friend_text_image = tk.PhotoImage(file="friend_text.png")
        self.friend_text = tk.Label(self.friend_frame, image=self.friend_text_image, bg="white", borderwidth=0)
        self.friend_text.place(x=20, y=13)

        self.friend_count = tk.Label(self.friend_frame, text="1", bg="white", padx=0, pady=0,
                                     borderwidth=0, highlightthickness=0, fg='gray')
        self.friend_count.place(x=49, y=11)
        self.friend_frame.pack(side="top")
        # 친구추가
        self.friend_list_frame = tk.Frame(self.inner_frame, background="white", width=311, height=46, borderwidth=0)
        self.friend_list_frame.pack(side="top")
        self.friend_list_update()
        self.chat_log=None
        self.is_maximized = False
        self.group_window_open = False


    def run(self):
        self.main_window.configure(bg="white")
        self.main_window.minsize(392,502)
        self.main_window.mainloop()

    def talk_bind(self):
        self.main_talk.bind("<Enter>", self.focus_talk)
        self.main_talk.bind("<Leave>", self.focus_out_talk)
    def talk_unbind(self):
        self.main_talk.unbind("<Enter>")
        self.main_talk.unbind("<Leave>")

    def main_bind(self):
        self.main_friend.bind("<Enter>", self.focus_main)
        self.main_friend.bind("<Leave>", self.focus_out_main)

    def main_unbind(self):
        self.main_friend.unbind("<Enter>")
        self.main_friend.unbind("<Leave>")
    def focus_talk(self,event):
        main_talk_focus_image=tk.PhotoImage(file="main_talk_focus.png")
        self.main_talk.config(image=main_talk_focus_image,borderwidth=0)
        self.main_talk.image = main_talk_focus_image
    def focus_out_talk(self,event):
        main_talk_image=tk.PhotoImage(file="main_talk.png")
        self.main_talk.config(image=main_talk_image,borderwidth=0)
        self.main_talk.image = main_talk_image

    def focus_main(self,event):
        main_talk_focus_image=tk.PhotoImage(file="main_friend_focus.png")
        self.main_friend.config(image=main_talk_focus_image,borderwidth=0)
        self.main_friend.image = main_talk_focus_image
    def focus_out_main(self,event):
        main_talk_image=tk.PhotoImage(file="main_friend_non_click.png")
        self.main_friend.config(image=main_talk_image,borderwidth=0)
        self.main_friend.image = main_talk_image

    def top_menu_main(self):
        self.main_text = tk.Label(self.top_menu, image=self.main_text_image, background="white", borderwidth=0)
        self.main_text.place(x=21, y=49)

        self.main_convex = tk.Label(self.top_menu, image=self.main_convex_image, bg="white", borderwidth=0)
        self.main_convex.place(x=244, y=48)

        self.main_plus = tk.Label(self.top_menu, image=self.main_plus_image, bg="white", borderwidth=0)
        self.main_plus.bind("<Button-1>", self.plus_window)
        self.main_plus.place(x=281, y=48)

        self.close = tk.Label(self.top_menu, image=self.close_image, bg="white", borderwidth=0)
        self.close.place(x=306, y=10)
        self.close.bind("<Button-1>", self.close_window)

        self.mini = tk.Label(self.top_menu, image=self.mini_image, bg="white", borderwidth=0)
        self.mini.place(x=260, y=10)
        self.mini.bind("<Button-1>", self.minimize_window)

        self.big = tk.Label(self.top_menu, image=self.big_image, bg="white", borderwidth=0)
        self.big.place(x=284, y=10)
        self.big.bind("<Button-1>", self.toggle_maximize)

    def top_menu_talk(self):
        self.talk_text = tk.Label(self.top_menu, image=self.chat_text_image, background="white", borderwidth=0)
        self.talk_text.place(x=21, y=49)

        self.chat_plus_image=tk.PhotoImage(file="chat_plus.png")
        self.main_convexx = tk.Label(self.top_menu, image=self.chat_plus_image, bg="white", borderwidth=0)
        self.main_convexx.place(x=283, y=48)
        self.main_convexx.bind("<Button-1>", self.open_grouptalk_window)
        self.close = tk.Label(self.top_menu, image=self.close_image, bg="white", borderwidth=0)
        self.close.place(x=306, y=10)
        self.close.bind("<Button-1>", self.close_window)

        self.mini = tk.Label(self.top_menu, image=self.mini_image, bg="white", borderwidth=0)
        self.mini.place(x=260, y=10)
        self.mini.bind("<Button-1>", self.minimize_window)

        self.big = tk.Label(self.top_menu, image=self.big_image, bg="white", borderwidth=0)
        self.big.place(x=284, y=10)
        self.big.bind("<Button-1>", self.toggle_maximize)
    def open_grouptalk_window(self,event):
        global group_talk_windows
        if not group_talk_windows:
            group_talk_windows = True
            bb = tk.Toplevel()
            group = grouptalk_window(bb,self.friend_info,self.user_info)
            group.run()

    def click_main(self,event):
        click_main_image = tk.PhotoImage(file="main_friend.png")
        self.main_friend.config(image=click_main_image, borderwidth=0)
        self.main_friend.image = click_main_image
        main_talk_image = tk.PhotoImage(file="main_talk.png")
        self.main_talk.config(image=main_talk_image, borderwidth=0)
        self.main_talk.image = main_talk_image
        self.talk_bind()
        self.main_unbind()

        if self.top_menu.winfo_exists():
            for widget in self.top_menu.winfo_children():
                widget.destroy()
        self.top_menu_main()

        if self.inner_frame.winfo_exists():
            for widget in self.inner_frame.winfo_children():
                widget.destroy()
        self.create_main_chat_window()

    def click_talk(self,event):
        ab="[room_list],"+self.my_id
        sock.send(ab.encode())
        clic_talk_image = tk.PhotoImage(file="main_talk_click.png")
        self.main_talk.config(image=clic_talk_image, borderwidth=0)
        self.main_talk.image = clic_talk_image
        main_talk_image = tk.PhotoImage(file="main_friend_non_click.png")
        self.main_friend.config(image=main_talk_image, borderwidth=0)
        self.main_friend.image = main_talk_image
        self.talk_unbind()
        self.main_bind()

        if self.top_menu.winfo_exists():
            for widget in self.top_menu.winfo_children():
                widget.destroy()
        self.top_menu_talk()

        if self.inner_frame.winfo_exists():
            for widget in self.inner_frame.winfo_children():
                widget.destroy()
        # self.create_friend_list_window()

    def my_info_click(self,event):
        self.my_info.config(bg="#f2f2f2")
        self.profile_picture_box.config(bg="#f2f2f2")
        self.profile_name.config(bg="#f2f2f2")
        self.is_clicked = True
    def my_info_focus(self,event):
        if not self.is_clicked:
            self.my_info.config(bg="#f8f8f8")
            self.profile_picture_box.config(bg="#f8f8f8")
            self.profile_name.config(bg="#f8f8f8")
    def my_info_focus_out(self,event):
        if not self.is_clicked:
            self.my_info.config(bg="white")
            self.profile_picture_box.config(bg="white")
            self.profile_name.config(bg="white")

    def round_corners(self,im, rad):
        circle = Image.new('L', (rad * 2, rad * 2), 0)
        draw = ImageDraw.Draw(circle)
        draw.ellipse((0, 0, rad * 2, rad * 2), fill=255)
        alpha = Image.new('L', im.size, 255)
        w, h = im.size
        alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
        alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
        alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
        alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))
        im.putalpha(alpha)
        return im
    def profile_picture_update(self,picture):
        if picture == b'-':
            return tk.PhotoImage(file="common_image.png")
        else:
            image_data = io.BytesIO(picture)
            image = Image.open(image_data)
            resized_image = image.resize((54, 54))
            rounded_image = self.round_corners(resized_image, 20)
            photo_image = ImageTk.PhotoImage(rounded_image)
            return photo_image
    def set_profile_picture(self,picture):
        photo_image = self.profile_picture_update(picture)
        self.profile_picture_box.image = photo_image
        self.profile_picture_box.config(image=photo_image)
        self.profile_picture_box.update()
        self.my_info.update()
        self.scroll_area.update()
    def open_my_profile_window(self,event):
        global my_profile_windows
        if not my_profile_windows:
            my_profile_windows=True
            bb = tk.Toplevel()
            my_profile_windowa = my_profile_window(bb, self.user_info, self.set_profile_picture)
            my_profile_windowa.run()

    def friend_list_update(self):
        if not self.friend_info:
            return
        for widget in self.friend_list_frame.winfo_children():
            widget.destroy()
        self.friends_frames = {}

        for friend_row in self.friend_info:
            self.friend_count.config(text=len(self.friend_info))
            self.friend_list = tk.Frame(self.friend_list_frame, background="white", width=311, height=56,
                                        borderwidth=0)
            self.friend_list.pack(side="top")
            user_id = self.user_info[3]
            friend_id = friend_row[3]
            if user_id < friend_id: #친구아이디가 알파벳순으로 뒤에면 내꺼 앞에
                first_id, first_phone = user_id, self.user_info[1]
                second_id, second_phone = friend_id, friend_row[1]
            else:
                first_id, first_phone = friend_id, friend_row[1]
                second_id, second_phone = user_id, self.user_info[1]
            room_id = "P" +  first_phone[7:] + second_phone[7:]
            self.room_id=room_id
            self.friend_list.bind("<Double-Button-1>",lambda event, friend=friend_row,room_ida=room_id,my_info=self.user_info: self.chat_window(event, friend,room_ida,my_info))
            self.friend_picture= tk.Label(self.friend_list, bg="white", width=40, height=40)
            self.set_friend_profile_picture(friend_row[2])
            self.friend_name = tk.Label(self.friend_list, bg="white", text=friend_row[0])
            self.friend_picture.place(x=20,y=8)
            self.friend_picture.bind("<Button-1>",
                                     lambda event, user_info=friend_row: self.open_friend_profile_window(event,
                                                                                                         user_info))
            self.friend_name.place(x=72,y=22)
            self.friends_frames[friend_row[1]] = self.friend_list

    def chat_list_update(self,info):
        self.chat_log=info
        result_info = info[1]
        if not info:
            return
        for widget in self.inner_frame.winfo_children():
            widget.destroy()
        flat_list = [item for sublist in result_info for item in sublist]

        # datetime 기준으로 정렬
        sorted_info = sorted(flat_list, key=lambda x: x[5], reverse=True)
        for row in sorted_info:
            if isinstance(row[3], list):
                label_text = ', '.join(row[3])
            else:
                label_text = row[3]
            self.chat_list = tk.Frame(self.inner_frame, background="white", width=311, height=70,
                                        borderwidth=0)
            self.chat_list.pack(side="top")
            self.chat_picture= tk.Label(self.chat_list, bg="white", width=44, height=44,borderwidth=0)

            self.chat_name = tk.Label(self.chat_list, bg="white", text=label_text,borderwidth=0)
            self.chat_picture.place(x=21,y=13)
            self.set_chat_profile_picture(row[1])
            self.chat_name.place(x=80,y=19)
            display_time = self.format_chat_time(row[5])
            if "AM" in display_time:
                display_time = display_time.replace("AM", "오전")
            else:
                display_time = display_time.replace("PM", "오후")
            self.font=tk.font.Font(size=8)
            self.chat_time = tk.Label(self.chat_list, bg="white",borderwidth=0,text=display_time,fg="#bfbfbf",font=self.font)
            self.chat_time.place(x=250,y=19)

            self.chat_detail = tk.Label(self.chat_list, bg="white",borderwidth=0,fg="#969696")
            self.chat_detail.place(x=81,y=38)

            if b"[st]" in row[6] and b"[end]" in row[6]:
                self.chat_detail.config(text="사진을 보냈습니다.")
            else:
                self.chat_detail.config(text=row[6].decode())

            room_id = row[4]
            if room_id[0] == "P":
                for friend_row in self.friend_info:
                    if row[2] == friend_row[3]:
                        self.chat_list.bind("<Double-Button-1>",lambda event, friend=friend_row,room_ida=row[4],my_info=self.user_info: self.chat_window(event,friend,room_ida,my_info))
            else:
                matched_friends = []
                for friend_rowa in self.friend_info:
                    if friend_rowa[3] in row[2]:  # row[2]에 friend_row[3]이 포함되어 있는지 확인
                        matched_friends.append(friend_rowa)
                matched_friends.append(self.user_info)
                self.chat_list.bind("<Double-Button-1>",lambda event, friend=matched_friends,room_ida=row[4],my_info=self.user_info: self.create_group_window(event,friend,room_ida,my_info))

    def format_chat_time(self, chat_time):
        now = datetime.datetime.now()
        if chat_time.date() == now.date():
            display_time = chat_time.strftime('%p %I:%M').lstrip('0').replace(' 0', ' ')
            return display_time.replace("AM", "오전").replace("PM", "오후")
        elif chat_time.date() == (now - datetime.timedelta(days=1)).date():
            return "어제"
        else:
            return chat_time.strftime('%Y-%m-%d')
    def set_friend_profile_picture(self,picture):
        photo_image = self.friend_picture_add(picture)
        self.friend_picture.image = photo_image
        self.friend_picture.config(image=photo_image)

    def set_chat_profile_picture(self,picture):
        photo_image = self.chat_picture_add(picture)
        self.chat_picture.image = photo_image
        self.chat_picture.config(image=photo_image)
    def friend_picture_add(self,picture):
        if picture == b'-':
            return self.profile_picture
        else:
            image_data = io.BytesIO(picture)
            image = Image.open(image_data)
            resized_image = image.resize((40, 40))
            rounded_image = self.round_corners(resized_image, 20)
            photo_image = ImageTk.PhotoImage(rounded_image)
            return photo_image
    def chat_picture_add(self,picture):
        if picture == b'-':
            return self.chat_profile
        elif isinstance(picture, list):
            return self.profile_picture
        else:
            image_data = io.BytesIO(picture)
            image = Image.open(image_data)
            resized_image = image.resize((44, 44))
            rounded_image = self.round_corners(resized_image, 20)
            photo_image = ImageTk.PhotoImage(rounded_image)
            return photo_image

    def chat_window(self, event, friend_info,room_id,my_info):
        if room_id in chat_windows:
            chat_windows[room_id].window.lift()
            return
        my_id=my_info[3]

        message = "[pri_chat_room],"+room_id+","+my_id+","+friend_info[3]
        sock.send(message.encode())
        cc = tk.Toplevel()
        cd = chat_window(cc, friend_info,room_id,my_info)
        if room_id not in chat_windows:
            chat_windows[room_id]=cd
        cd.run()
    def create_group_window(self,event,friend_info,room_id,my_info):
        sorted_ids = sorted(friend[3] for friend in friend_info)
        id = ", ".join(sorted_ids)
        chat = ["[group_chat]", room_id, [id]]
        abcz=pickle.dumps(chat)
        sock.send(abcz)
        bb = tk.Toplevel()
        cd = group_window(bb,friend_info,room_id,my_info)
        if room_id not in chat_windows:
            chat_windows[room_id]=cd
        cd.run()
    def plus_window(self,event):
        global plus_windows
        if not plus_windows:
            plus_windows = True
            bb=tk.Toplevel()
            aa=plus_window(bb,self.user_number, self.friend_list_update)
            aa.run()
class my_profile_window: #내 프로필
    def __init__(self, main_window_profile, user_info,update_profile_ui):
        self.is_open = False
        self.user_number = user_info[1]
        self.user_info = user_info
        self.picture=user_info[2]
        self.main_window_profile = main_window_profile
        self.main_window_profile.geometry("300x600+810+200")
        self.main_window_profile.configure(bg="#81888C") ####
        self.main_window_profile.overrideredirect(True)
        self.main_window_profile.bind("<Button-1>", self.start_move)  # 마우스 버튼 누름
        self.main_window_profile.bind("<ButtonRelease-1>", self.stop_move)  # 마우스 버튼 뗌
        self.main_window_profile.bind("<B1-Motion>", self.on_move)

        self.canvas = tk.Canvas(self.main_window_profile, bg="#81888C", bd=0, highlightthickness=0, relief='ridge')
        self.canvas.place(x=0, y=495, width=300, height=2)  # 가로선 위치 및 크기 설정
        self.canvas.create_line(0, 0, 300, 0, fill="white", width=1)  # 하양색 가로선 그리기
        self.profile_window=False
        image11 = Image.open("11111.png")
        self.photo_11 = ImageTk.PhotoImage(image11)
        image11chat = Image.open("11chat.png")
        image11chatre = image11chat.resize((44, 13), Image.LANCZOS)
        self.photo_11_chat = ImageTk.PhotoImage(image11chatre)

        image22 = Image.open("22222.png")
        self.photo_22 = ImageTk.PhotoImage(image22)
        image22voice = Image.open("22voice.png")
        image22voicere = image22voice.resize((44, 13), Image.LANCZOS)
        self.photo_22_voice = ImageTk.PhotoImage(image22voicere)

        image33 = Image.open("33333.png")
        self.photo_33 = ImageTk.PhotoImage(image33)
        image33face = Image.open("33face.png")
        image33facere = image33face.resize((44, 13), Image.LANCZOS)
        self.photo_33_face = ImageTk.PhotoImage(image33facere)


        self.photo_profile = tk.PhotoImage(file="comm.png")


        image_bgimg = Image.open("bgimg.png")
        image_bgimgre = image_bgimg.resize((25, 25), Image.LANCZOS)
        self.photo_bgimg = ImageTk.PhotoImage(image_bgimgre)

        image_star = Image.open("star.png")
        image_starre = image_star.resize((25, 25), Image.LANCZOS)
        self.photo_star = ImageTk.PhotoImage(image_starre)

        image_present = Image.open("present.png")
        image_presentre = image_present.resize((25, 25), Image.LANCZOS)
        self.photo_present = ImageTk.PhotoImage(image_presentre)

        image_other = Image.open("other.png")
        image_otherre = image_other.resize((25, 25), Image.LANCZOS)
        self.photo_other = ImageTk.PhotoImage(image_otherre)

        image_X = Image.open("X.png")
        image_Xre = image_X.resize((10, 10), Image.LANCZOS)
        self.photo_X = ImageTk.PhotoImage(image_Xre)

        self.chat_label = tk.Label(main_window_profile, image=self.photo_11, bd=0, bg="#81888C")
        self.chat_label.place(x=60, y=530)
        self.chat_label1 = tk.Label(main_window_profile, image=self.photo_11_chat, bd=0, bg="#81888C")
        self.chat_label1.place(x=48, y=560)

        self.voice_label = tk.Label(main_window_profile, image=self.photo_22, bd=0, bg="#81888C")
        self.voice_label.place(x=140, y=530)
        self.voice_label1 = tk.Label(main_window_profile, image=self.photo_22_voice, bd=0, bg="#81888C")
        self.voice_label1.place(x=128, y=560)

        self.face_label = tk.Label(main_window_profile, image=self.photo_33, bd=0, bg="#81888C")
        self.face_label.place(x=220, y=530)
        self.face_label1 = tk.Label(main_window_profile, image=self.photo_33_face, bd=0, bg="#81888C")
        self.face_label1.place(x=210, y=560)

        self.profile_label = tk.Label(main_window_profile, image=self.photo_profile, bd=0, bg="#81888C")
        self.profile_label.bind("<Button-1>", lambda event: self.setup_file_send(self.user_number))
        self.profile_label.place(x=105, y=340)

        self.bgimg_label = tk.Label(main_window_profile, image=self.photo_bgimg, bd=0, bg="#81888C")
        self.bgimg_label.place(x=11, y=11)

        self.star_label = tk.Label(main_window_profile, image=self.photo_star, bd=0, bg="#81888C")
        self.star_label.place(x=44, y=11)

        self.present_label = tk.Label(main_window_profile, image=self.photo_present, bd=0, bg="#81888C")
        self.present_label.place(x=76, y=11)

        self.other_label = tk.Label(main_window_profile, image=self.photo_other, bd=0, bg="#81888C")
        self.other_label.place(x=108, y=11)

        name_font = font.Font(family="맑은 고딕", size=12)
        message_font = font.Font(family="맑은 고딕", size=10)
        self.name_label = tk.Label(main_window_profile, text=self.user_info[0], font=name_font, bg="#81888C", fg="white", borderwidth=0)  # 이름 라벨
        self.name_label.place(x=125, y=433)
        self.message_label = tk.Label(main_window_profile, text="상태 메세지", font=message_font, fg="white", bg='#81888C',highlightthickness=0)  # 이름 라벨
        self.message_label.place(x=110, y=460)

        self.X_label = tk.Label(main_window_profile, image=self.photo_X, bd=0, bg='#81888C')
        self.X_label.place(x=280, y=9)
        self.X_label.bind("<Button-1>", self.close_profile)


        self.update_profile_ui = update_profile_ui
        self.set_profile_picture(self.user_info[2])

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def stop_move(self, event):
        self.x = None
        self.y = None

    def on_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.main_window_profile.winfo_x() + deltax
        y = self.main_window_profile.winfo_y() + deltay
        self.main_window_profile.geometry(f"+{x}+{y}")

    def run(self):
        self.main_window_profile.configure(bg="#81888C")
        self.main_window_profile.resizable(False, False)
        self.main_window_profile.mainloop()

    def open_my_profile_window(self, event):
        if not self.is_open:
            self.is_open = True
            bb = tk.Toplevel()
            bb.protocol("WM_DELETE_WINDOW", self.on_profile_window_close)
            my_profile_windowa = my_profile_window(bb, self.user_info, self.set_profile_picture)
            my_profile_windowa.run()

    def on_profile_window_close(self):
        self.is_open = False
        self.main_window_profile.destroy()

    def setup_file_send(self,number):
        if not self.profile_window:  # 파일 선택 창이 이미 열려있지 않다면
            self.profile_window = True  # 파일 선택 창 열림 상태로 설정
            self.picture_add()
            self.profile_window = False
    def picture_add(self):
        filepath = filedialog.askopenfilename(
            title="Open File",
            filetypes=(("Image Files", "*.png;*.jpg;*.jpeg"),)
        )
        if filepath:
            with open(filepath, 'rb') as file:
                blob_data = file.read()
                header="[change_picture]"
                number=self.user_number
                send=[header,number,blob_data]
                aa=pickle.dumps(send)
                sock.send(aa)
                self.set_profile_picture(blob_data)
                self.update_profile_ui(blob_data)

    def round_corners(self,im, rad):
        circle = Image.new('L', (rad * 2, rad * 2), 0)
        draw = ImageDraw.Draw(circle)
        draw.ellipse((0, 0, rad * 2, rad * 2), fill=255)
        alpha = Image.new('L', im.size, 255)
        w, h = im.size
        alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
        alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
        alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
        alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))
        im.putalpha(alpha)
        return im

    def profile_picture_update(self, picture):
        if picture == b'-':
            return tk.PhotoImage(file="comm.png")
        else:
            image_data = io.BytesIO(picture)
            image = Image.open(image_data)
            resized_image = image.resize((86, 86))
            rounded_image = self.round_corners(resized_image, 20)
            photo_image = ImageTk.PhotoImage(rounded_image)
            return photo_image

    def set_profile_picture(self, picture):
        photo_image = self.profile_picture_update(picture)
        self.profile_label.image = photo_image
        self.profile_label.config(image=photo_image)
        self.profile_label.update()
        self.main_window_profile.update()

    def close_profile(self,event):
        global my_profile_windows
        my_profile_windows=False
        self.main_window_profile.destroy()
class register_window:
    def __init__(self, window):
        self.window = window
        self.window.resizable(False, False)
        self.window.title("회원가입")

        self.window.geometry("360x590+810+200")
        self.window.configure(bg='#fde900')
        self.default_texts = {"사용자이름": "사용자이름", "연락처": "연락처", "사용자계정(id)": "사용자계정(id)", "비밀번호 입력": "비밀번호 입력",
                              "비밀번호 확인": "비밀번호 확인","1999-01-01 이런식으로 입력해주세요":"1999-01-01 이런식으로 입력해주세요"}
        self.frame1 = tk.Frame(window, bg="#fde900")
        self.frame1.place(x=70, y=100)
        self.frame2 = tk.Frame(window, bg="#fde900")
        self.frame2.place(x=70, y=250)

        self.nameVar = tk.StringVar()
        self.mobileVar = tk.StringVar()
        self.idVar = tk.StringVar()
        self.pwdVar = tk.StringVar()

        self.label1 = tk.Label(self.frame1, text="회원정보", bg="#fde900", font=("굴림체", 12, "bold"))
        self.label1.pack()

        self.nameIn = tk.Entry(self.frame1, width=25, font=(12), fg='gray')
        self.nameIn.insert(0, "사용자이름")
        self.nameIn.bind("<FocusIn>",self.delete_text)
        self.nameIn.bind("<FocusOut>", lambda event, text="사용자이름": self.restore_text(event, text))
        self.nameIn.pack(side="top", pady=5)

        self.mobile = tk.Entry(self.frame1, width=25, font=(12), fg='gray')
        self.mobile.insert(0, "연락처")
        self.mobile.bind("<FocusIn>", self.delete_text)
        self.mobile.bind("<FocusOut>", lambda event, text="연락처": self.restore_text(event, text))
        self.mobile.pack(side="top", pady=5)

        self.id = tk.Entry(self.frame2, width=25, font=(12), fg='gray')
        self.id.insert(0, "사용자계정(id)")
        self.id.pack(side="top", pady=5)
        self.id.bind("<FocusIn>", self.delete_text)
        self.id.bind("<FocusOut>", lambda event, text="사용자계정(id)": self.restore_text(event, text))

        self.pwdin1 = tk.Entry(self.frame2, width=25, font=(12), fg='gray',show='*')
        self.pwdin1.insert(0, "비밀번호 입력")
        self.pwdin1.bind("<FocusIn>", self.delete_text)
        self.pwdin1.bind("<FocusOut>", lambda event, text="비밀번호 입력": self.restore_text(event, text))
        self.pwdin1.pack(side="top", pady=5)

        self.pwdin2 = tk.Entry(self.frame2, width=25, font=(12), fg='gray',show='*')
        self.pwdin2.insert(0, "비밀번호 확인")
        self.pwdin2.bind("<FocusIn>", self.delete_text)
        self.pwdin2.bind("<FocusOut>", lambda event, text="비밀번호 확인": self.restore_text(event, text))
        self.pwdin2.pack(side="top", pady=5)

        self.birth=tk.Entry(self.frame2, width=25, font=(12), fg='gray')
        self.birth.insert(0,"1999-01-01 이런식으로 입력해주세요")
        self.birth.bind("<FocusIn>", self.delete_text)
        self.birth.bind("<FocusOut>", lambda event, text="1999-01-01 이런식으로 입력해주세요": self.restore_text(event, text))
        self.birth.pack(side="top", pady=5)
        self.JoinComform = tk.Button(window, width=28, text="확 인",command=self.check_info)
        self.JoinComform.place(x=70, y=400)


    def delete_text(self, event):
        current_text = event.widget.get()
        if current_text in self.default_texts.values():
            event.widget.delete(0, "end")

    def restore_text(self, event, default_text):
        if not event.widget.get():
            event.widget.insert(0, default_text)

    def run(self):
        self.window.mainloop()
    def check_info(self):
        abc=""
        if not self.mobile.get().isdigit():
            msgbox.showinfo("알림","전화번호를 다시입력해주세요")
            return
        if not self.pwdin1.get() == self.pwdin2.get():
            msgbox.showinfo("알림", "비밀번호를 다시입력해주세요")
            return
        if self.pwdin1.get() == self.pwdin2.get():
            abc=self.pwdin2.get()
        if not "@" in self.id.get() or self.id.get()=="@":
            msgbox.showinfo("알림", "아이디를 이메일 형식으로 다시 입력해주세요")
            return
        try:
            birthdate = datetime.datetime.strptime(self.birth.get(), '%Y-%m-%d')
            current_year = datetime.datetime.now().year
            if birthdate.year > current_year:
                msgbox.showinfo("알림", "년도는 현재 년도보다 클 수 없습니다.")
                return
        except ValueError:
            msgbox.showinfo("알림", "생일은 'YYYY-MM-DD' 형식이어야 합니다.")
            return
        header_text="[register]"
        phone_number=self.mobile.get()
        name=self.nameIn.get()
        password=abc
        id=self.id.get()
        birth = self.birth.get()
        info=[header_text,name,phone_number,id,password,birth]
        print(info)
        a=pickle.dumps(info)
        sock.send(a)

class plus_window:
    def __init__(self, window,user_number, friend_list_update_callback):
        self.user_number = user_number
        self.window = window
        self.window.geometry("300x430+810+200")
        self.window.configure(bg="#ffffff")
        self.friend_list_update_callback = friend_list_update_callback
        self.window.resizable(False, False)
        self.window.overrideredirect(True)
        self.frame0=tk.Frame(window, width=260, height=27,bg="white",borderwidth=0)
        self.frame0.pack(side="top", anchor="nw", padx=10, pady=10)
        self.frame0.pack_propagate(False)
        self.label0=tk.Label(self.frame0, text="친구 추가", font=("",13, "bold"), bg="#ffffff")
        self.label0.pack(side="left", padx=10)
        self.ddd={+82:"한국",+1:"미국",+81:"일본",+86:"중국",+100:"아프카니스탄"}
        self.style=ttk.Style()
        self.notebook = ttk.Notebook(window, width=300, height=350)
        self.notebook.pack(padx=10,pady=10)
        self.frame1= tk.Frame(window, bg="#ffffff")
        self.notebook.add(self.frame1, text="  연락처로 추가")
        self.label11 = tk.Label(self.frame1, text=" ", bg="#ffffff")
        self.label11.grid(row=0, column=0,padx=5,pady=5)
        self.entry12=tk.Entry(self.frame1,width=30)                 # 친구 추가할 연락처의 이름
        self.entry12.grid(row=1,column=0, padx=5, pady=5,columnspan=3)
        self.label12 = tk.Label(self.frame1, text="0/20", bg="#ffffff")
        self.label12.grid(row=1, column=3,padx=5,pady=5)
        self.selectedKey=tk.StringVar()
        self.selectedValue=tk.StringVar()
        self.combobox1=["{}:{}".format(key,value) for key,value in self.ddd.items()]    # 국제전화 국가번호
        self.cmbxKey=ttk.Combobox(self.frame1, textvariable=self.selectedKey, values=self.combobox1)
        self.cmbxKey.config(width=4, state="readonly")
        self.cmbxKey.set("+82")
        self.cmbxKey.grid(row=2,column=0)
        self.cmbxKey.bind("<<ComboboxSelected>>",self.cmbSelect)
        self.entry13 = tk.Entry(self.frame1, width=22)              # 친구 추가할 연락처의 전화번호
        self.entry13.grid(row=2, column=1, padx=5, pady=5)
        self.label13 = tk.Label(self.frame1, text="친구의 이름과 전화번호를 입력해주세요. ", bg="#ffffff")
        self.label13.grid(row=3, column=0,padx=5,pady=5,columnspan=3)
        self.btnFrdAppend=tk.Button(self.frame1, width=10, height=2, text="친구 추가", command=self.frdAppend, relief="flat")
        self.btnFrdAppend.place(x=175, y=270)
        self.frame2=tk.Frame(window, bg="#ffffff")
        self.notebook.add(self.frame2, text="  ID로 추가")
        self.label21 = tk.Label(self.frame2, text="", bg="#ffffff")
        self.label21.grid(row=0, column=0,padx=5,pady=5)
        self.entry22=tk.Entry(self.frame2,width=32 )
        self.entry22.grid(row=1,column=0, padx=5, pady=5,columnspan=3)
        self.label23 = tk.Label(self.frame2, text="파이톡 ID를 등록하고 검색을 허용한 친구만 찾을 수 있습니다.",wraplength=250 , bg="#ffffff")
        self.label23.grid(row=2, column=0,padx=5,pady=5,columnspan=3)
        self.close_image = tk.PhotoImage(file="plus_close.png")
        self.close=tk.Label(self.window,image=self.close_image,borderwidth=0)
        self.close.place(x=280,y=10)
        self.close.bind("<Button-1>",self.close_window)
        self.frame0.bind("<Button-1>", self.start_move)  # 마우스 버튼 누름
        self.frame0.bind("<ButtonRelease-1>", self.stop_move)  # 마우스 버튼 뗌
        self.frame0.bind("<B1-Motion>", self.on_move)  # 마우스 드래그
    def start_move(self, event):

        self.x = event.x
        self.y = event.y

    def stop_move(self, event):
        self.x = None
        self.y = None

    def on_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.window.winfo_x() + deltax
        y = self.window.winfo_y() + deltay
        self.window.geometry(f"+{x}+{y}")

    def close_window(self,event):
        global plus_windows
        plus_windows=False
        self.window.destroy()

    def run(self):
        self.window.mainloop()
    def cmbSelect(self,event):
        selected_item=self.cmbxKey.get()
        selectedKey=selected_item.split(":")[0]
        self.cmbxKey.set(selectedKey)
    def frdAppend(self):
        header="[friend_add],".encode()
        myphone=self.user_number.encode()
        frdPhone = self.entry13.get().strip().encode()
        sock.send(header+myphone+b','+frdPhone)
class chat_window:
    def __init__(self, main_window, friend_info,room_id,my_info): #friend_info 채팅방판 친구1명 정보
        self.window = main_window
        self.my_info=my_info
        self.my_name=my_info[0]
        self.room_id=room_id
        self.friend_info=friend_info
        self.window.geometry("380x640+990+200")
        self.window.configure(bg="#B3B3B3")
        self.window.overrideredirect(True)
        self.top_frame=tk.Frame(self.window,borderwidth=0,relief="solid",width=378,height=89,bg="#BACEE0")
        self.top_frame.place(x=1,y=1)
        self.top_frame.pack_propagate(False)
        self.top_frame.bind("<Button-1>", self.start_move)  # 마우스 버튼 누름
        self.top_frame.bind("<ButtonRelease-1>", self.stop_move)  # 마우스 버튼 뗌
        self.top_frame.bind("<B1-Motion>", self.on_move)
        self.profile_picture = tk.PhotoImage(file="common_image_chat.png")

        self.face_talk_image = tk.PhotoImage(file="face_talk_icon_no_focus.png",master=self.window)
        self.face_talk = tk.Label(self.top_frame, image=self.face_talk_image, borderwidth=0)
        self.face_talk.bind("<Button-1>",lambda event,friend=friend_info,my_info=self.my_info: self.run_face_talk(event,friend,my_info))
        self.face_talk.place(x=310, y=43)

        self.friend_pic=tk.PhotoImage(master=self.window)
        self.friend_picture = tk.Label(self.top_frame, borderwidth=0,bg="#BACEE0")
        self.friend_picture.place(x=14,y=38)
        self.set_profile_picture_window(friend_info[2])
        self.friend_name = tk.Label(self.top_frame, text=friend_info[0],borderwidth=0,bg="#BACEE0")
        self.friend_name.place(x=66,y=42)
        #
        self.chat_count_pe_image=tk.PhotoImage(file="chat_count_pe.png",master=self.window)
        self.chat_count_pe=tk.Label(self.top_frame,image=self.chat_count_pe_image,borderwidth=0)
        self.chat_count_pe.place(x=66,y=64)
        #
        self.friend_count=tk.Label(self.top_frame,borderwidth=0,text="2",bg="#BACEE0")
        self.friend_count.place(x=80,y=61)

        self.chat_close_image=tk.PhotoImage(file="chat_close.png",master=self.window)
        self.chat_close=tk.Label(self.top_frame,image=self.chat_close_image,borderwidth=0)
        self.chat_close.bind("<Button-1>",self.close_chat)
        self.chat_close.place(x=360,y=10)

        self.chat_frame=tk.Frame(self.window,borderwidth=0,width=378,height=426,bg="#BACEE0")
        self.chat_frame.place(x=1, y=90)
        self.chat_frame.pack_propagate(False)
        # 13,10
        self.scroll_area = tk.Canvas(self.chat_frame, borderwidth=0, bg="#BACEE0", highlightthickness=0)

        # 스크롤바
        self.scrollbar = tk.Scrollbar(self.chat_frame, command=self.scroll_area.yview, borderwidth=0)
        self.scroll_area.configure(yscrollcommand=self.scrollbar.set, scrollregion=self.scroll_area.bbox("all"))

        self.scrollbar.pack(side="right", fill="y")

        self.scroll_area.pack(side="left", fill="both", expand=True)

        self.inner_frame = tk.Frame(self.scroll_area,borderwidth=0 ,bg="#BACEE0")

        self.scroll_area_window = self.scroll_area.create_window(0, 0, window=self.inner_frame, anchor="nw")
        self.inner_frame.bind("<Configure>", self.onFrameConfigure)
        self.scroll_area.bind("<Configure>", self.onCanvasConfigure)
        self.inner_frame.bind('<Enter>', self.onEnter)  # bind wheel events when the cursor enters the control
        self.inner_frame.bind('<Leave>', self.onLeave)
        self.onFrameConfigure(
            None)

        self.file_open = False
        self.send_frame=tk.Frame(self.window,borderwidth=0,relief="solid",width=378,height=123,bg="white")
        self.send_frame.place(x=1, y=516)
        self.send_entry=tk.Entry(self.send_frame,borderwidth=0,width=200,bg="white")
        self.send_entry.bind("<Return>", lambda event,friend_info=self.friend_info,user_info=self.my_info,room_id=self.room_id:self.chat_send(event,friend_info,user_info,room_id))
        self.send_entry.place(x=13,y=10)


        self.send_image=tk.PhotoImage(file="talk_send.png") #전송버튼
        self.send_button=tk.Label(self.send_frame,borderwidth=0,image=self.send_image)
        self.send_button.bind("<Button-1>",lambda event,friend_info=self.friend_info,user_info=self.my_info,room_id=self.room_id:self.chat_send(event,friend_info,user_info,room_id))
        self.send_button.place(x=316,y=85)


        self.file_send_image=tk.PhotoImage(file="file_send.png") #파일전송
        self.file_send=tk.Label(self.send_frame,borderwidth=0,image=self.file_send_image)
        self.file_send.place(x=110,y=91)
        self.file_send.bind("<Button-1>",self.setup_file_send)
        self.send_frame.pack_propagate(False)
        sock.send("[chat_fill],".encode()+room_id.encode())
        self.current_date = None



    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def stop_move(self, event):
        self.x = None
        self.y = None

    def on_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.window.winfo_x() + deltax
        y = self.window.winfo_y() + deltay
        self.window.geometry(f"+{x}+{y}")
    def close_chat(self,event):
        del chat_windows[self.room_id]
        self.window.destroy()
    def run(self):
        self.window.mainloop()
    def onFrameConfigure(self, event):
        '''Reset the scroll region to encompass the inner frame'''
        # aaa = "[room_list]," + self.room_id
        # sock.send(aaa.encode())
        self.scroll_area.configure(scrollregion=self.scroll_area.bbox(
            "all"))

    def onCanvasConfigure(self, event):
        '''Reset the canvas window to encompass inner frame when required'''
        canvas_width = event.width
        self.scroll_area.itemconfig(self.scroll_area_window,
                               width=canvas_width)
    def onMouseWheel(self, event):  # cross platform scroll wheel event
        if platform.system() == 'Windows':
            self.scroll_area.yview_scroll(int(-1 * (event.delta / 120)), "units")
        elif platform.system() == 'Darwin':
            self.scroll_area.yview_scroll(int(-1 * event.delta), "units")
        else:
            if event.num == 4:
                self.scroll_area.yview_scroll(-1, "units")
            elif event.num == 5:
                self.scroll_area.yview_scroll(1, "units")

    def onEnter(self, event):  # bind wheel events when the cursor enters the control
        if platform.system() == 'Linux':
            self.scroll_area.bind_all("<Button-4>", self.onMouseWheel)
            self.scroll_area.bind_all("<Button-5>", self.onMouseWheel)
        else:
            self.scroll_area.bind_all("<MouseWheel>", self.onMouseWheel)

    def onLeave(self, event):  # unbind wheel events when the cursorl leaves the control
        if platform.system() == 'Linux':
            self.scroll_area.unbind_all("<Button-4>")
            self.scroll_area.unbind_all("<Button-5>")
        else:
            self.scroll_area.unbind_all("<MouseWheel>")

    def round_corners(self,im, rad):
        circle = Image.new('L', (rad * 2, rad * 2), 0)
        draw = ImageDraw.Draw(circle)
        draw.ellipse((0, 0, rad * 2, rad * 2), fill=255)
        alpha = Image.new('L', im.size, 255)
        w, h = im.size
        alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
        alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
        alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
        alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))
        im.putalpha(alpha)
        return im

    def set_profile_picture(self,picture):
        photo_image = self.friend_picture_add(picture)
        self.friend_picc.image = photo_image
        self.friend_picc.config(image=photo_image)
    def set_profile_picture_window(self,picture):
        photo_image = self.friend_picture_add(picture)
        self.friend_picture.image = photo_image
        self.friend_picture.config(image=photo_image)
    def friend_picture_add(self,picture):
        if picture == b'-':

            return self.profile_picture
        else:
            image_data = io.BytesIO(picture)
            image = Image.open(image_data)
            resized_image = image.resize((40, 40))
            rounded_image = self.round_corners(resized_image, 20)

            # Image 객체로부터 ImageTk.PhotoImage 객체 생성
            photo_image = ImageTk.PhotoImage(rounded_image)
            return photo_image
    def chat_send(self,event,friend_info,my_info,room_id):
        if not self.send_entry.get()=="":
            chat="[chat],"+room_id+','+friend_info[3]+','+my_info[3]+','+self.send_entry.get()
            aaa="[room_list],"+room_id
            sock.send(chat.encode())
            time.sleep(0.2)
            sock.send(aaa.encode())
            self.send_entry.delete(0, tkinter.END)

    def setup_file_send(self,event):
        if not self.file_open:  # 파일 선택 창이 이미 열려있지 않다면
            self.file_open = True  # 파일 선택 창 열림 상태로 설정
            self.send_picture(self.friend_info, self.my_info, self.room_id)
            self.file_open = False
    def send_picture(self,friend_info,my_info,room_id):
        filepath = filedialog.askopenfilename(
            title="Open File",
            filetypes=(("Image Files", "*.png;*.jpg;*.jpeg"),)
        )
        if filepath:
            with open(filepath, 'rb') as file:
                blob_data = file.read()
                picture=b"[st]"+blob_data+b"[end]"
                chat = "[chat]," + room_id + ',' + friend_info[3] + ',' + my_info[3] + ','
                # aaa = "[room_list]," + room_id
                sock.send(chat.encode()+picture)
                # time.sleep(0.2)
                # sock.send(aaa.encode())
    def vid_info(self):
        global vid_friend_id
        vid_friend_id=self.friend_info[3]
    def run_face_talk(self,event,friend,my_info):
        global current_toCall_instance
        for state in interface_states.values():
            if state:
                return

        window= tk.Toplevel()
        self.vid_info()
        to_call_instance=toCall(window,friend,my_info)
        current_toCall_instance = to_call_instance
        to_call_instance.run()

    def insert_date_separator(self, date):
        weekdays = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일']
        weekday_index = date.weekday()
        korean_weekday = weekdays[weekday_index]
        date_str = date.strftime('%Y년 %m월 %d일 ') + korean_weekday

        canvas = tk.Canvas(self.inner_frame, height=50, bg="#BACEE0",highlightthickness=0)
        canvas.pack(fill="x", pady=10)

        self.weekday_box = tk.PhotoImage(file="weekday.png")
        canvas.create_image(180, 25, image=self.weekday_box)
        canvas.create_text(120, 25, text=date_str, anchor="w", fill="black")

        canvas.image = self.weekday_box

    def fill_chat(self,chat_list):
        aaa = "[room_list]," + self.room_id
        sock.send(aaa.encode())
        self.scroll_area.yview_moveto(1)
        last_date = None
        time_check = None
        check = 0
        try:
            if self.inner_frame.winfo_exists():
                for widget in self.inner_frame.winfo_children():
                    widget.destroy()
        except Exception as e:
            print(f"Error accessing the chat frame: {e}")
        for chat in chat_list:
            chat_date = chat[2].date()

            if last_date != chat_date:
                self.insert_date_separator(chat_date)
                last_date = chat_date
            chat_data = chat[3]

            if chat[1]==self.my_info[3]: #내가 보낸 톡이면?
                self.chat_row=tk.Frame(self.inner_frame,bg="#BACEE0", width=368, height=30,
                                        borderwidth=0)
                self.chat_row.pack(side="top",anchor="ne", pady=3)
                self.chat_row.pack_propagate(False)
                self.adfff=tk.Frame(self.chat_row,bg="#BACEE0", width=10)
                self.adfff.pack(side="right",anchor="se")
                self.chat_info=tk.Frame(self.chat_row,bg="yellow",borderwidth=0)
                self.chat_info.pack(side="right",padx=1,anchor="se")
                detail_font = tk.font.Font(size=10)
                self.chat_detail=tk.Label(self.chat_info,borderwidth=0, wraplength=240,bg="yellow",justify='left',font=detail_font)
                self.chat_detail.pack(side="right", padx=2,pady=6)

                if b"[st]" in chat_data and b"[end]" in chat_data:
                    # 이미지 데이터 추출 및 처리
                    start_idx = chat_data.find(b"[st]") + len(b"[st]")
                    end_idx = chat_data.find(b"[end]")
                    image_data = chat_data[start_idx:end_idx]
                    image_stream = io.BytesIO(image_data)
                    pil_image = Image.open(image_stream)
                    photo = ImageTk.PhotoImage(pil_image)
                    self.chat_row.pack_propagate(True)
                    self.chat_detail.image = photo  # 참조 유지
                    self.chat_detail.config(image=photo)
                else:
                    self.chat_detail.config(text=chat_data.decode('utf-8'))

                display_time = chat[2].strftime('%p %I:%M').lstrip('0').replace(' 0', ' ')
                if "AM" in display_time:
                    display_time = display_time.replace("AM", "오전")
                else:
                    display_time = display_time.replace("PM", "오후")
                time_font=tk.font.Font(size=8)
                self.time_info=tk.Frame(self.chat_row,bg="#BACEE0",borderwidth=0)
                self.time_info.pack(side="right",anchor="se",padx=2)
                self.time=tk.Label(self.time_info,borderwidth=0,text=display_time,font=time_font,bg="#BACEE0")
                self.time.pack(side="right",anchor="sw")
                self.scroll_area.yview_moveto(1)
                check=1

            else: #친구가보낸거
                chat_data = chat[3]
                if check==0 and chat[2].strftime('%I:%M')==time_check:
                    self.scroll_area.yview_moveto(1)
                    self.chat_row = tk.Frame(self.inner_frame, background="#BACEE0", width=368, height=30,
                                             borderwidth=0)
                    self.chat_row.pack(side="top",anchor="nw", pady=3)
                    self.chat_row.pack_propagate(False)
                    self.adfff = tk.Frame(self.chat_row, bg="#BACEE0", width=50)
                    self.adfff.pack(side="left", anchor="sw")
                    self.chat_info = tk.Frame(self.chat_row, bg="white", borderwidth=0)
                    self.chat_info.pack(side="left", padx=1,anchor="sw")
                    detail_font = tk.font.Font(size=10)
                    self.chat_detail = tk.Label(self.chat_info, borderwidth=0, wraplength=240,
                                                bg="white", justify='left',font=detail_font)
                    self.chat_detail.pack(side="left", padx=2,pady=6)

                    if b"[st]" in chat_data and b"[end]" in chat_data:
                        # 이미지 데이터 추출 및 처리
                        start_idx = chat_data.find(b"[st]") + len(b"[st]")
                        end_idx = chat_data.find(b"[end]")
                        image_data = chat_data[start_idx:end_idx]
                        image_stream = io.BytesIO(image_data)
                        pil_image = Image.open(image_stream)
                        photo = ImageTk.PhotoImage(pil_image)
                        self.chat_row.pack_propagate(True)
                        self.chat_detail.image = photo  # 참조 유지
                        self.chat_detail.config(image=photo)
                    else:
                        self.chat_detail.config(text=chat_data.decode('utf-8'))

                    display_time = chat[2].strftime('%p %I:%M').lstrip('0').replace(' 0', ' ')
                    time_check = chat[2].strftime('%I:%M')
                    if "AM" in display_time:
                        display_time = display_time.replace("AM", "오전")
                    else:
                        display_time = display_time.replace("PM", "오후")
                    time_font = tk.font.Font(size=8)
                    self.time_info = tk.Frame(self.chat_row, bg="#BACEE0", borderwidth=0)
                    self.time_info.pack(side="left", anchor="sw", padx=2)
                    self.time = tk.Label(self.time_info, borderwidth=0, text=display_time,font=time_font,bg="#BACEE0")
                    self.time.pack(side="left",anchor="sw")
                    self.scroll_area.yview_moveto(1)
                    check = 0

                else:
                    self.scroll_area.yview_moveto(1)
                    self.chat_row = tk.Frame(self.inner_frame, background="#BACEE0", width=368, height=50,
                                             borderwidth=0)
                    self.chat_row.pack(side="top", anchor="nw", pady=3)
                    self.chat_row.pack_propagate(False)
                    self.adfff = tk.Frame(self.chat_row, bg="#BACEE0", width=10,borderwidth=2,relief="solid")
                    self.adfff.pack(side="left", anchor="sw")
                    self.friend_picc = tk.Label(self.chat_row,
                                                   borderwidth=0, bg="#BACEE0")
                    self.friend_picc.pack(side="left",anchor="nw",)
                    self.set_profile_picture(self.friend_info[2])
                    # self.box=tk.Frame(self.chat_row,bg="#BACEE0",borderwidth=2,relief="solid")
                    # self.box.pack(side="left")
                    self.friend_nam = tk.Label(self.chat_row, text=self.friend_info[0],
                                                   borderwidth=0, bg="#BACEE0")
                    self.friend_nam.pack(side="top", anchor="nw")
                    detail_font = tk.font.Font(size=10)
                    self.chat_box = tk.Frame(self.chat_row, borderwidth=0, bg="#BACEE0")
                    self.chat_box.pack(side="top", anchor="sw")
                    self.chat_detail = tk.Label(self.chat_box, borderwidth=0, wraplength=240,
                                                bg="white", justify='left', font=detail_font)
                    self.chat_detail.pack(side="left", padx=2, pady=6)

                    if b"[st]" in chat_data and b"[end]" in chat_data:
                        # 이미지 데이터 추출 및 처리
                        start_idx = chat_data.find(b"[st]") + len(b"[st]")
                        end_idx = chat_data.find(b"[end]")
                        image_data = chat_data[start_idx:end_idx]
                        image_stream = io.BytesIO(image_data)
                        pil_image = Image.open(image_stream)
                        photo = ImageTk.PhotoImage(pil_image)
                        self.chat_row.pack_propagate(True)
                        self.chat_detail.image = photo  # 참조 유지
                        self.chat_detail.config(image=photo)
                    else:
                        self.chat_detail.config(text=chat_data.decode('utf-8'))

                    display_time = chat[2].strftime('%p %I:%M').lstrip('0').replace(' 0', ' ')
                    time_check = chat[2].strftime('%I:%M')
                    if "AM" in display_time:
                        display_time = display_time.replace("AM", "오전")
                    else:
                        display_time = display_time.replace("PM", "오후")
                    time_font = tk.font.Font(size=8)
                    self.time_info = tk.Frame(self.chat_box, bg="#BACEE0", borderwidth=0)
                    self.time_info.pack(side="left", padx=2)
                    self.time = tk.Label(self.time_info, borderwidth=0, text=display_time, font=time_font, bg="#BACEE0")
                    self.time.pack(side="left")
                    check = 0
                    self.scroll_area.yview_moveto(1)
            self.scroll_area.yview_moveto(1)
class fromCall: #페이스톡 왔을 때의 화면
    def __init__(self, fromCall,friend_name,id,id2):
        interface_states["fromCall"] = True
        self.fromCall = fromCall
        self.fromCall.title("페이스톡")
        self.fromCall.geometry("391x540+810+200")
        self.fromCall.configure(bg="black")
        self.friend_name=friend_name.decode()
        self.id=id.decode()
        self.id2=id2.decode()
        self.delay = 1
        self.canvas = tkinter.Canvas(self.fromCall, width=370, height=240)
        self.canvas.place(x=8, y=10)
        self.running=True

        self.t = threading.Thread(target=self.cam)
        self.t.daemon = True
        self.t.start()

        self.decimg = 0

        label_font = font.Font(family="맑은 고딕", size=15, weight="bold")
        self.name_label = tk.Label(fromCall, text=self.friend_name, font=label_font, bg="black", fg="white", highlightthickness=0)#이름 라벨
        self.name_label.place(x=170, y= 270)
        self.wait_label = tk.Label(fromCall, text="페이스톡 해요", font=label_font, bg='black', fg="white", highlightthickness=0)
        self.wait_label.place(x=130, y= 330)
        image = Image.open("hangup.png")#통화거절 이미지
        image2 = image.resize((60, 60), Image.LANCZOS)#버튼 크기에 맞게 이미지 조절
        self.photo2 = ImageTk.PhotoImage(image2)

        image = Image.open("answer.png")#통화받기 이미지
        image1 = image.resize((60, 60), Image.LANCZOS)#버튼 크기에 맞게 이미지 조절
        self.photo1 = ImageTk.PhotoImage(image1)

        self.fromCall_deny_btn = tk.Button(fromCall, image=self.photo1, command=self.fromCall_answer, width=60, height=60, bd=0, bg="black", activebackground="black")
        self.fromCall_deny_btn.place(x=120, y=400)
        self.fromCall_answer_btn = tk.Button(fromCall, image=self.photo2, command=self.fromCall_deny, width=60, height=60, bd=0, bg="black", activebackground="black")
        self.fromCall_answer_btn.place(x=200, y=400)
        self.info_vid()
        self.update()
    def run(self):
        self.fromCall.mainloop()
    def info_vid(self):
        global vid_friend_id
        vid_friend_id=self.id

    def cam(self):
        capture = cv2.VideoCapture(0)
        while self.running:
            ret, frame = capture.read()
            if ret ==False:
                continue
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY),90]
            result, imgencode = cv2.imencode('.jpg',frame,encode_param)
            data=np.array(imgencode)
            stringData=data.tobytes()
            # video_data=stringData
            # friend_id = self.friend+','
            # sock.send(b'[video],'+friend_id.encode()+video_data)
            data = np.frombuffer(stringData, dtype='uint8')
            self.decimg = cv2.imdecode(data, 1)

        capture.release()
    def update(self):
        try:
            pil_image = PIL.Image.fromarray(cv2.cvtColor(self.decimg, cv2.COLOR_BGR2RGB))
            resized_image = pil_image.resize((370, 240))
            self.photo = PIL.ImageTk.PhotoImage(image=resized_image)
            self.canvas.create_image(0, 0, image=self.photo, anchor=tkinter.NW)

        except Exception as e:
            print("예외 발생:", e)

        self.fromCall.after(self.delay, self.update)

    def fromCall_answer(self):#받기 버튼 눌렀을 때 함수
        interface_states["fromCall"] = False
        id=self.id.encode()
        id2=self.id2.encode()
        sock.send(b'[answer],'+id+b","+id2)
        self.fromCall_deny()
    def fromCall_deny(self):#거절 버튼 눌렀을 때 함수
        interface_states["fromCall"] = False
        self.running = False
        self.t.join()
        self.fromCall.destroy()
class toCall:
    def __init__(self, toCall,friend_id,my_info):
        interface_states["toCall"] = True
        self.toCall = toCall
        self.friend_info=friend_id
        self.friend_id=friend_id[3]
        self.my_name=my_info[0]
        self.my_id=my_info[3]
        self.running=True
        self.toCall.title("페이스톡")
        self.toCall.geometry("391x540")
        self.toCall.configure(bg="black")
        self.delay = 1
        self.canvas = tkinter.Canvas(self.toCall, width=370, height=240)
        self.canvas.place(x=8, y=10)

        self.t= threading.Thread(target=self.cam)
        self.t.daemon=True
        self.t.start()

        self.button_frame = tkinter.Frame(self.toCall, bg="black")
        self.button_frame.place(x=160, y=400)
        self.decimg=0

        label_font = font.Font(family="맑은 고딕", size=15, weight="bold")
        self.name_label = tk.Label(toCall, text=self.friend_info[0], font=label_font, bg="black", fg="white", highlightthickness=0)  # 이름 라벨
        self.name_label.place(x=165, y=270)
        self.wait_label = tk.Label(toCall, text="연결 중 입니다...", font=label_font, bg='black', fg="white", highlightthickness=0)
        self.wait_label.place(x=120, y=330)

        image = Image.open("hangup.png")  # 통화 종료 이미지
        image2 = image.resize((60, 60), Image.LANCZOS)  # 버튼 크기에 맞게 이미지 조절
        self.photo2 = ImageTk.PhotoImage(image2)

        self.toCall_end_btn = tk.Button(self.button_frame, image=self.photo2, command=self.toCall_end, width=60, height=60, bd=0, bg="black", activebackground="black")
        self.toCall_end_btn.pack(side="left")

        self.update()

    def cam(self):
        sock.send(b'[call],' + self.friend_id.encode() + b',' + self.my_name.encode() + b',' + self.my_id.encode())
        capture = cv2.VideoCapture(0)
        time.sleep(0.5)
        while self.running:
            ret, frame = capture.read()
            if ret ==False:
                continue
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY),90]
            result, imgencode = cv2.imencode('.jpg',frame,encode_param)
            data=np.array(imgencode)
            stringData=data.tobytes()
            # video_data=stringData
            # friend_id = self.friend_info[1]+','
            # sock.send(b'[video],'+friend_id.encode()+video_data)
            data = np.frombuffer(stringData, dtype='uint8')
            self.decimg = cv2.imdecode(data, 1)
            mycam_queue.put(self.decimg)

        capture.release()

    def update(self):
        try:
            if not mycam_queue.empty():
                frame=mycam_queue.get()
                pil_image = PIL.Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                resized_image = pil_image.resize((370, 240))
                self.photo = PIL.ImageTk.PhotoImage(image=resized_image)
                self.canvas.create_image(0, 0, image=self.photo, anchor=tkinter.NW)

        except Exception as e:
            pass

        self.toCall.after(self.delay, self.update)
    def toCall_end(self): #버튼 눌렀을 때 실행 함수
        interface_states["toCall"] = False
        self.running = False
        self.t.join()
        self.toCall.destroy()

    def run(self):
        self.toCall.mainloop()
class start_call: #페이스톡 통화 화면
    def __init__(self, call):
        interface_states["start_call"] = True
        self.call=call
        self.call.title("페이스톡")
        self.call.geometry("391x540+810+200")
        self.call.configure(bg="black")

        self.running = True
        self.t = threading.Thread(target=self.cam)
        self.t.daemon = True
        self.t.start()

        self.delay = 1
        self.flags = 0
        self.canvas = tkinter.Canvas(self.call, width=320, height=190) #내 화면
        self.canvas.place(x=35, y=10)
        self.result_img=0
        self.canvas1 = tkinter.Canvas(self.call, width=320, height=190) #상대방 화면
        self.canvas1.place(x=35, y=215)
        self.decimg=0
        self.fri_decimg=0
        self.filter_frame = tkinter.Frame(call, width=325, height=50, bd=0) #필터 공간 프레임
        self.filter_frame_visible = False

        image = Image.open("hangup.png") #전화 끊기
        image2 = image.resize((45,45), Image.LANCZOS)
        self.photo2 = ImageTk.PhotoImage(image2)

        image = Image.open("effect.png")  #필터 효과 이미지
        image3 = image.resize((45, 45), Image.LANCZOS)  # 버튼 크기에 맞게 이미지 조절
        self.photo3 = ImageTk.PhotoImage(image3)

        image = Image.open("nocam.png")  #카메라 끄기 이미지
        image4 = image.resize((55, 55), Image.LANCZOS)  # 버튼 크기에 맞게 이미지 조절
        self.photo4 = ImageTk.PhotoImage(image4)

        image = Image.open("bar.png") #필터 버튼 클릭시 생성되는 바 이미지
        image5 = image.resize((350, 80), Image.LANCZOS)
        self.photo5 = ImageTk.PhotoImage(image5)

        image = Image.open("gray.png") #필터: 흑백
        image_gray = image.resize((40,40), Image.LANCZOS)
        self.photo_gray = ImageTk.PhotoImage(image_gray)

        image = Image.open("zoom_out.png") #필터: 오목거울
        image_zoom_out = image.resize((60, 60), Image.LANCZOS)
        self.photo_zoom_out = ImageTk.PhotoImage(image_zoom_out)

        image = Image.open("blossom.png") #필터: 벚꽃
        image_blossom = image.resize((40, 40), Image.LANCZOS)
        self.photo_blossom = ImageTk.PhotoImage(image_blossom)

        self.img_tree = cv2.imread('tree1.png', cv2.IMREAD_COLOR)
        self.img_tree = cv2.resize(self.img_tree, (263, 186))
        self.img_tree = cv2.cvtColor(self.img_tree, cv2.COLOR_BGR2RGB)

        image = Image.open("wave.png") #필터: 파도
        image_wave = image.resize((45, 45), Image.LANCZOS)
        self.photo_wave = ImageTk.PhotoImage(image_wave)

        image = Image.open("mosaic.png") #필터: 모자이크
        image_mosaic = image.resize((40, 40), Image.LANCZOS)
        self.photo_mosaic = ImageTk.PhotoImage(image_mosaic)

        image = Image.open("return.png") #필터: 원본
        image_return = image.resize((35, 35), Image.LANCZOS)
        self.photo_return = ImageTk.PhotoImage(image_return)

        image = Image.open("standard.PNG") #카메라 끄면 나오는 스탠다드 화면
        image_no_cam = image.resize((100, 100), Image.LANCZOS)
        self.photo_no_cam = ImageTk.PhotoImage(image_no_cam)

        self.call_end_btn = tk.Button(call, image=self.photo2, command=self.call_end, width=45, height=45, bd=0, bg="black", activebackground="black")
        self.call_end_btn.place(x=172, y=477)

        self.call_effect_btn = tk.Button(call, image=self.photo3, command=self.call_effect, width=45, height=45, bd=0, bg="black", activebackground="black")
        self.call_effect_btn.place(x=105, y=476)

        self.no_cam_btn = tk.Button(call, image=self.photo4, command=self.flagchange_no_cam, width=60, height=60, bd=0, bg="black", activebackground="black")
        self.no_cam_btn.place(x=230, y=470)

        self.filter_bar = tk.Label(self.filter_frame, image=self.photo5, width=325, height=55, bd=0, bg="black")
        self.filter_bar.pack()

        self.filter_gray_btn = tk.Button(self.filter_frame, image=self.photo_gray, command=self.flagchange_gray, width=40, height=40, bd=0, bg="#403F3D", activebackground="#403F3D")
        self.filter_gray_btn.place(x=13, y=5)

        self.filter_zoom_out_btn = tk.Button(self.filter_frame, image=self.photo_zoom_out, command=self.flagchange_zoom_out, width=40, height=40, bd=0, bg="#403F3D", activebackground="#403F3D")
        self.filter_zoom_out_btn.place(x=64, y=5)

        self.filter_blossom_btn = tk.Button(self.filter_frame, image=self.photo_blossom, command=self.flagchange_blossom, width=40, height=40, bd=0, bg="#403F3D", activebackground="#403F3D")
        self.filter_blossom_btn.place(x=115, y=5)

        self.filter_wave_btn = tk.Button(self.filter_frame, image=self.photo_wave, command=self.flagchange_wave, width=40, height=40, bd=0, bg="#403F3D", activebackground="#403F3D")
        self.filter_wave_btn.place(x=165, y=5)

        self.filter_mosaic_btn = tk.Button(self.filter_frame, image=self.photo_mosaic, command=self.flagchange_mosaic, width=40, height=40, bd=0, bg="#403F3D", activebackground="#403F3D")
        self.filter_mosaic_btn.place(x=215, y=5)

        self.filter_return_btn = tk.Button(self.filter_frame, image=self.photo_return, command=self.flagchange_ret, width=40, height=40, bd=0, bg="#403F3D", activebackground="#403F3D")
        self.filter_return_btn.place(x=265, y=5)

        self.update()
        self.update1()
        self.wavefilter_count = 0
        self.e = cv2.VideoCapture("e.mp4")
        self.img_tree = cv2.imread('tree1.png', cv2.IMREAD_COLOR)
        self.img_tree = cv2.resize(self.img_tree, (300, 150))
        self.img_tree = cv2.cvtColor(self.img_tree, cv2.COLOR_BGR2RGB)

    def call_end(self):  # 버튼 눌렀을 때 실행 함수
        interface_states["start_call"] = False
        self.running = False
        self.t.join(timeout=1)  # 5초 동안 대기
        self.call.destroy()
    def cam(self):
        capture = cv2.VideoCapture(0)
        global vid_friend_id
        global sock
        aa= vid_friend_id

        while True:
            global abc
            ret, frame = capture.read()
            if ret ==False:
                continue
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY),90]
            frame=cv2.resize(frame,(320,190))
            imgencode = cv2.imencode('.jpg',frame)[1].tobytes()
            # data=np.array(imgencode)
            # stringData=data.tostring() #스트링데이터는 50000에서 6만으로나옴

            friend_id = aa+','
            abc=friend_id.encode()
            video=b'[start_video],'+abc+imgencode+b','+b'[end_video]'
            # video_queue.put(video)
            # # sock.sendall(video)
            sock.sendall(video)
            data = np.frombuffer(imgencode, dtype='uint8')
            self.result_img = cv2.imdecode(data, 1)
    def call_effect(self): #필터 효과 버튼 눌렀을 때 실행 함수
        if self.filter_frame_visible:
            self.filter_frame.place_forget()
        else:
            self.filter_frame.place(x=35, y=420)
        self.filter_frame_visible = not self.filter_frame_visible

    def gray(self,frame): #흑백 필터
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blr = cv2.GaussianBlur(gray, (0, 0), 2)
        pil_image = PIL.Image.fromarray(blr)
        resized_image = pil_image.resize((370, 240))
        return resized_image

    def zoom_out(self,frame):
        if frame is not None:
            rows, cols = frame.shape[:2]  # 너비 추출
            exp = 0.5  # 오목 지수
            scale = 1.3  # 변환 영역 크기
            map_y, map_x = np.indices((rows, cols), dtype=np.float32)
            map_x = 2 * map_x / (cols - 1) - 1
            map_y = 2 * map_y / (rows - 1) - 1
            r, theta = cv2.cartToPolar(map_x, map_y)
            r[r < scale] = r[r < scale] ** exp
            map_x, map_y = cv2.polarToCart(r, theta)
            map_x = ((map_x + 1) * cols - 1) / 2
            map_y = ((map_y + 1) * rows - 1) / 2
            distorted = cv2.remap(frame, map_x, map_y, cv2.INTER_LINEAR)
            pil_image = PIL.Image.fromarray(distorted)
            resized_image = pil_image.resize((370, 240))
            return resized_image

    def blossom(self, decimg): #벚꽃
        tree_area = decimg[:self.img_tree.shape[0], :self.img_tree.shape[1]]
        result = cv2.add(tree_area, self.img_tree)
        decimg[:self.img_tree.shape[0], :self.img_tree.shape[1]] = result
        if self.e.get(cv2.CAP_PROP_POS_FRAMES) == self.e.get(cv2.CAP_PROP_FRAME_COUNT):
            self.e.set(cv2.CAP_PROP_POS_FRAMES, 0)
        rt1, frame1 = self.e.read()
        if rt1:
            frame1 = cv2.resize(frame1, (decimg.shape[1], decimg.shape[0]))
            distorted = cv2.add(decimg, frame1)
            pil_image = PIL.Image.fromarray(distorted)
            resized_image = pil_image.resize((370, 240))
            return resized_image

    def wave(self,frame): #파도
        rows, cols = frame.shape[:2]
        mapy, mapx = np.indices((rows, cols), dtype=np.float32)
        mapx = mapx.astype(np.float32)
        mapy = mapy.astype(np.float32)
        self.wavefilter_count += 1
        displacement = self.wavefilter_count * 30
        mapy_shifted = mapy + displacement
        l = 60
        amp = 50
        sinx = mapx + amp * np.sin(mapy_shifted / l)
        cosy = mapy + amp * np.cos(mapx / l)
        distorted = cv2.remap(frame, sinx, mapy, cv2.INTER_LINEAR)
        pil_image = PIL.Image.fromarray(distorted)
        resized_image = pil_image.resize((370, 240))
        return resized_image

    def mosaic(self, frame): #모자이크
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 2)  # 불러온 데이터 기반으로 객체 검출
        for (x, y, w, h) in faces:
            roi = frame[y:y + h, x:x + w]
            factor = 20  # 모자이크 픽셀 크기 조절
            small_roi = cv2.resize(roi, (w // factor, h // factor))
            mosaic_roi = cv2.resize(small_roi, (w, h), interpolation=cv2.INTER_NEAREST)
            frame[y:y + h, x:x + w] = mosaic_roi

        pil_image = PIL.Image.fromarray(frame)
        resized_image = pil_image.resize((370, 240))
        return resized_image


    def ret(self,frame): #원본
        pass

    def update(self):
        try:
            vid = cv2.cvtColor(self.result_img, cv2.COLOR_BGR2RGB)
            pil_image = PIL.Image.fromarray(vid)
            resized_image = pil_image.resize((320, 190))

            if self.flags == 0:
                vid = self.ret(vid)
            if self.flags == 1:
                resized_image = self.gray(vid)
            if self.flags == 2:
                resized_image = self.zoom_out(vid)
            if self.flags == 3:
                resized_image = self.blossom(vid)
            if self.flags == 4:
                resized_image = self.wave(vid)
            if self.flags == 5:
                resized_image = self.mosaic(vid)
            if self.flags == 6:
                pass

            self.photo = PIL.ImageTk.PhotoImage(image=resized_image)
            self.canvas.create_image(0, 0, image=self.photo, anchor=tkinter.NW)


        except Exception as e:
            print("예외 발생:", e)

        self.call.after(self.delay, self.update)

    def update1(self):
        try:
            if not friend_queue.empty():
                frame = friend_queue.get()
                frame1 = cv2.imdecode(np.frombuffer(frame, dtype=np.uint8), cv2.IMREAD_COLOR)
                # data = np.frombuffer(frame, dtype='uint8')
                # result_img = cv2.imdecode(data, 1)
                vid = cv2.cvtColor(frame1,cv2.COLOR_BGR2RGB)
                pil_image = PIL.Image.fromarray(vid)
                # resized_image = pil_image.resize((320, 190))

                # if self.flags == 0:
                #     vid = self.ret(vid)
                # if self.flags == 1:
                #     resized_image = self.gray(vid)
                # if self.flags == 2:
                #     resized_image = self.zoom_out(vid)
                # if self.flags == 3:
                #     resized_image = self.blossom(vid)
                # if self.flags == 4:
                #     resized_image = self.wave(vid)
                # if self.flags == 5:
                #     resized_image = self.mosaic(vid)
                # if self.flags == 6:
                #     pass

                self.photo350 = PIL.ImageTk.PhotoImage(image=pil_image)
                self.canvas1.create_image(0, 0, image=self.photo350, anchor=tkinter.NW)


        except Exception as e:
            print("예외 발생:", e)

        self.call.after(self.delay, self.update1)
    def run(self):
        self.call.mainloop()
    def flagchange_gray(self):
        self.flags = 1
    def flagchange_zoom_out(self):
        self.flags = 2
    def flagchange_blossom(self):
        self.flags = 3
    def flagchange_wave(self):
        self.flags = 4
    def flagchange_mosaic(self):
        self.flags = 5
    def flagchange_no_cam(self):
        self.flags = 6
    def flagchange_ret(self):
        self.flags = 0
class showBirthday:
    def __init__(self, root,phone,birth_info):
        self.image_profile = None
        self.image_cake = tk.PhotoImage(file='cake_icon.png')
        self.image_gift = tk.PhotoImage(file="gift_icon.png")
        self.profile_picture = tk.PhotoImage(file="profile_icon.png")
        self.birth_info=birth_info
        self.my_phone=phone
        self.root = root
        self.root.geometry("340x480+810+200")
        self.root.configure(bg="white")
        self.root.resizable(0, 0)
        self.close_image=tk.PhotoImage(file="birth_close.png")
        self.close=tk.Label(root,image=self.close_image,borderwidth=0)
        self.close.place(x=320,y=10)
        self.close.bind("<Button-1>",self.birth_close)
        self.today = datetime.datetime.now()
        self.dfont = tkinter.font.Font(family="맑은 고딕", size=8)
        self.root.overrideredirect(True)
        self.frame0 = tk.Frame(root, width=340, height=20,borderwidth=0)             # 최상위 창(창 타이틀)
        self.frame0.pack(side="top", anchor="nw", padx=20, pady=2)
        self.root.bind("<Button-1>", self.start_move)  # 마우스 버튼 누름
        self.root.bind("<ButtonRelease-1>", self.stop_move)  # 마우스 버튼 뗌
        self.root.bind("<B1-Motion>", self.on_move)  # 마우스 드래그
        self.label0 = tk.Label(self.frame0, text="생일인 친구", font=("맑은 고딕", 12, ""), bg="white")
        self.label0.pack()

        # 스크롤 최외곽 창
        self.scroll_frame = tk.Frame(root, borderwidth=0, bg="white")
        self.scroll_frame.pack(side='left', fill='both', expand=True)

        # 스크롤 전체 캔버스
        self.scroll_area = tk.Canvas(self.scroll_frame, borderwidth=0, bg="white", highlightthickness=0)

        # 스크롤바
        self.scrollbar = tk.Scrollbar(self.scroll_frame, command=self.scroll_area.yview, borderwidth=0)
        self.scroll_area.configure(yscrollcommand=self.scrollbar.set, scrollregion=self.scroll_area.bbox("all"))
        self.scrollbar.pack(side="right", fill="y")
        self.scroll_area.pack(side="left", fill="both", expand=True)
        self.inner_frame = tk.Frame(self.scroll_area, bg="white")  # , borderwidth=2, relief="solid"
        self.scroll_area_window = self.scroll_area.create_window(0, 0, window=self.inner_frame, anchor="nw")

        self.inner_frame.bind("<Configure>", self.onFrameConfigure)
        self.scroll_area.bind("<Configure>", self.onCanvasConfigure)
        self.inner_frame.bind('<Enter>', self.onEnter)  # bind wheel events when the cursor enters the control
        self.inner_frame.bind('<Leave>', self.onLeave)
        self.onFrameConfigure(None)

        self.calcBirthday()
    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def stop_move(self, event):
        self.x = None
        self.y = None

    def on_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")
    def birth_close(self,event):
        global birth_windows
        birth_windows=False
        self.root.destroy()
    def onFrameConfigure(self, event):              # 스크롤 프레임의 설정
        '''Reset the scroll region to encompass the inner frame'''
        self.scroll_area.configure(scrollregion=self.scroll_area.bbox("all"))

    def onCanvasConfigure(self, event):             # 스크롤 캔버스의 설정
        '''Reset the canvas window to encompass inner frame when required'''
        canvas_width = event.width
        self.scroll_area.itemconfig(self.scroll_area_window, width=canvas_width)

    def onMouseWheel(self, event):  # cross platform scroll wheel event
        if platform.system() == 'Windows':
            self.scroll_area.yview_scroll(int(-1 * (event.delta / 120)), "units")
        elif platform.system() == 'Darwin':
            self.scroll_area.yview_scroll(int(-1 * event.delta), "units")
        else:
            if event.num == 4:
                self.scroll_area.yview_scroll(-1, "units")
            elif event.num == 5:
                self.scroll_area.yview_scroll(1, "units")

    def onEnter(self, event):  # bind wheel events when the cursor enters the control
        if platform.system() == 'Linux':
            self.scroll_area.bind_all("<Button-4>", self.onMouseWheel)
            self.scroll_area.bind_all("<Button-5>", self.onMouseWheel)
        else:
            self.scroll_area.bind_all("<MouseWheel>", self.onMouseWheel)

    def onLeave(self, event):  # unbind wheel events when the cursorl leaves the control
        if platform.system() == 'Linux':
            self.scroll_area.unbind_all("<Button-4>")
            self.scroll_area.unbind_all("<Button-5>")
        else:
            self.scroll_area.unbind_all("<MouseWheel>")

    def set_friend_profile_picture(self,picture):   # 친구 프로파일 이미지 설정
        photo_image = self.friend_picture_add(picture)
        self.label_profile.image = photo_image
        self.label_profile.config(image=photo_image)

    def friend_picture_add(self,picture):           # # 친구 프로파일 이미지 규격설정
        if picture == b'-':
            return self.profile_picture
        else:
            image_data = io.BytesIO(picture)
            image = PIL.Image.open(image_data)
            resized_image = image.resize((40, 40))
            photo_image = ImageTk.PhotoImage(resized_image)
            return photo_image


    def calcBirthday(self):
        frd_birthdays = self.birth_info  # DB에서 불러온 친구의 생일날짜
        today_list = []
        pass_list = []
        come_list = []
        for row in frd_birthdays:
            birthday = row[1].replace(year=self.today.year)  # 생년월일의 년도를 현재 년도로 변경
            row = (row[0],birthday, row[2], row[3])
            td = (self.today.date() - birthday).days  # 오늘날짜에서 친구의 생일날짜를 뺀값.
            if td == 0:  # 오늘 생일자
                today_list.append(row)
            elif 0 < td < 3:  # 지난 생일자
                pass_list.append(row)
            elif -3 < td < 0:  # 다가올 생일자
                come_list.append(row)

        self.showFrame("오늘 생일", today_list)
        self.showFrame("지난 생일", pass_list)
        self.showFrame("다가오는 생일", come_list)

    def showFrame(self, ftext, birthday_list):
        if birthday_list:
            self.frame = tk.Frame(self.inner_frame, width=340, height=10, bg="white")
            self.frame.pack(side="top", anchor="nw", padx=20, pady=2)
            self.label_text = tk.Label(self.inner_frame, text=ftext, font=("", 10, "bold"), bg="white")
            self.label_text.pack(side="top", anchor="nw", padx=20, pady=2)
        else:
            pass
        self.set_dates=set()
        for row in birthday_list:
            Ddate = row[1]
            self.currentRow=row
            if Ddate not in self.set_dates:
                self.set_dates.add(Ddate)
                self.label_date = tk.Label(self.inner_frame, text=row[1].strftime("%m월 %d일"), font=self.dfont, bg="white",
                                        fg='gray')
                self.label_date.pack(side="top", anchor="nw", padx=20, pady=2)
                self.frameContent()
            else :
                self.frameContent()

    def frameContent(self):
        self.frame_content = tk.Frame(self.inner_frame, width=340, height=55, relief="flat", bd=2, bg="white")     # 생일자 개인 프레임 만들기
        self.frame_content.pack(side="top", anchor="nw", padx=0, pady=2)

        # 친구의 프로파일 이미지 띄우기
        self.label_profile = tk.Label(self.frame_content, image=self.image_profile, bg="white")
        self.label_profile.place(x=15, y=3)
        self.set_friend_profile_picture(self.currentRow[3])
        self.label_name = tk.Label(self.frame_content, text=self.currentRow[2], bg="white")        # 친구의 이름 띄우기
        self.label_name.place(x=65, y=15)
        td = (self.today.date() - self.currentRow[1]).days
        if td == 0 :                      # 오늘 생일자만 케익이미지 띄우기
            self.label_cake = tk.Label(self.frame_content, image=self.image_cake, bg="white")
            self.label_cake.place(x=105, y=14)
        else:
            pass
        self.label_gift = tk.Label(self.frame_content, image=self.image_gift, bg="white")
        self.label_gift.place(x=240, y=10)
    def run(self):
        self.root.mainloop()
class grouptalk_window:
    def __init__(self, main_window, friend_info,my_info):
        self.window = main_window
        self.window.geometry("370x600")
        self.window.configure(bg="white")
        self.top_frame=tk.Frame(self.window,width=368,height=88,bg="white")
        self.top_frame.place(x=1,y=1)
        self.top_frame.pack_propagate(False)
        self.window.overrideredirect(True)
        self.top_frame.bind("<Button-1>", self.start_move)  # 마우스 버튼 누름
        self.top_frame.bind("<ButtonRelease-1>", self.stop_move)  # 마우스 버튼 뗌
        self.top_frame.bind("<B1-Motion>", self.on_move)
        self.friend_info=friend_info
        self.my_info=my_info
        self.filtered_friends = friend_info
        self.top_text_image=tk.PhotoImage(file="group_talk_text.png")
        self.top_text=tk.Label(self.top_frame, image=self.top_text_image, borderwidth=0)
        self.top_text.place(x=22,y=40)

        self.close_image=tk.PhotoImage(file="group_close.png")
        self.close=tk.Label(self.top_frame, image=self.close_image,borderwidth=0)
        self.close.place(x=350, y=10)
        self.close.bind("<Button-1>",self.close_window)

        self.search_frame=tk.Frame(self.window,width=368,height=49,bg="white",borderwidth=0)
        self.search_frame.place(x=1,y=89)
        self.search_frame.pack_propagate(False)

        self.search_box_image = tk.PhotoImage(file="search_box.png")
        self.search_box=tk.Label(self.search_frame,image=self.search_box_image,borderwidth=0,bg="white")
        self.search_box.place(x=20,y=0)

        self.search_entry = tk.Entry(self.search_frame,relief="flat")
        self.search_entry.place(x=59,y=9)
        self.search_entry.bind("<KeyRelease>", self.filter_friends)

        self.friend_list_frame=tk.Frame(self.window,width=368,height=384,borderwidth=0,bg="white")
        self.friend_list_frame.place(x=1,y=138)
        self.friend_list_frame.pack_propagate(False)

        self.border_bottom_frame=tk.Frame(self.window,width=370,height=79,borderwidth=0,bg="#e6e6e6")
        self.border_bottom_frame.place(x=0,y=521)
        self.bottom_frame=tk.Frame(self.border_bottom_frame,width=368,height=77,borderwidth=0,bg="white")
        self.bottom_frame.place(x=1,y=1)
        self.bottom_frame.pack_propagate(False)

        self.group_create_image = tk.PhotoImage(file="group_create.png")
        self.group_focus_create_image = tk.PhotoImage(file="group_focus_create.png")
        self.group_cancel_image = tk.PhotoImage(file="group_cancel.png")

        self.group_create=tk.Label(self.bottom_frame,borderwidth=0, image=self.group_create_image)
        self.group_create.place(x=180, y=19)
        self.group_create.bind("<Button-1>", self.create_group)

        self.group_cancel = tk.Label(self.bottom_frame,borderwidth=0, image=self.group_cancel_image)
        self.group_cancel.place(x=268,y=19)
        self.group_cancel.bind("<Button-1>",self.cancel)

        self.friend_checks = {}
        self.checked_status = {friend[0]: False for friend in friend_info}
        self.common_image=tk.PhotoImage(file="group_common_image.png")

        self.scroll_area = tk.Canvas(self.friend_list_frame, borderwidth=0, bg="white", highlightthickness=0)

        # 스크롤바
        self.scrollbar = tk.Scrollbar(self.friend_list_frame, command=self.scroll_area.yview, borderwidth=0)
        self.scroll_area.configure(yscrollcommand=self.scrollbar.set, scrollregion=self.scroll_area.bbox("all"))

        self.scrollbar.pack(side="right", fill="y")

        self.scroll_area.pack(side="left", fill="both", expand=True)

        # 채팅목록창

        self.inner_frame = tk.Frame(self.scroll_area, borderwidth=0,bg="white")  # , borderwidth=2, relief="solid"

        self.scroll_area_window = self.scroll_area.create_window(0, 0, window=self.inner_frame, anchor="nw")

        self.inner_frame.bind("<Configure>", self.onFrameConfigure)
        self.scroll_area.bind("<Configure>", self.onCanvasConfigure)
        self.inner_frame.bind('<Enter>', self.onEnter)  # bind wheel events when the cursor enters the control
        self.inner_frame.bind('<Leave>', self.onLeave)

        self.friend_list_count_frame=tk.Frame(self.inner_frame, borderwidth=0,bg="white",height=33)
        self.friend_list_count_frame.pack(side="top", fill="x")
        self.friend_list_count_frame.pack_propagate()

        self.friend_text_image = tk.PhotoImage(file="group_talk_friend.png")
        self.friend_text=tk.Label(self.friend_list_count_frame, borderwidth=0,bg="white",image=self.friend_text_image)
        self.friend_text.place(x=21,y=5)
        self.check_image = tk.PhotoImage(file="check_friend.png")
        self.check_on_image = tk.PhotoImage(file="check_on.png")
        self.fill_friend_list()
        #친구 숫자세서 넣어줄 숫자필요 180 19

    def cancel(self,event):
        global group_talk_windows
        group_talk_windows = False
        self.window.destroy()
    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def stop_move(self, event):
        self.x = None
        self.y = None

    def on_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.window.winfo_x() + deltax
        y = self.window.winfo_y() + deltay
        self.window.geometry(f"+{x}+{y}")

    def close_window(self,event):
        global group_talk_windows
        group_talk_windows=False
        self.window.destroy()
    def onFrameConfigure(self, event):
        '''Reset the scroll region to encompass the inner frame'''
        self.scroll_area.configure(scrollregion=self.scroll_area.bbox(
            "all"))
    def onCanvasConfigure(self, event):
        '''Reset the canvas window to encompass inner frame when required'''
        canvas_width = event.width
        self.scroll_area.itemconfig(self.scroll_area_window,
                               width=canvas_width)
    def onMouseWheel(self, event):  # cross platform scroll wheel event
        if platform.system() == 'Windows':
            self.scroll_area.yview_scroll(int(-1 * (event.delta / 120)), "units")
        elif platform.system() == 'Darwin':
            self.scroll_area.yview_scroll(int(-1 * event.delta), "units")
        else:
            if event.num == 4:
                self.scroll_area.yview_scroll(-1, "units")
            elif event.num == 5:
                self.scroll_area.yview_scroll(1, "units")

    def onEnter(self, event):  # bind wheel events when the cursor enters the control
        if platform.system() == 'Linux':
            self.scroll_area.bind_all("<Button-4>", self.onMouseWheel)
            self.scroll_area.bind_all("<Button-5>", self.onMouseWheel)
        else:
            self.scroll_area.bind_all("<MouseWheel>", self.onMouseWheel)

    def onLeave(self, event):  # unbind wheel events when the cursorl leaves the control
        if platform.system() == 'Linux':
            self.scroll_area.unbind_all("<Button-4>")
            self.scroll_area.unbind_all("<Button-5>")
        else:
            self.scroll_area.unbind_all("<MouseWheel>")
    def run(self):
        self.window.mainloop()

    def fill_friend_list(self):
        for friend in self.filtered_friends:
            friend_row=tk.Frame(self.inner_frame,borderwidth=0,width=354,height=56,bg="white")
            friend_row.pack(side="top")
            friend_row.pack_propagate(False)
            friend_row.bind("<Button-1>",self.check_friend)
            print(friend)
            friend_picture=tk.Label(friend_row,borderwidth=0,bg="white")
            friend_picture.place(x=20,y=10)
            if friend[2]==b'-':
                friend_picture.config(image=self.common_image)
            else:
                image_stream = io.BytesIO(friend[2])
                pil_image = Image.open(image_stream)
                resized_image = pil_image.resize((40, 40))
                photo = ImageTk.PhotoImage(resized_image)
                friend_picture.image=photo
                friend_picture.config(image=photo)

            friend_name=tk.Label(friend_row,borderwidth=0,text=friend[0],bg="white")
            friend_name.place(x=73,y=23)
            #324 9

            check=tk.Label(friend_row,borderwidth=0,image=self.check_image if not self.checked_status[friend[0]] else self.check_on_image,bg="white")
            check.place(x=324,y=19)

            self.friend_checks[friend[0]] = check
            self.checked_status[friend_row] = False

    def filter_friends(self, event):
        search_query = self.search_entry.get()
        self.filtered_friends = []
        for friend in self.friend_info:
            if search_query in friend[0]:
                self.filtered_friends.append(friend)
        # self.filtered_friends = [friend for friend in self.friend_info if search_query in friend[0]]
        self.refresh_friend_list()

    def refresh_friend_list(self):
        # 이전에 생성된 위젯들을 지우고 새로운 목록으로 다시 생성
        for widget in self.inner_frame.winfo_children():
            widget.destroy()
        self.fill_friend_list()

    def update_create_button_image(self):
        if any(self.checked_status.values()):  # 체크된 항목이 하나라도 있는지 검사
            self.group_create.config(image=self.group_focus_create_image)
        else:
            self.group_create.config(image=self.group_create_image)
    def check_friend(self,event):
        friend_name = event.widget.winfo_children()[1].cget("text")
        is_checked = self.checked_status[friend_name]

        if is_checked:
            self.friend_checks[friend_name].config(image=self.check_image)
            self.checked_status[friend_name] = False
        else:
            self.friend_checks[friend_name].config(image=self.check_on_image)
            self.checked_status[friend_name] = True
        self.update_create_button_image()

    def create_group(self, event):
        # 체크된 친구들을 선택
        selected_friends = [friend for friend in self.friend_info if self.checked_status[friend[0]]]
        global group_talk_windows
        group_talk_windows = False
        # 체크된 친구가 2명 이상일 때만 룸키 생성
        if len(selected_friends) >= 2:
            # 자신의 정보 추가
            selected_friends.append(self.my_info)
            # 전체 리스트를 특정 필드로 정렬
            selected_friends.sort(key=lambda friend: friend[3])

            # 룸키 초기화
            room_key = "G"
            # 정렬된 리스트에서 각 친구의 폰 번호 마지막 부분을 사용하여 룸키 구성
            for friend in selected_friends:
                phone = friend[1]
                key = phone[8:]  # 폰 번호의 마지막 일부 추출
                room_key += key  # 룸키에 추가

            self.create_group_window(selected_friends,room_key,self.my_info)

        else:
            # 체크된 친구가 2명 미만일 경우 메시지 출력 또는 예외 처리
            return None


    def create_group_window(self,friend_info,room_id,my_info):
        self.window.destroy()
        sorted_ids = sorted(friend[3] for friend in friend_info)
        id = ", ".join(sorted_ids)
        chat = ["[group_chat]", room_id, [id]]

        abcz=pickle.dumps(chat)
        sock.send(abcz)
        bb = tk.Toplevel()
        cd = group_window(bb,friend_info,room_id,my_info)
        if room_id not in chat_windows:
            chat_windows[room_id]=cd
        cd.run()
class group_window:
    def __init__(self, main_window, friend_info,room_id,my_info):
        self.window = main_window
        self.my_info=my_info
        self.my_name=my_info[0]
        self.room_id=room_id
        self.friend_info = friend_info
        self.room_name = ""
        self.make_room_name()
        self.window.geometry("380x640+990+200")
        self.window.configure(bg="#B3B3B3")
        self.window.overrideredirect(True)

        self.top_frame=tk.Frame(self.window,borderwidth=0,relief="solid",width=378,height=89,bg="#BACEE0")
        self.top_frame.place(x=1,y=1)
        self.top_frame.pack_propagate(False)
        self.top_frame.bind("<Button-1>", self.start_move)  # 마우스 버튼 누름
        self.top_frame.bind("<ButtonRelease-1>", self.stop_move)  # 마우스 버튼 뗌
        self.top_frame.bind("<B1-Motion>", self.on_move)
        self.profile_picture = tk.PhotoImage(file="group_profile.png")

        # self.face_talk_image = tk.PhotoImage(file="face_talk_icon_no_focus.png",master=self.window)
        # self.face_talk = tk.Label(self.top_frame, image=self.face_talk_image, borderwidth=0)
        # self.face_talk.bind("<Button-1>",lambda event,friend=friend_info,my_info=self.my_info: self.run_face_talk(event,friend,my_info))
        # self.face_talk.place(x=310, y=43)

        self.friend_pic=tk.PhotoImage(master=self.window)
        self.friend_picture = tk.Label(self.top_frame, borderwidth=0,bg="#BACEE0",image=self.profile_picture)
        self.friend_picture.place(x=14,y=38)
        self.friend_name = tk.Label(self.top_frame,borderwidth=0,bg="#BACEE0",text=self.room_name)
        self.friend_name.place(x=66,y=42)
        #
        self.chat_count_pe_image=tk.PhotoImage(file="chat_count_pe.png",master=self.window)
        self.chat_count_pe=tk.Label(self.top_frame,image=self.chat_count_pe_image,borderwidth=0)
        self.chat_count_pe.place(x=66,y=64)
        #
        self.friend_count=tk.Label(self.top_frame,borderwidth=0,text=len(self.friend_info),bg="#BACEE0")
        self.friend_count.place(x=80,y=61)

        self.chat_close_image=tk.PhotoImage(file="chat_close.png",master=self.window)
        self.chat_close=tk.Label(self.top_frame,image=self.chat_close_image,borderwidth=0)
        self.chat_close.bind("<Button-1>",self.close_chat)
        self.chat_close.place(x=360,y=10)

        self.chat_frame=tk.Frame(self.window,borderwidth=0,width=378,height=426,bg="#BACEE0")
        self.chat_frame.place(x=1, y=90)
        self.chat_frame.pack_propagate(False)
        # 13,10
        self.scroll_area = tk.Canvas(self.chat_frame, borderwidth=0, bg="#BACEE0", highlightthickness=0)

        # 스크롤바
        self.scrollbar = tk.Scrollbar(self.chat_frame, command=self.scroll_area.yview, borderwidth=0)
        self.scroll_area.configure(yscrollcommand=self.scrollbar.set, scrollregion=self.scroll_area.bbox("all"))

        self.scrollbar.pack(side="right", fill="y")

        self.scroll_area.pack(side="left", fill="both", expand=True)

        self.inner_frame = tk.Frame(self.scroll_area,borderwidth=0 ,bg="#BACEE0")

        self.scroll_area_window = self.scroll_area.create_window(0, 0, window=self.inner_frame, anchor="nw")
        self.inner_frame.bind("<Configure>", self.onFrameConfigure)
        self.scroll_area.bind("<Configure>", self.onCanvasConfigure)
        self.inner_frame.bind('<Enter>', self.onEnter)  # bind wheel events when the cursor enters the control
        self.inner_frame.bind('<Leave>', self.onLeave)
        self.onFrameConfigure(
            None)


        self.send_frame=tk.Frame(self.window,borderwidth=0,relief="solid",width=378,height=123,bg="white")
        self.send_frame.place(x=1, y=516)
        self.send_entry=tk.Entry(self.send_frame,borderwidth=0,width=200,bg="white")
        self.send_entry.bind("<Return>",self.chat_send)
        self.send_entry.place(x=13,y=10)


        self.send_image=tk.PhotoImage(file="talk_send.png") #전송버튼
        self.send_button=tk.Label(self.send_frame,borderwidth=0,image=self.send_image)
        self.send_button.bind("<Button-1>",self.chat_send)
        self.send_button.place(x=316,y=85)


        self.common_image=tk.PhotoImage(file="common_image_chat.png")

        self.file_send_image=tk.PhotoImage(file="file_send.png") #파일전송
        self.file_send=tk.Label(self.send_frame,borderwidth=0,image=self.file_send_image)
        self.file_send.place(x=110,y=91)
        self.file_send.bind("<Button-1>",self.setup_file_send)
        self.send_frame.pack_propagate(False)
        self.file_open=False
        sock.send("[group_chat_fill],".encode() + self.room_id.encode())

    def make_room_name(self):
        name = ", ".join(friend[0] for friend in self.friend_info)
        self.room_name = name
    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def stop_move(self, event):
        self.x = None
        self.y = None

    def on_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.window.winfo_x() + deltax
        y = self.window.winfo_y() + deltay
        self.window.geometry(f"+{x}+{y}")

    def close_chat(self, event):
        del chat_windows[self.room_id]
        self.window.destroy()

    def run(self):
        self.window.mainloop()

    def onFrameConfigure(self, event):
        '''Reset the scroll region to encompass the inner frame'''
        self.scroll_area.configure(scrollregion=self.scroll_area.bbox(
            "all"))

    def onCanvasConfigure(self, event):
        '''Reset the canvas window to encompass inner frame when required'''
        canvas_width = event.width
        self.scroll_area.itemconfig(self.scroll_area_window,
                                    width=canvas_width)

    def onMouseWheel(self, event):  # cross platform scroll wheel event
        if platform.system() == 'Windows':
            self.scroll_area.yview_scroll(int(-1 * (event.delta / 120)), "units")
        elif platform.system() == 'Darwin':
            self.scroll_area.yview_scroll(int(-1 * event.delta), "units")
        else:
            if event.num == 4:
                self.scroll_area.yview_scroll(-1, "units")
            elif event.num == 5:
                self.scroll_area.yview_scroll(1, "units")

    def onEnter(self, event):  # bind wheel events when the cursor enters the control
        if platform.system() == 'Linux':
            self.scroll_area.bind_all("<Button-4>", self.onMouseWheel)
            self.scroll_area.bind_all("<Button-5>", self.onMouseWheel)
        else:
            self.scroll_area.bind_all("<MouseWheel>", self.onMouseWheel)

    def onLeave(self, event):  # unbind wheel events when the cursorl leaves the control
        if platform.system() == 'Linux':
            self.scroll_area.unbind_all("<Button-4>")
            self.scroll_area.unbind_all("<Button-5>")
        else:
            self.scroll_area.unbind_all("<MouseWheel>")

    def chat_send(self,event):
        if not self.send_entry.get()=="":
            sorted_ids = sorted(friend[3] for friend in self.friend_info)
            id = ", ".join(sorted_ids)
            chat=["[group_send]",self.room_id,[id],self.my_info[3],self.send_entry.get()]
            abc=pickle.dumps(chat)
            aaa="[room_list],"+self.room_id
            sock.send(abc)
            time.sleep(0.2)
            sock.send(aaa.encode())
            self.send_entry.delete(0, tkinter.END)

    def setup_file_send(self, event):
        if not self.file_open:  # 파일 선택 창이 이미 열려있지 않다면
            self.file_open = True  # 파일 선택 창 열림 상태로 설정
            self.send_picture(self.friend_info, self.my_info, self.room_id)
            self.file_open = False

    def send_picture(self, friend_info, my_info, room_id):
        filepath = filedialog.askopenfilename(
            title="Open File",
            filetypes=(("Image Files", "*.png;*.jpg;*.jpeg"),)
        )
        if filepath:
            with open(filepath, 'rb') as file:
                blob_data = file.read()
                picture = b"[st]" + blob_data + b"[end]"
                sorted_ids = sorted(friend[3] for friend in self.friend_info)
                id = ", ".join(sorted_ids)
                # chat = "[chat]," + room_id + ',' + friend_info[3] + ',' + my_info[3] + ','
                chat = ["[group_send]", self.room_id, [id], self.my_info[3], picture ]
                # aaa = "[room_list]," + room_id
                info=pickle.dumps(chat)
                sock.send(info)
                # time.sleep(0.2)
                # sock.send(aaa.encode())
    def insert_date_separator(self, date):
        weekdays = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일']
        weekday_index = date.weekday()
        korean_weekday = weekdays[weekday_index]
        date_str = date.strftime('%Y년 %m월 %d일 ') + korean_weekday

        canvas = tk.Canvas(self.inner_frame, height=50, bg="#BACEE0",highlightthickness=0)
        canvas.pack(fill="x", pady=10)

        self.weekday_box = tk.PhotoImage(file="weekday.png")
        canvas.create_image(180, 25, image=self.weekday_box)
        canvas.create_text(120, 25, text=date_str, anchor="w", fill="black")

        canvas.image = self.weekday_box

    def fill_group_chat(self,chat_list):
        aaa = "[room_list]," + self.room_id
        sock.send(aaa.encode())
        self.scroll_area.yview_moveto(1)
        last_date = None
        time_check = None
        check = 0
        try:
            if self.inner_frame.winfo_exists():
                for widget in self.inner_frame.winfo_children():
                    widget.destroy()
        except Exception as e:
            print(f"Error accessing the chat frame: {e}")
        for chat in chat_list:
            print(chat)
            chat_date = chat[2].date()
            if last_date != chat_date:
                self.insert_date_separator(chat_date)
                last_date = chat_date
            chat_data = chat[3]
            if chat[1]==self.my_info[3]: #내가 보낸 톡이면?
                self.chat_row=tk.Frame(self.inner_frame,bg="#BACEE0", width=368, height=30,
                                        borderwidth=0)
                self.chat_row.pack(side="top",anchor="ne", pady=3)
                self.chat_row.pack_propagate(False)
                self.adfff=tk.Frame(self.chat_row,bg="#BACEE0", width=10)
                self.adfff.pack(side="right",anchor="se")
                self.chat_info=tk.Frame(self.chat_row,bg="yellow",borderwidth=0)
                self.chat_info.pack(side="right",padx=1,anchor="se")
                detail_font = tk.font.Font(size=10)
                self.chat_detail=tk.Label(self.chat_info,borderwidth=0, wraplength=240,bg="yellow",justify='left',font=detail_font)
                self.chat_detail.pack(side="right", padx=2,pady=6)
                if b"[st]" in chat_data and b"[end]" in chat_data:
                    # 이미지 데이터 추출 및 처리
                    start_idx = chat_data.find(b"[st]") + len(b"[st]")
                    end_idx = chat_data.find(b"[end]")
                    image_data = chat_data[start_idx:end_idx]
                    image_stream = io.BytesIO(image_data)
                    pil_image = Image.open(image_stream)
                    photo = ImageTk.PhotoImage(pil_image)
                    self.chat_row.pack_propagate(True)
                    self.chat_detail.image = photo  # 참조 유지
                    self.chat_detail.config(image=photo)
                else:
                    self.chat_detail.config(text=chat_data.decode('utf-8'))

                display_time = chat[2].strftime('%p %I:%M').lstrip('0').replace(' 0', ' ')
                if "AM" in display_time:
                    display_time = display_time.replace("AM", "오전")
                else:
                    display_time = display_time.replace("PM", "오후")
                time_font=tk.font.Font(size=8)
                self.time_info=tk.Frame(self.chat_row,bg="#BACEE0",borderwidth=0)
                self.time_info.pack(side="right",anchor="se",padx=2)
                self.time=tk.Label(self.time_info,borderwidth=0,text=display_time,font=time_font,bg="#BACEE0")
                self.time.pack(side="right",anchor="sw")
                self.scroll_area.yview_moveto(1)
                check=1

            else: #친구가보낸거
                if check==0 and chat[2].strftime('%I:%M')==time_check:
                    self.scroll_area.yview_moveto(1)
                    self.chat_row = tk.Frame(self.inner_frame, background="#BACEE0", width=368, height=30,
                                             borderwidth=0)
                    self.chat_row.pack(side="top",anchor="nw", pady=3)
                    self.chat_row.pack_propagate(False)
                    self.adfff = tk.Frame(self.chat_row, bg="#BACEE0", width=50)
                    self.adfff.pack(side="left", anchor="sw")
                    self.chat_info = tk.Frame(self.chat_row, bg="white", borderwidth=0)
                    self.chat_info.pack(side="left", padx=1,anchor="sw")
                    detail_font = tk.font.Font(size=10)
                    self.chat_detail = tk.Label(self.chat_info, borderwidth=0, wraplength=240,
                                                bg="white", justify='left',font=detail_font)
                    self.chat_detail.pack(side="left", padx=2,pady=6)
                    if b"[st]" in chat_data and b"[end]" in chat_data:
                        # 이미지 데이터 추출 및 처리
                        start_idx = chat_data.find(b"[st]") + len(b"[st]")
                        end_idx = chat_data.find(b"[end]")
                        image_data = chat_data[start_idx:end_idx]
                        image_stream = io.BytesIO(image_data)
                        pil_image = Image.open(image_stream)
                        photo = ImageTk.PhotoImage(pil_image)
                        self.chat_row.pack_propagate(True)
                        self.chat_detail.image = photo  # 참조 유지
                        self.chat_detail.config(image=photo)
                    else:
                        self.chat_detail.config(text=chat_data.decode('utf-8'))
                    display_time = chat[2].strftime('%p %I:%M').lstrip('0').replace(' 0', ' ')
                    time_check = chat[2].strftime('%I:%M')
                    if "AM" in display_time:
                        display_time = display_time.replace("AM", "오전")
                    else:
                        display_time = display_time.replace("PM", "오후")
                    time_font = tk.font.Font(size=8)
                    self.time_info = tk.Frame(self.chat_row, bg="#BACEE0", borderwidth=0)
                    self.time_info.pack(side="left", anchor="sw", padx=2)
                    self.time = tk.Label(self.time_info, borderwidth=0, text=display_time,font=time_font,bg="#BACEE0")
                    self.time.pack(side="left",anchor="sw")
                    self.scroll_area.yview_moveto(1)
                    check = 0
                else:
                    self.scroll_area.yview_moveto(1)
                    self.chat_row = tk.Frame(self.inner_frame, background="#BACEE0", width=368, height=50,
                                             borderwidth=0)
                    self.chat_row.pack(side="top", anchor="nw", pady=3)
                    self.chat_row.pack_propagate(False)
                    self.adfff = tk.Frame(self.chat_row, bg="#BACEE0", width=10,borderwidth=2,relief="solid")
                    self.adfff.pack(side="left", anchor="sw")
                    self.friend_picc = tk.Label(self.chat_row,
                                                   borderwidth=0, bg="#BACEE0")
                    self.friend_picc.pack(side="left",anchor="nw",)
                    friend_names = [friend[0] for friend in self.friend_info if friend[3] == chat[1]]
                    # 이름 목록 길이가 4 이상인 경우 처리
                    if len(friend_names) > 3:
                        formatted_friend_names = ", ".join(friend_names[:3]) + ", ..."
                    else:
                        formatted_friend_names = ", ".join(friend_names)
                    friend_pictures = [friend[2] for friend in self.friend_info if friend[3] == chat[1]]
                    if friend_pictures[0] ==b'-':
                        self.friend_picc.config(image=self.common_image)
                    else:
                        image_stream = io.BytesIO(friend_pictures[0])
                        pil_image = Image.open(image_stream)
                        resized_image = pil_image.resize((40, 40))
                        photo = ImageTk.PhotoImage(resized_image)
                        self.friend_picc.image = photo  # 참조 유지
                        self.friend_picc.config(image=photo)

                    self.friend_nam = tk.Label(self.chat_row, text=formatted_friend_names, borderwidth=0, bg="#BACEE0")
                    self.friend_nam.pack(side="top", anchor="nw")
                    detail_font = tk.font.Font(size=10)
                    self.chat_box = tk.Frame(self.chat_row, borderwidth=0, bg="#BACEE0")
                    self.chat_box.pack(side="top", anchor="sw")
                    self.chat_detail = tk.Label(self.chat_box, borderwidth=0, wraplength=240,
                                                bg="white", justify='left', font=detail_font)
                    self.chat_detail.pack(side="left", padx=2, pady=6)
                    if b"[st]" in chat_data and b"[end]" in chat_data:
                        # 이미지 데이터 추출 및 처리
                        start_idx = chat_data.find(b"[st]") + len(b"[st]")
                        end_idx = chat_data.find(b"[end]")
                        image_data = chat_data[start_idx:end_idx]
                        image_stream = io.BytesIO(image_data)
                        pil_image = Image.open(image_stream)
                        photo = ImageTk.PhotoImage(pil_image)
                        self.chat_row.pack_propagate(True)
                        self.chat_detail.image = photo  # 참조 유지
                        self.chat_detail.config(image=photo)
                    else:
                        self.chat_detail.config(text=chat_data.decode('utf-8'))
                    display_time = chat[2].strftime('%p %I:%M').lstrip('0').replace(' 0', ' ')
                    time_check = chat[2].strftime('%I:%M')
                    if "AM" in display_time:
                        display_time = display_time.replace("AM", "오전")
                    else:
                        display_time = display_time.replace("PM", "오후")
                    time_font = tk.font.Font(size=8)
                    self.time_info = tk.Frame(self.chat_box, bg="#BACEE0", borderwidth=0)
                    self.time_info.pack(side="left", padx=2)
                    self.time = tk.Label(self.time_info, borderwidth=0, text=display_time, font=time_font, bg="#BACEE0")
                    self.time.pack(side="left")
                    check = 0
                    self.scroll_area.yview_moveto(1)
            self.scroll_area.yview_moveto(1)
class friend_profile_window: #친구 프로필
    def __init__(self, main_window, username, user_picture):
        self.user_name = username
        self.picture=user_picture
        self.main_window_friend_profile = main_window
        self.main_window_friend_profile.overrideredirect(True)
        self.main_window_friend_profile.geometry("300x600+810+200")
        self.main_window_friend_profile.configure(bg="#81888C") ####
        self.main_window_friend_profile.bind("<Button-1>", self.start_move)  # 마우스 버튼 누름
        self.main_window_friend_profile.bind("<ButtonRelease-1>", self.stop_move)  # 마우스 버튼 뗌
        self.main_window_friend_profile.bind("<B1-Motion>", self.on_move)

        self.canvas = tk.Canvas(self.main_window_friend_profile, bg="#81888C", bd=0, highlightthickness=0, relief='ridge')
        self.canvas.place(x=0, y=495, width=300, height=2)  # 가로선 위치 및 크기 설정
        self.canvas.create_line(0, 0, 300, 0, fill="white", width=1)  # 하양색 가로선 그리기

        image11 = Image.open("11111.png")
        self.photo_11 = ImageTk.PhotoImage(image11)
        image11chat = Image.open("11chat.png")
        image11chatre = image11chat.resize((44, 13), Image.LANCZOS)
        self.photo_11_chat = ImageTk.PhotoImage(image11chatre)

        image22 = Image.open("22222.png")
        self.photo_22 = ImageTk.PhotoImage(image22)
        image22voice = Image.open("22voice.png")
        image22voicere = image22voice.resize((44, 13), Image.LANCZOS)
        self.photo_22_voice = ImageTk.PhotoImage(image22voicere)

        image33 = Image.open("33333.png")
        self.photo_33 = ImageTk.PhotoImage(image33)
        image33face = Image.open("33face.png")
        image33facere = image33face.resize((44, 13), Image.LANCZOS)
        self.photo_33_face = ImageTk.PhotoImage(image33facere)

        image_bgimg = Image.open("bgimg.png")
        image_bgimgre = image_bgimg.resize((25, 25), Image.LANCZOS)
        self.photo_bgimg = ImageTk.PhotoImage(image_bgimgre)

        image_star = Image.open("star.png")
        image_starre = image_star.resize((25, 25), Image.LANCZOS)
        self.photo_star = ImageTk.PhotoImage(image_starre)

        image_present = Image.open("present.png")
        image_presentre = image_present.resize((25, 25), Image.LANCZOS)
        self.photo_present = ImageTk.PhotoImage(image_presentre)

        image_other = Image.open("other.png")
        image_otherre = image_other.resize((25, 25), Image.LANCZOS)
        self.photo_other = ImageTk.PhotoImage(image_otherre)

        image_X = Image.open("X.png")
        image_Xre = image_X.resize((10, 10), Image.LANCZOS)
        self.photo_X = ImageTk.PhotoImage(image_Xre)


        friend_profile_data = self.picture

        self.chat_label = tk.Label(main_window, image=self.photo_11, bd=0, bg="#81888C")
        self.chat_label.place(x=60, y=530)
        self.chat_label1 = tk.Label(main_window, image=self.photo_11_chat, bd=0, bg="#81888C")
        self.chat_label1.place(x=48, y=560)

        self.voice_label = tk.Label(main_window, image=self.photo_22, bd=0, bg="#81888C")
        self.voice_label.place(x=140, y=530)
        self.voice_label1 = tk.Label(main_window, image=self.photo_22_voice, bd=0, bg="#81888C")
        self.voice_label1.place(x=128, y=560)

        self.face_label = tk.Label(main_window, image=self.photo_33, bd=0, bg="#81888C")
        self.face_label.place(x=220, y=530)
        self.face_label1 = tk.Label(main_window, image=self.photo_33_face, bd=0, bg="#81888C")
        self.face_label1.place(x=210, y=560)

        self.profile_label = tk.Label(main_window, bd=0, bg="#81888C")
        self.profile_label.place(x=105, y=340)

        self.bgimg_label = tk.Label(main_window, image=self.photo_bgimg, bd=0, bg="#81888C")
        self.bgimg_label.place(x=11, y=11)

        self.star_label = tk.Label(main_window, image=self.photo_star, bd=0, bg="#81888C")
        self.star_label.place(x=44, y=11)

        self.present_label = tk.Label(main_window, image=self.photo_present, bd=0, bg="#81888C")
        self.present_label.place(x=76, y=11)

        self.other_label = tk.Label(main_window, image=self.photo_other, bd=0, bg="#81888C")
        self.other_label.place(x=108, y=11)

        name_font = font.Font(family="맑은 고딕", size=12)
        message_font = font.Font(family="맑은 고딕", size=10)
        self.name_label = tk.Label(main_window, text=self.user_name, font=name_font, bg="#81888C", fg="white", borderwidth=0)  # 이름 라벨
        self.name_label.place(x=125, y=433)
        self.message_label = tk.Label(main_window, text="상태 메세지", font=message_font, fg="white", bg='#81888C',highlightthickness=0)  # 이름 라벨
        self.message_label.place(x=110, y=460)

        self.X_label = tk.Label(main_window, image=self.photo_X, bd=0, bg='#81888C')
        self.X_label.bind("<Button-1>", self.close_profile)
        self.X_label.place(x=280, y=9)


        self.set_profile_picture(self.picture)

        for widget in self.main_window_friend_profile.winfo_children():
            if widget != self.X_label:
                widget.bind("<Button-1>", lambda event: "break")
                widget.bind("<ButtonRelease-1>", lambda event: "break")
                widget.bind("<B1-Motion>", lambda event: "break")


    def start_move(self, event):
        if event.widget == self.main_window_friend_profile.winfo_children():
            return
        self.x = event.x
        self.y = event.y

    def stop_move(self, event):
        self.x = None
        self.y = None

    def on_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.main_window_friend_profile.winfo_x() + deltax
        y = self.main_window_friend_profile.winfo_y() + deltay
        self.main_window_friend_profile.geometry(f"+{x}+{y}")

    def close_profile(self,event):
        del friend_profile_windows[self.user_name]
        self.main_window_friend_profile.destroy()

    def run(self):
        self.main_window_friend_profile.configure(bg="#81888C")
        self.main_window_friend_profile.resizable(False, False)
        self.main_window_friend_profile.mainloop()


    def round_corners(self,im, rad):
        circle = Image.new('L', (rad * 2, rad * 2), 0)
        draw = ImageDraw.Draw(circle)
        draw.ellipse((0, 0, rad * 2, rad * 2), fill=255)
        alpha = Image.new('L', im.size, 255)
        w, h = im.size
        alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
        alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
        alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
        alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))
        im.putalpha(alpha)
        return im

    def profile_picture_update(self, picture):
        if picture == b'-':
            return tk.PhotoImage(file="comm.png")
        else:
            image_data = io.BytesIO(picture)
            image = Image.open(image_data)
            resized_image = image.resize((86, 86))
            rounded_image = self.round_corners(resized_image, 20)
            photo_image = ImageTk.PhotoImage(rounded_image)
            return photo_image


    def set_profile_picture(self, picture):
        photo_image = self.profile_picture_update(picture)
        self.profile_label.image = photo_image
        self.profile_label.config(image=photo_image)

        self.profile_label.update()
        self.main_window_friend_profile.update()
if __name__ == "__main__":
    root = tk.Tk()
    app = login(root)
    runChat()
    root.mainloop()

