'''
Description: xmlrpc server module for executing commands, trasffer file between 
    server and clients

Author: tutong@taobao.com

Date: Sun, 07 Jul 2013
'''

import socket, signal
from SimpleXMLRPCServer import *
import os
import subprocess
import shlex

__all__=['AgentServer', 'main']

def execmd(cmd):
    r'''Execute cmd and return the stdout value back
    This function ignore the cmd checking. If you want to
    us some dangerous command such as rm, mv, please check
    it before using
    '''
    args = shlex.split(cmd)
    try:
        proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        retV = proc.communicate()[0]
    except:
        return "Something wrong when executing commads [%s]" % cmd
    else:
        return repr(retV)

def saveToAgent(content, path):
    r'''
    save client's file to agent's certain path
    @content - file content that should be saved
    @path - full path that the file placed
    '''
    handle = open(path, 'wb')
    try:
        handle.write(content.data)
    except:
        return False
    finally:
        handle.close()
    return True

def cpFromAgent(path):
    r'''
    copy a file placed in agent to client
    @path - full path that the target file placed
    '''
    if not os.path.exists(path):
        return 'Path not exists'
    content = None
    handle = open(path, 'rb')
    try:
        content = xmlrpclib.Binary(handle.read())
    finally:
        handle.close()
    return content
        
class AgentServer(SimpleXMLRPCServer):
    '''xmlrpc server inherited SimpleXMLRPCServer.
     It provides a shutdown method for close the 
     agent remotely.
    '''
    finished=False

    def register_signal(self, signum):
        signal.signal(signum, self.signal_handler)

    def signal_handler(self, signum, frame):
        print "Caught signal", signum
        self.shutdown()

    def shutdown(self):
        self.finished=True
        return 1

    def serve_forever(self):
        self.logRequests = False
        while not self.finished:
            self.handle_request()

def main(hostname, port=80):
    '''
    main fuction for staring xmlrpc server agent
    '''
    server = AgentServer((hostname, port))
    server.register_function(server.shutdown)
    server.register_function(execmd)
    server.register_function(cpFromAgent)
    server.register_function(saveToAgent)
    server.register_introspection_functions()
    server.register_signal(signal.SIGHUP)
    server.register_signal(signal.SIGINT)
    server.serve_forever()

if __name__ =="__main__":
    import socket
    main(socket.gethostbyname(socket.getfqdn()), 8192)
