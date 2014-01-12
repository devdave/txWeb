import time

import zmq
from txzmq import ZmqEndpoint, ZmqFactory, ZmqPushConnection, ZmqPullConnection
from psutil 

class PSMonitor(object):

    def __init__(self, port = 6767, addr = '0.0.0.0'):
        """
            :param port:
            :param addr: Port & Addr for ZMQ push type socket service
        """
        self.zf = ZmqFactory()
        self.port = port
        self.addr = addr
        self.zep = ZmqEndpoint("bind", "tcp://{}:{}" % (port, addr))

        self.zcon = ZmqPushConnection(self.zf, self.zep)
        
        
    def serialize_psstats():
        

    def step(*args, **kwargs):
        print args, kwargs, time.time()