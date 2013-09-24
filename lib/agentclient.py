'''
Description: helper module for xmlrpc agent client. using the methods
    can execute command and get the results remotely.

Author: tutong@taobao.com

Date: Sun, 07 Jul 2013
'''
import xmlrpclib
import logging

class AgentClient(object):
    def __init__(self, url):
        self.proxy = xmlrpclib.ServerProxy(url)
        self._usableMethods()
        logging.info('Server: ' + url)

    def _usableMethods(self):
        '''
        List Usable remote functions
        if no server agent on, return None
        when calling a remote function, call this
        function first
        '''
        try:
            self.methods =  self.proxy.system.listMethods()
        except:
            self.methods = None

    def hasMethod(self, m):
        '''query a method is usable or not'''
        if not self.methods:
            return False
        if m in self.methods:
            return True
        else:
            return Flase
        
    def cpFromAgent(self, file_from, file_to):
        '''copy a file from remote
        file_from: file path at remote
        file_to: destination path
        '''
        if not self.hasMethod('cpFromAgent'):
            return False
        handle = open(file_to, 'wb')
        try:
            handle.write(self.proxy.cpFromAgent(file_from).data)
        except:
            return False
        finally:
            handle.close()
        return True
        
    def saveToAgent(self, file_from, file_to):
        '''copy a file to remote
        file_from: local file path 
        file_to: destination path at remote
        '''
        if not self.hasMethod('saveToAgent'):
            return False
        else:
            bin_data = None
            with open(file_from, 'rb') as handle:
                bin_data = xmlrpclib.Binary(handle.read())
            self.proxy.saveToAgent(bin_data, file_to)
            
    def execmd(self, cmd):
        '''excuting commands at remote and get result
        In this function, all commands could be excuted.
        Please ensure the commands will not causing disastrous results
        at remote.
        '''
        logging.info('CMD: ' + cmd)
        if not self.hasMethod('execmd'):
            logging.error('agentclient has no execmd method')
            return False
        else:
            rt = eval(self.proxy.execmd(cmd))
            logging.info('RESULT: ' + rt)
            return rt

        
def closeServerAgent(obj):
    if not obj.hasMethod('shutdown'):
         return False
    if isinstance(obj, AgentClient):
        obj.proxy.shutdown()
        return True
    else:
        return False

def main_test():
    import socket
    s = AgentClient('http://10.235.160.66:8192')
    cmd = 'ls -al'
    a = s.execmd(cmd)
    print a
    closeServerAgent(s)

if __name__ == "__main__":
    main_test()
