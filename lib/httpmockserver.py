'''
Description: This module is mock server for tesgting rfc2616 protocol conformance
    HTTPRequestHandlerMock: It is the handle class and handling actions of original server(OS).
        user must setting the response that the OS returned to client
   
    mock_HEAD/mock_GET: the real mock method for mocking HEAD and GET. In this fuction, you can
        rewrite it for your own mock logic

    UserDataHelper: Helper class for user setting request , response etc.

Author: tutong@taobao.com
Date: Sun, 06 Jul 2013
'''
from BaseHTTPServer import BaseHTTPRequestHandler
from BaseHTTPServer import HTTPServer
from SocketServer import ThreadingMixIn
import urlparse
import json
import random
import cgi
from urlparse import urlparse
import time

__all__ = ['HTTPRequestHandlerMock', 'mock_HEAD', 'mock_GET',
    'HTTPServerMock', 'ThreadedHTTPServerMock', 'UserDataHelper'] 

class HTTPRequestHandlerMock(BaseHTTPRequestHandler):
    '''Handle class for handling actions of original server receiving requests
    '''

    def log_message(self, format, *args):
        '''override it for not outputting message to stderr'''
        pass

    def send_response(self, code, message=None):
        '''override it for not appending server information
        and date information alway
        '''
        self.log_request(code)
        if message is None:
            if code in self.responses:
                message = self.responses[code][0]
        else:
            message = ''
        if self.request_version != 'HTTP/0.9':
            self.wfile.write("%s %d %s \r\n" % (self.protocol_version, code ,message))

    def _recordRequestHeaders(self):
        '''Get the request headers that the request forward from proxy'''
        del self.request_headers[:]
        self.request_headers.extend(self.headers.items())
        self.request_headers.append(('method', self.command))
        self.request_headers.append(('uri', self.path))
        self.request_headers.append(('protocol',self.request_version))
        
    def _countingURL(self):
        '''counting the url counts. When a url accepted by original server, 
        the count add 1
        key combine with Host and url path
        '''
        key = self.headers.get('Host', '') +  self.path
        if self.url_counts.has_key(key):
            self.url_counts[key] += 1
        else:
            self.url_counts[key] = 1

    def do_HEAD(self):
        self._recordRequestHeaders()
        self._countingURL()
        method = getattr(self, self.head_method_name)
        method()
        return
        
    def do_POST(self):
        self._recordRequestHeaders()
        if self.headers.getheader('Transfer-Encoding'):
            body = list()
            while True:
                temp = self.rfile.read(1)
                body.append(temp)
                if '0\r\n\r\n' == ''.join(body)[-5:]:
                    break
            self.request_headers.append(('body',''.join(body)))
        else:
            self.request_headers.append(('body',self.rfile.read(int(self.headers.getheader('content-length')))))
        self.send_response(self.user_defined_response, self.user_defined_resp_msg)
        has_date = False
        chunked = False
        del self.stepDate[:]
        for k, v in self.user_defined_headers:
            if k.lower() == 'transfer-encoding':
                chunked = True
    
            if k.lower() == 'date':
                if v.lower() == 'exclude':
                    has_date = True
                    self.stepDate.append(None)
                    continue
                elif v.strip().lower() == 'now':
                    continue
                has_date = True 
                self.stepDate.append(v)
            self.send_header(k, v)
        if not has_date:
            tmp = self.date_time_string(time.time())
            self.send_header('date', tmp)
            self.stepDate.append(tmp)
        self.end_headers()
        if chunked:
            chk_data = self.user_defined_body.rstrip('\r\n').split('\r\n')
            for i in range((len(chk_data) -1)/2):
                self.wfile.write(chk_data[2*i] + '\r\n' + chk_data[2*i+1]+'\r\n')
                self.wfile.flush()
                time.sleep(.1)
            self.wfile.write('0\r\n\r\n')
        else:
            self.wfile.write(self.user_defined_body)
        self.wfile.flush()    
        return

    def do_GET(self):
        self._recordRequestHeaders()
        self._countingURL()
        method = getattr(self, self.get_method_name)
        method()
        return

def mock_HEAD(self):
    '''for HEAD request logic'''
    self.send_response(self.user_defined_response, self.user_defined_resp_msg)
    has_date = False
    del self.stepDate[:]
    for k, v in self.user_defined_headers:
        if k.lower() == 'date':
            if v.lower() == 'exclude':
                has_date = True
                self.stepDate.append(None)
                continue
            elif v.strip().lower() == 'now':
                continue
            has_date = True 
            self.stepDate.append(v)
        self.send_header(k, v)
    if not has_date:
        tmp = self.date_time_string(time.time())
        self.send_header('date', tmp)
        self.stepDate.append(tmp)
    self.end_headers()
    self.wfile.flush()
    return

