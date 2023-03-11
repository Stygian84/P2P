from socket import *
import threading
import time


class PeerConnection:
    def __init__(self, own_addr):
        self.own_addr = own_addr
        self.peer_connection_socket = None
        self.msg = str()
        self.sendEvent = threading.Event()

    def setConnection(self, peer_addr):
        if isinstance(peer_addr, str):
            self.peer_connection_socket = socket(AF_INET,SOCK_STREAM) # this will be the socket that is used to communicate with the peer from now on
            self.peer_connection_socket.connect((peer_addr, 20000))
            self.peer_connection_socket.send(own_addr.encode())
        else:
            self.peer_connection_socket = peer_addr

    def startConnection(self):
        message_thread = threading.Thread(target=self.sendMsg)
        message_thread.start()
        receive_thread = threading.Thread(target=self.recvMsg)
        receive_thread.start()
    
    def recvMsg(self):
        while True:
            received = self.peer_connection_socket.recv(1024).decode()
            print(received)

    def sendMsg(self):
        while True:
            self.sendEvent.wait()
            self.peer_connection_socket.send(self.msg.encode())
            self.sendEvent.clear()

    def message(self, message):
        self.msg = message
        self.sendEvent.set()

    def getSocket(self):
        return self.peer_connection_socket


class PeerThread:
    def __init__(self, own_addr, peer_addr):
        self.peer_connection = PeerConnection(own_addr)
        self.peer_thread = threading.Thread(target=self.startPeerThread, args=(peer_addr,))
        self.peer_thread.start()

    def startPeerThread(self, peer_addr):
        self.peer_connection.setConnection(peer_addr)
        time.sleep(1)
        self.peer_connection.startConnection()

    def message(self, message):
        self.peer_connection.message(message)

    def stopThread(self):
        if self.thread.is_alive():
            try:
                self.peer_connection.getSocket().close()
                self.thread.join()
            except:
                # print('well theres this issue with the threads being unable to join the main thread but im choosing to ignore it for now.')
                pass
        return None

class Peer:
    def __init__(self, addr):
        self.addr = addr
        self.peers = []
        self.peer_connections = dict()
        self.welcome_socket = socket(AF_INET,SOCK_STREAM)
        not_valid_addr = True
        while not_valid_addr:
            try:
                self.welcome_socket.bind((self.addr, 20000))
                not_valid_addr = False
            except:
                print('The address given is not valid (may already be in use)')
                self.addr = input('Enter a new address: ')
        self.findPeers()
        self.connectPeers()
        listener = threading.Thread(target=self.listenPeers, daemon=True)
        listener.start()

    def message(self):
        print('starting messaging... showing available peers:')
        self.showPeers()
        while True:
            addressee = None
            while True:
                try:
                    addressee = input("Enter addressee: ")
                    peer_thread = self.peer_connections[addressee]
                    break
                except:
                    print('addressee not found. try again')
            print('patched through...')
            msg = input('Enter message: ')
            peer_thread.message(msg)


    def findPeers(self):
        connection_socket = socket(AF_INET,SOCK_STREAM)
        connection_socket.connect(('localhost', 10001))
        msg = 'FP:'+str(self.addr)
        connection_socket.send(msg.encode())
        
        while True:
            try:
                res = connection_socket.recv(1024).decode()
                res = res.split('&')
                if res[-1] == "AP":
                    res.remove(self.addr)
                    for new_peer in res[:-1]:
                        self.peers.append(new_peer)
                    break

                elif res[-1] == "pass":
                    break

            except:
                pass
        connection_socket.close()
        return None
    
    def showPeers(self):
        print(self.peers)

    def connectPeers(self):
        for peer_addr in self.peers:
            if not peer_addr in self.peer_connections:
                peer_socket_thread = PeerThread(own_addr=self.addr, peer_addr=peer_addr)
                self.peer_connections[peer_addr] = peer_socket_thread
    
    def listenPeers(self):
        self.welcome_socket.listen(1)
        while True:
            received_peer, received_addr = self.welcome_socket.accept()
            recv_addr = received_peer.recv(1024).decode()
            peer_socket_thread = PeerThread(own_addr=self.addr, peer_addr=received_peer)
            self.peer_connections[recv_addr] = peer_socket_thread
        pass

# addr = ['127.0.0.10', '127.0.0.11', '127.0.0.12', '127.0.0.13', '127.0.0.14']
# for i in addr:
#     new_peer = Peer(i)
#     new_peer.showPeers()
#     # new_peer.connectPeers()
#     time.sleep(1)

own_addr = input('Enter new address: ')
new_peer = Peer(own_addr)
new_peer.message()