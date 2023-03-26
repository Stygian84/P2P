import threading
import sys
import time
from random import randint
from socket import *
import pickle

# x11: I'm the connection server, sending you the new sp the list of all sp_ips
# x12: I'm a superpeer going to close now, remove from your sp_ip list

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

        while True:
            input_lock.acquire()
            inputt = input('Enter new address: ')
            input_lock.release()
            if inputt == 'exit':
                for c in self.sp_connections:
                    print('please delete me: ', self.ip)
                    c.send(b'\x12' + bytes(self.ip, "utf-8"))
                sys.exit()
            else:
                self.ip = inputt
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
                elif msg == "myip":
                    print(self.ip)
                    continue
            except Exception as e:
                print(e)
            data = bytes(msg, "utf-8")
            for connection in self.sp_connections:
                connection.send(data)
            for connection in self.p_connections:
                connection.send(data)

    def connectionHandler(self, sock):
        print('connectionHandler for ', self.ip)
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
                    c.send(b'\x11' + pickle.dumps(self.sp_ips))
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
                return 
            try:
                data = c.recv(1024)
            except Exception as e:
                print('rcvMsgHandler', e)
                break
            if data[0:1] == b'\x11' and self.ip != '127.0.0.1':
                sp_ips = pickle.loads(data[1:])
                union = self.sp_ips + sp_ips
                union = list(set(union)) # removes duplicates
                union.remove(self.ip)
                self.sp_ips = sorted(union)
                # make connections to all non cs sps
                for ip in self.sp_ips[1:]:
                    s = socket(AF_INET, SOCK_STREAM)
                    s.bind((self.ip, 0))
                    try:
                        print(self.ip , 'attempting to connect to ', ip)
                        s.connect((ip, 60000))
                        threading.Thread(daemon=True, target=self.rcvMsgHandler, args=(s, )).start()
                        self.sp_connections.append(s)
                    except Exception as e:
                        print('connecting sps', e)

            elif data[0:1] == b'\x12':
                ip_to_remove = data[1:].decode()
                self.sp_ips.remove(ip_to_remove)
                for c in self.sp_connections:
                    print(c.getpeername(), ip_to_remove)
                    if c.getpeername()[0] == ip_to_remove:
                        self.sp_connections.remove(c)
            
            elif data and data[0:1] != b'\x11' and data[0:1] != b'\x12':
                # time.sleep(2)
                print(str(data, "utf-8"))

# while True:
#     try: 
#         sp = Superpeer()
#     except Exception as e:
#             print(e)

try: 
    sp = Superpeer()
except Exception as e:
        print(e)