def mock_GET(self):
    self.send_response(self.user_defined_response, self.user_defined_resp_msg)
    has_date = False
    chunked = False
    del self.stepDate[:]
    for k, v in self.user_defined_headers:
        if k.lower() == 'transfer-encoding':
            chunked = True

        if k.lower() == 'date':
            if v.lower() == 'exclude':
                has_date = True
                self.stepDate.append(None)
                continue
            elif v.strip().lower() == 'now':
                continue
            has_date = True 
            self.stepDate.append(v)
        self.send_header(k, v)
    if not has_date:
        tmp = self.date_time_string(time.time())
        self.send_header('date', tmp)
        self.stepDate.append(tmp)
    self.end_headers()
    if chunked:
        chk_data = self.user_defined_body.rstrip('\r\n').split('\r\n')
        for i in range((len(chk_data) -1)/2):
            self.wfile.write(chk_data[2*i] + '\r\n' + chk_data[2*i+1]+'\r\n')
            self.wfile.flush()
            time.sleep(.1)
        self.wfile.write('0\r\n\r\n')
    else:
        self.wfile.write(self.user_defined_body)
    self.wfile.flush()    
    return

class UserDataHelper:
    '''Helper class for user setting request and response headers.
    User can get import information via this class
    '''
    def __init__(self):
        self.serverhandler = HTTPRequestHandlerMock
        self.serverhandler.user_defined_headers= list()
        self.serverhandler.user_defined_body = ''
        self.serverhandler.protocol_version = "HTTP/1.1"
        self.serverhandler.user_defined_response = 200 
        self.serverhandler.user_defined_resp_msg = None
        self.serverhandler.request_headers = list() 
        self.serverhandler.url_counts = dict()
        self.serverhandler.stepDate = list()
        self.setGetMethod('mock_GET')
        self.setHeadMethod('mock_HEAD')
        
    def zeroURLCount(self, key=None):
        if not key:
            self.serverhandler.url_counts.clear()
        else:
            self.serverhandler.url_counts[key] = 0

    def getURLCount(self, key):
        return  self.serverhandler.url_counts.get(key, 0)

    def getStepDate(self):
        if len(self.serverhandler.stepDate):
            return self.serverhandler.stepDate.pop()
        else:
            return None
        
    def setHTTPProtocol(self, protocol):
        self.serverhandler.protocol_version =protocol
 
    def setResponse(self, stat, msg=None):
        self.serverhandler.user_defined_response = stat
        self.serverhandler.user_defined_resp_msg = msg 

    def setBodyContent(self, body):
        self.serverhandler.user_defined_body = body

    def setHeaders(self, headers):
        self.serverhandler.user_defined_headers.extend(headers)

    def clearHeaders(self):
        del self.serverhandler.user_defined_headers[:]
        del self.serverhandler.request_headers[:]
        self.serverhandler.user_defined_body = ''

    def setGetMethod(self, name):
        self.serverhandler.get_method_name = name
        self.serverhandler.__dict__.update({name:eval(name)})

    def setHeadMethod(self, name):
        self.serverhandler.head_method_name = name
        self.serverhandler.__dict__.update({name:eval(name)})

    def getRealRequestHeaders(self):
        tmp = list(self.serverhandler.request_headers)
        del self.serverhandler.request_headers[:]
        return tmp
        
class HTTPServerMock(HTTPServer):
    '''Macaroon HTTP mock server'''

class ThreadedHTTPServerMock(ThreadingMixIn, HTTPServerMock):
    '''Handle requests in a seperate thread'''
    pass



def testserver(port):
    import socket
    import threading
    import sys
    sys.path.append('..')
    import mutil

    from httpmockclient import HTTPHeaders as hh

    helpc = UserDataHelper()
    ip = socket.gethostbyname(socket.getfqdn())
    server = ThreadedHTTPServerMock((ip, port), helpc.serverhandler)
    httpd = threading.Thread(target=server.serve_forever)
    httpd.start()
    print "---http mock server started---"
    body = 'This is a testing case templates'

    resph =list()
    resph.append((hh.CACHE_CONTROL, 'max-ag=9'))
    resph.append((hh.CACHE_CONTROL, 'no-store'))
    resph.append((hh.DATE, mutil.getGmtNow()))
    resph.append((hh.CONTENT_LENGTH, len(body)))
    resph.append((hh.CACHE_CONTROL, 'no-store'))
    resph.append((hh.DATE, mutil.getGmtNow()))
    resph.append((hh.CONTENT_LENGTH, len(body)))

    helpc.setHeaders(resph)
    helpc.setBodyContent(body)


    
if __name__ == '__main__':
    import time

    testserver(8192)
    time.sleep(1000)
