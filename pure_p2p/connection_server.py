from socket import *
import threading

class ConnectionThread:
    def __init__(self, new_peer_socket):
        self.thread = threading.Thread(target=self.connectPeer, args=(new_peer_socket,))
        self.thread.start()
        pass
    
    def connectPeer(self, new_peer_socket):
        global peer_lock
        try:
            msg = new_peer_socket.recv(1024).decode()
            if msg[0:2] != 'FP':
                print('failed fp')
                new_peer_socket.close()
            
            else:
                peer_lock.acquire()
                global peers
                new_peer = msg[3:]
                check = not new_peer in peers

                if check:
                    msg = self.addPeer(msg[3:])
                    new_peer_socket.send(msg.encode())
                    new_peer_socket.close()
                
                else:
                    msg = 'pass'
                    new_peer_socket.send(msg.encode())
                    new_peer_socket.close()
                
                peer_lock.release()

                while len(peers) < 2:
                     pass

        except:
            print('error')
            new_peer_socket.close()
        self.stopThread()
        return None
    
    def addPeer(self, new_peer):
        global peers
        peers.append(new_peer)
        msg = ''
        for peer in peers:
            msg += peer + '&'
        return msg + 'AP'
    
    # FIX THIS TRHEAD STOPPING THING
    def stopThread(self):
        if self.thread.is_alive():
            try:
                self.thread.join()
            except:
                # print('well theres this issue with the threads being unable to join the main thread but im choosing to ignore it for now.')
                pass
        return None

connection_port = 10001
server_addr = '0.0.0.0'

peers = []
peer_lock = threading.Lock()

welcomeSocket = socket(AF_INET,SOCK_STREAM)

welcomeSocket.bind((server_addr, connection_port))
welcomeSocket.listen(1)

print(f'connection server is running at {server_addr}')

try: 
    while True:
        new_peer, addr = welcomeSocket.accept()
        print('Received a connection from: ', addr)
        peer_thread = ConnectionThread(new_peer_socket=new_peer)

except KeyboardInterrupt:
	print('bye...')

finally:
	welcomeSocket.close()