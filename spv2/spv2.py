import threading
import sys
import time
from random import randint
from socket import *
import pickle

# x11: I'm the connection server, sending you the new sp the list of all sp_ips
# x12: I'm the connection server sending you a new ip

input_lock = threading.Lock()

class Superpeer:
    sp_ips = [] # all other superpeer ip addresses
    p_ips = [] # children ip addresses
    ip = '' # superpeers own ip
    sp_connections = [] # socket object of connected superpeers
    p_connections = [] # socket object of connected peers

    def __init__(self):
        sock = socket(AF_INET, SOCK_STREAM) # listening socket
        connecting_sock = socket(AF_INET, SOCK_STREAM)
        input_lock.acquire()
        self.ip = input('Enter new address: ')
        input_lock.release()
        if self.ip == 'exit':
            sys.exit()
        try:
            sock.bind((self.ip, 60000))
            connecting_sock.bind((self.ip, 60001))
            print(f'listening socket binded at {self.ip}, port 60000')
            print(f'connecting socket binded at {self.ip}, port 60001')
        except Exception as e:
            print('bind error: ', e)
        print('sockname: ', sock.getsockname())
        sock.listen(1)

        # connect to connection_server (preset 127.0.0.1)
        if self.ip != '127.0.0.1':
            try:
                connecting_sock.connect(("127.0.0.1", 60000))
                self.sp_ips.append("127.0.0.1")
                self.sp_connections.append(connecting_sock)
                print(connecting_sock.getsockname())
                print(f'connecting socket succesfully binded to connection server \n')
                threading.Thread(daemon=True, target=self.rcvMsgHandler, args=(connecting_sock, )).start()

            except Exception as e:
                print('establish contact exception: ', e)

        threading.Thread(daemon=True, target=self.sendMsg,).start()
        threading.Thread(daemon=True, target=self.connectionHandler, args=(sock, )).start()
        
    def sendMsg(self):
        input_lock.acquire()
        while True:
            try:
                msg = input("")
                if msg == "exit":
                    print('exiting sendMsg thread...')
                    input_lock.release()
                    sys.exit()
                elif msg == "print ips":
                    print(self.sp_ips)
                    continue
                elif msg == "print connections":
                    print(len(self.sp_connections))
                    continue
            except Exception as e:
                print(e)
            data = bytes(msg, "utf-8")
            for connection in self.sp_connections:
                connection.send(data)
            for connection in self.p_connections:
                connection.send(data)

    def connectionHandler(self, sock):
        print('connectionHandler')
        print(self.ip)
        # if ip == '127.0.0.1':
        while True:
            try:
                # c - connection, a - ip address
                c, addr = sock.accept()  # blocking method
                print(f"incoming address: {addr}\n")
                incoming_ip = addr[0]
                incoming_portnumber = addr[1]
                if self.ip == '127.0.0.1' and incoming_portnumber == 60001 and incoming_ip not in self.sp_ips:
                    print(f'incoming connection from {incoming_ip}\n')
                    self.sp_connections.append(c)
                    self.sp_ips.append(addr[0])
                    threading.Thread(daemon=True, target=self.rcvMsgHandler, args=(c, )).start()
                    # send the new sp self.sp_ips
                    print('sending x11, ', self.sp_ips)
                    c.send(b'\x11' + pickle.dumps(self.sp_ips))
                    # update connected sps with new addr
                    print('BROADCASTING')
                    for connection in self.sp_connections:
                        connection.send(b'\x12'+bytes(addr[0], 'utf-8'))
                elif self.ip != '127.0.0.1' and incoming_ip not in self.sp_ips:
                    print(f'incoming connection from {incoming_ip}\n')
                    self.sp_connections.append(c)
                    self.sp_ips.append(addr[0])
                    threading.Thread(daemon=True, target=self.rcvMsgHandler, args=(c, )).start()
                    
            except Exception as e:
                print('connectionHandler exception: ', e)
        # else: # non connection_server superpeers
                    
    def rcvMsgHandler(self, c):
        while True:
            data = bytes([])
            if not isinstance(c, socket):
                print('not isinstance')
                return 
            try:
                data = c.recv(1024)
            except Exception as e:
                print('rcvMsgHandler', e)
                break
            if data[0:1] == b'\x11' and self.ip != '127.0.0.1':
                sp_ips = pickle.loads(data[1:])
                print('x11 list: ', sp_ips)
                union = self.sp_ips + sp_ips
                union = list(set(union)) # removes duplicates
                union.remove(self.ip)
                self.sp_ips = sorted(union)
            if data[0:1] == b'\x12' and self.ip != '127.0.0.1':
                ip = data[1:].decode()
                print("x12: ", ip)
                if ip not in self.sp_ips and ip != self.ip:
                    self.sp_ips.append(ip)
                    sock = socket(AF_INET, SOCK_STREAM)
                    try:
                        sock.connect((ip, 60000))
                        threading.Thread(daemon=True, target=self.rcvMsgHandler, args=(sock, )).start()
                    except Exception as e:
                        print('connecting sps', e)
                    self.sp_connections.append(sock)
            elif data and data[0:1] != b'\x11' and data[0:1] != b'\x12':
                # time.sleep(2)
                print(str(data, "utf-8"))

while True:
    try: 
        sp = Superpeer()
    except Exception as e:
            print(e)

