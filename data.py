import socket
from threading import Lock, Thread
import json
from time import sleep
from uuid import uuid4
from datetime import timezone
from datetime import datetime
from collections import OrderedDict
from operator import getitem
from copy import deepcopy


class Data:
    def __init__(self, file_name, author_name) -> None:
        # file_name is json file given by user to save all the information
        self.file_name = file_name
        self.author_name = author_name
        self.stop_threads = False  # a variable to stop threads

        self.ports = []  # will contain ports of our network
        self.messages = {}  # will contain all the messages
        self.disconnected_peers = []  # will contain all the peers which are disconnected

        """
        Locks are used in this project to avoid the RACE conditions
        Decrease the number of critical sections, to decrease the problem between acquiring and releasing locks.
        Like there are functions for both reading and writing, so don't have to increase critical section.
        """
        self.file_lock = Lock()  # lock for reading/writing of file
        self.data_lock = Lock()  # lock for shared variables between threads

        self.read_json()
        self.start_threads()

    # Function to get UTC timestamp
    def get_utc(self):
        dt = datetime.now(timezone.utc)
        utc_time = dt.replace(tzinfo=timezone.utc)
        utc_timestamp = utc_time.timestamp()
        return int(utc_timestamp)

    # Function to read json file for ports and messages
    def read_json(self):
        self.file_lock.acquire()

        # checking exception for no file or empty file
        try:
            f = open(self.file_name)
            data = json.load(f)

            self.ports = data["ports"]
            self.messages = data["messages"]

            f.close()
        except:
            f = open(self.file_name, "w+")
            f.close()

        self.file_lock.release()

    # Function to write updated json data on file
    def write_json(self):

        # lock for file
        self.file_lock.acquire()

        file = open(self.file_name, "w+")

        # lock for data
        self.data_lock.acquire()

        new_data = {"ports": self.ports, "messages": self.messages}

        self.data_lock.release()

        # writing data on file
        file.seek(0)
        json.dump(new_data, file, indent=4)

        file.close()

        self.file_lock.release()

    # Function to start background threads
    def start_threads(self):
        t1 = Thread(target=self.get_data, args=(),
                    daemon=True)  # thread to act as client
        t2 = Thread(target=self.send_data, args=(),
                    daemon=True)  # thread to act as server

        t1.start()
        t2.start()

    # Setter function which help in stopping the threads
    def stop_all_threads(self):
        self.stop_threads = True

    # Function which will send data to peer on demand
    def send_data_thread(self, connection):
        try:
            self.data_lock.acquire()

            new_data = {"ports": self.ports, "messages": self.messages}
            self.data_lock.release()

            # converting to string form
            data = json.dumps(new_data)

            # send all is used to send big json data
            connection.sendall(data.encode())

            connection.close()
        except:
            pass

    # Function which act as server thread to listen request from peer who acting as client
    def send_data(self):
        temp_socket = socket.socket()
        temp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        """
        Port '0' is used to help user, so they don't have to play guessing game for port number
        """
        temp_socket.bind(('', 0))

        # printing port for user to remember
        self.port = temp_socket.getsockname()[1]
        print(f'\nYour port number is {self.port}\n')
        self.ports.append(self.port)

        temp_socket.listen(10)

        # always open to serve
        while True:
            client, address = temp_socket.accept()
            t1 = Thread(target=self.send_data_thread, args=(client, ))
            t1.start()

            # threads stop condition
            if self.stop_threads:
                break

    # Function which receive data from socket
    def receive_data(self, s):
        # loop is use so we can receive big json file
        BUFF_SIZE = 4096
        data = ''
        while True:
            part = s.recv(BUFF_SIZE).decode()
            data += part
            if len(part) == 0:
                break

        new_data = json.loads(data)

        self.data_lock.acquire()

        # adding ports without duplication
        self.ports = list(set(self.ports + new_data["ports"]))
        # adding messages
        self.messages.update(new_data["messages"])

        self.data_lock.release()

    # Function to get data from specific peer
    def get_data_peer(self, port):
        s = socket.socket()
        try:
            s.connect(('127.0.0.1', port))
        except:
            print(f'\n{port} is not available for connection !!!\n')
            return
        self.receive_data(s)
        self.write_json()
        s.close()

    # Function which act as client thread to get data from other peer who acting as server
    def get_data(self):
        while True:
            # thread stop condition
            if self.stop_threads:
                break

            # waiting 10 second before asking for updated data
            sleep(10)
            count = 0

            # will not work if there is no one in our network
            if len(self.ports) != 0:

                # deep copy, so updating ports will not affect the loop
                ports = self.ports[:]

                for port in ports:
                    s = socket.socket()

                    # exception if port is not available to connect
                    try:
                        s.connect(('127.0.0.1', port))
                    except:
                        self.disconnected_peers.append(port)
                        continue

                    count += 1
                    self.receive_data(s)
                    s.close()

                    # break after receiving data from first 5 active users
                    if count == 5:
                        break

                self.write_json()

    # Function which add message to our messages
    def add_message(self, data):
        new_data = {}
        new_data["author_name"] = self.author_name
        new_data["messages"] = data
        new_data["port"] = self.port
        new_data["date"] = self.get_utc()  # utc time stamp

        self.data_lock.acquire()
        # using uuid4 as key for each message
        self.messages[str(uuid4())] = new_data
        self.data_lock.release()

        self.write_json()

    # Function to print all the messages
    def print_messages(self):
        self.data_lock.acquire()
        if len(self.messages) == 0:
            print("\nThere is no message to print.\n")
        else:
            # sorting messages on the basis of date
            result = deepcopy(OrderedDict(
                sorted(self.messages.items(), key=lambda x: getitem(x[1], 'date'))))
            
            # printing sorted dict
            for id, message in result.items():
                result[id]["date"] = str(
                    datetime.fromtimestamp(result[id]["date"]))
                print(json.dumps(message, indent=4))
        self.data_lock.release()
