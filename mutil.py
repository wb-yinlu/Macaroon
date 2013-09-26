# -*- coding: utf-8 -*-

"""
    macaroon.mutil

    implement various help method here

    :Author <buke@taobao.com>
    :Date   2013/07/16

"""

import sys
import os

#get macaroon lib's abs path and add to sys.path
spath = os.path.split(os.path.realpath(__file__))[0]
lib = spath + '/lib'
sys.path.append(lib)

import time
import socket
import hashlib
import urllib
import logging
import threading
import re

import config
import httpmockserver
import httpmockclient as hc
import contentfilter
import datetime
import agentserver

__all__ = ['getGmtNow', 'getLocalIP', 'md5sum', 'getRandomUri', 'CaseError', 'YamlParseError']

HTTP_DATE_FILELDs = ['date', 'last-modified', 'expires', 'if-modified-since']
#set tmpurl for url hit or miss test
global _currenturi
_currenturi = ""

global stepdates
stepdates = dict()

global server
global httpd_G
def setCurrentUri(uri):
    global _currenturi
    _currenturi = uri

def getCurrentUri():
    global _currenturi
    return _currenturi

failureException = AssertionError
""" 
    Adapt to unittest's framework, judge failure depend on AssertionError
    Exception
    as follows, all self defined exception inherit failueException
"""

def replaceNow(lst, now):    
    _lst = list()
    for k, v in lst:
        if k.lower() == 'date':
            _lst.append((k, v))
            continue
        if type(v) is not str:
            _lst.append((k, v))
            continue
        tm = date_time_string(v, now)
        if tm:
            _lst.append((k, tm))
        else:
            _lst.append((k, v))
    del lst[:]
    lst.extend(_lst)

def date_time_string(v, now):
    '''parse the now value to a real date time value'''
    b = []
    for i in range(len(v)):
        if not v[i].isspace():
            b.append(v[i])
    newV = ''.join(b).lower()
    if not newV.startswith('now'):
        return None
    if newV.count('+') > 1:
        return None
    elif newV.count('-') > 1:
        return None
    elif newV.count('now') > 1:
        return None
    
    delta_s = newV[3:]
    if not delta_s:
        delta_s = '0'
    delta = datetime.timedelta(seconds = eval(delta_s))
    tm = (now + delta).strftime('%a, %d %b %Y %H:%M:%S GMT')
    return tm

def myPrint(color, msg):
    """
    color print method

    :color - could choose 'r', 'g', 'b', 'y'
    :msg   - the content will be printed in color

    Usage:
        myPrint('r', 'red color message')
    """

    if color == 'r':
        fore = 31
    elif color == 'g':
        fore = 32
    elif color == 'b':
        fore = 36
    elif color == 'y':
        fore = 33
    else:
        fore = 37
    color = "\x1B[%d;%dm" % (1,fore)
    print "%s %s\x1B[0m" % (color,msg)


def getLocalIP():
    """
    get local host ip address
    """
    lip = socket.gethostbyname(socket.getfqdn())
    logging.info('getLocalIP: ' + lip)
    return lip

def getGmtNow(inteval=0):
    """
    get current time and return in gmt format as a string as below:
        
        Mon, 15 Jul 2013 04:05:51 GMT

    """

    fmt = '%a, %d %b %Y %H:%M:%S GMT'

    ctime = time.time()
    if inteval == 0:
        return time.strftime(fmt)
    else:
        ntime = ctime + inteval
        ntime = time.localtime(ntime)
        return time.strftime(fmt, ntime)

def gmt2Datetime(gmttime):
    GMT_FORMAT = '%a, %d %b %Y %H:%M:%S GMT'
    dt = datetime.datetime.strptime(gmttime, GMT_FORMAT)
    return dt


def timestamp2Datetime(timestamp):
    dt = datetime.datetime.utcfromtimestamp(timestamp)
    return dt

def datetime2Timestamp(dt):
    import calendar 
    timestamp = calendar.timegm(dt.utctimetuple())
    return timestamp


def fail(msg=None):
    """Fail immediately, with the giv"""
    raise failureException(msg)

def parseBodyLine(bodyline):
    ''' 
    parse body cmd line: file(filename='123.txt')
    in client check
    '''
    import re

    pattern = re.compile('file(.*)', re.IGNORECASE)
    match = pattern.search(bodyline)
    if match == None:
        return -1

    bodyconf = {}
    bodyline = bodyline.strip()
    bodyline = bodyline.replace('file(', '')
    bodyline = bodyline.replace(')', '')
    bodyline = bodyline.replace("'", '')
    bodyline = bodyline.replace('"', '')
    for keyword in bodyline.split(','):
        key = keyword.split('=')[0]
        value = keyword.split('=')[1]
        key = key.strip()
        value = value.strip()
        bodyconf.setdefault(key, value)

    return bodyconf

def md5sum(fd=None, str=None, url=None):
    """
        md5sum diff object
    fd  - file
    str - string
    url - object from the url
    
    return md5 string in hex
    """
    m = hashlib.md5()
    md5 = None
    if fd is not None:
        cc = fd.read()
        m.update(cc)
        md5 = m.hexdigest()
    elif str is not None:
        
        m.update(str)
        md5 = m.hexdigest()
    elif url is not None:
        try:
            ff = urllib.urlopen(url, 'rb')
        except:
            return md5
        cc = ff.read()
        m.update(cc)
        md5 = m.hexdigest()

    return md5

def testBooleanExpr(num, expression):
    """
    test boolean expression is true or false

    :num - target number
    :the - boolean expression

    Usage:
        testBooleanExpr(200, '>= 300')
        return: false

        ---
        testBooleanExpr(200, '>100 and <300')
        return: true

        ---
        testBooleanExpr(200, '!= 100')
        return: true
    """

    expression = expression.strip()

    if expression.find('and') > 0:
        expr1, expr2 = expression.split('and')
        return testBoolean(num, expr1) and testBoolean(num, expr2)
    elif expression.find('or') > 0:
        expr1, expr2 = expression.split('or')
        return testBoolean(num, expr1) or testBoolean(num, expr2)
    else:
        return testBoolean(num, expression)

def testBoolean(num, expression):
    operator = ['>', '<', '==', '>=', '<=', '!=', '<>']
    expression = expression.strip()

    isop = False
    for op in operator:
        if expression.find(op) >= 0:
            isop = True
            result = str(num) + expression
            break
    if not isop:
        result = str(num) + '==' + expression
    return eval(result)


def getRandomUri(length=10):
    """
    :lenght - url length
    @return the url in defined length
    
    the url if combined in:
    digit, letters and special letters ' #?=&%#+'
    """
    
    import random

    charset = ' /?%#&=1234567890qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLMNBVCXZ'
    length_charset = len(charset)

    uri = '/'
    i = 0
    while i < length:
        uri += charset[random.randint(0, length_charset-1)]
        i += 1
    
    return uri

def getBodyContent(length=1000):
    """ create content body of length"""

    if length < 0:
        raise CaseError('length must not less than 0')

    import random

    charset = '/?%#&=1234567890qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLMNBVCXZ~!@#$%^&*()_+'
    alen = len(charset)

    body = ''
    i = 0
    while i < length:
        body += charset[random.randint(0, alen-1)]
        i += 1

    return body

def startMockServer(port):
    """ init mock server and return UserDataHelper()"""

    helper = httpmockserver.UserDataHelper()
    ip = getLocalIP()
    global server
    global httpd_G
    server = httpmockserver.ThreadedHTTPServerMock((ip, port), helper.serverhandler)
    httpd_G = threading.Thread(target=server.serve_forever)
    httpd_G.start()
    myPrint('g', '|-- Http mock server start at %s:%s...\n'%(ip, str(port)))

    return helper

def stopMockServer(helper):
    helper = None
    global server
    th_2 = threading.Thread(target=server.shutdown)
    th_2.start()
    httpd_G.join()
    th_2.join()
    server = None
    myPrint('g', '|-- Http mock server stopped...\n')


def getDefaultResponse():
    """ mock server will user dftresponse if server did not set any other
    config"""

    #dftresponse = {'protocol':'HTTP/1.1', 'statuscode':200, 'content-length':10}
    dftresponse = [('protocol','HTTP/1.1'),('statuscode',200),('content-length',0)]
    return dftresponse

def getDefaultRequest():
    """ min request if user do not set request header or method"""

    #dftrequest = {'method':'GET', 'uri':'/', 'protocol':'HTTP/1.1', 'host':config._host, 'user-agent':'mockclient 0.1', 'accept':'*/*'}
    dftrequest = [('method','GET'), ('uri','/'), ('protocol', 'HTTP/1.1'), ('host', config._host), ('user-agent', 'mockclient/0.1'), ('accept', '*/*')]

    return dftrequest

def parseRequestLine(request):
    _method = 'UNDEFINE'
    _uri = ''
    _protocol = 'UNDEFINE'

    for i in request:
        if i[0] == 'method':
            _method = i[1]
        elif i[0] == 'uri':
            _uri = i[1]
        elif i[0] == 'protocol':
            _protocol = i[1]

    if _method != 'UNDEFINE':
        removeItem('method', request)
    if _uri != '':
        removeItem('uri', request)
    if _protocol != 'UNDEFINE':
        removeItem('protocol', request)

    return _method, _uri, _protocol


def parseStatusLine(response):
    _protocol = '_UNDEFINE'
    _statuscode = 0

    iresponse = response
    for i in iresponse:
        if i[0] == 'statuscode':
            _statuscode = i[1]
        if i[0] == 'protocol':
            _protocol = i[1]

    if _protocol != '_UNDEFINE':
        removeItem('protocol', response)
    if _statuscode != 0:
        removeItem('statuscode', response)

    return _protocol, _statuscode

def processStepDate(stepDate):
    elems = []
    tmp = []
    for i in stepDate:
        if i in ['+', '-', '*', '/', '%']:
            elems.append(''.join(tmp))
            del tmp[:]
            elems.append(i)
        elif not i.isspace():
            tmp.append(i)
        else:
            elems.append(''.join(tmp))
            del tmp[:]
    if len(tmp):
        elems.append(''.join(tmp))
        del tmp[:]
    for e in elems:
        if stepdates.has_key(e):
            dt = gmt2Datetime(stepdates[e])
            ts = datetime2Timestamp(dt)
            tmp.append(str(ts)) 
        else:
            tmp.append(e) 
    dt = timestamp2Datetime(eval(''.join(tmp)))
    
    return dt.strftime('%a, %d %b %Y %H:%M:%S GMT')

def printHeader(headers):
    for k, v in headers:
        if k.lower() in HTTP_DATE_FILELDs: 
            if v.strip().find('_Date_Step') > 0:
                v_new = processStepDate(v)
                print '%s:'%(k), v_new
            else:
                print '%s:'%(k), v
        else:
            print '%s:'%(k), v

def getHeaderKeys(headers):
    """
    headers is a list like below
    [('Host','ss.cn'),('User-Agent','mockclient'),('Connection', 'close')]
    """
    names = []
    for i in headers:
        names.append(i[0])

    return names

def getHeaderValues(name, headers):
    """
    [('Host','ss.cn'),('User-Agent','mockclient/0.1'),('Connection', 'close')]
    getHeaderValues('Host')
    ['ss.cn']
    """
    values = []
    for i in headers:
        if i[0] == name:
            if i[0].lower() in HTTP_DATE_FILELDs: 
                if i[1].strip().find('_Date_Step') > 0:
                    v_new = processStepDate(i[1])
                    values.append(v_new)
                else:
                    values.append(i[1])
            else:
                values.append(i[1])

    return values

def reCompare(string, target):
    pattern = re.compile(target[2:-1], re.IGNORECASE)
    match = pattern.search(string)
    if match != None:
        return True
    else:
        return False

def isRaw(target):
    pattern = re.compile('r\'|r"', re.IGNORECASE)
    match = pattern.match(target)
    if match != None:
        return True
    else:
        return False
    
def timeProcess(rawtime):
    if rawtime != 'None':
        if rawtime.find('GMT'):
            dt = gmt2Datetime(rawtime)
            ts = datetime2Timestamp(dt)
            return ts
        else:
            rawtime = rawtime.strip()
            global stepdates
            ts = stepdates[rawtime]
            return ts
    else:
        return rawtime

def checkHeader(expectheader, realheader):
    expectkeys = getHeaderKeys(expectheader)
    realkeys   = getHeaderKeys(realheader)
    for key in expectkeys:
        tmpvalues = getHeaderValues(key, expectheader)
        if ('exclude' in tmpvalues) or ('EXCLUDE' in tmpvalues) :
            #case1: exclude process
            if key in realkeys:
                msg = 'header ' + key + ' should EXCLUDE'
                raise CheckHeaderError(msg)
            else:
                break
        elif key not in realkeys:
            #case2: key not exist
            msg = 'expect header ' + key + ' not exist'
            raise CheckHeaderError(msg)

        else:
            #case3: key compare
            expectvalue = getHeaderValues(key, expectheader)
            realvalue = getHeaderValues(key, realheader)
            if len(expectvalue) != len(realvalue):
                msg = key + " header num not equal"
                raise CheckHeaderError(msg)

            expectvalue.sort()
            realvalue.sort()
            k = 0
            while k < len(expectvalue):
                #traverse the value list and make compare
                try:
                    expect = str(expectvalue[k])
                    real = str(realvalue[k])
                    if key in ['date', 'last-modified', 'if-modified-since']:
                        #time header process
                        expect = str(timeProcess(expect))
                        real   = str(timeProcess(real))

                    #Begin compare...    
                    if isRaw(expect):
                        #case1: Regex compare
                        if reCompare(real, expect):
                            pass
                        else:
                            msg = '--Regex compare--'
                            raise CheckHeaderError(msg)

                    elif key in ['age', 'content-length', 'date','last-modified', 'if-modified-since']:
                        #case2: Num compare:> >=  < <= = !=
                        if testBooleanExpr(real, expect):
                            pass
                        else:
                            msg = '--Num compare--'
                            raise CheckHeaderError(msg)

                    else:
                        #case3: String compare
                        if expect == real:
                            pass
                        else:
                            msg = '--String compare--'
                            raise CheckHeaderError(msg)

                except Exception, reason:
                    msg = str(reason) + ' Expect Header ' + key + ':' + str(expectvalue)[1:-1] + '  Real Header ' + key + ':' + str(realvalue)[1:-1]
                    raise CheckHeaderError(msg)
                k = k + 1

def combineHeader(list1, list2):
    #add list2 to list1, if exist pass
    keys1 = getHeaderKeys(list1)
    keys2 = getHeaderKeys(list2)
    for k, v in list1:
        if k.lower() in HTTP_DATE_FILELDs: 
            if v.strip().find('_Date_Step') > 0:
                v_new = processStepDate(v)
                list1.remove((k, v))
                list1.append((k, v_new))
    for k in keys2:
        if k in keys1:
            pass
        else:
            values = getHeaderValues(k, list2)
            for v in values:
                hdr = (k, v)
                list1.append(hdr)

    return list1

def removeItem(key, list):
    #[(),{}]
    i = 0
    while i < len(list):
        if list[i][0] == key:
            list.pop(i)
        i = i + 1

def setResponse(helpc, response):
    """
    set response for mockserver
    
    :response - a list containing header tuple
    :helpc - a mockserver handler

    Usage:
        response = [('content-length', 10),('body', '1234567890')]
        setResponse(helpc, response)

    """

    tmp = dict(response)

    #default remove content-length from response if transfer-encoding
    if tmp.has_key('transfer-encoding'):
        if not tmp.has_key('content-length'):
            response.append(('content-length', 'EXCLUDE'))

    keys = getHeaderKeys(response)
    
    body = None
    cl = 0
    bl = -1
    filter_length = 0
    #create body
    if 'body-length'in keys:
        bl = int(getHeaderValues('body-length', response)[0])
        body = getBodyContent(bl)
        removeItem('body-length', _response)

    if 'body' in keys:
        body = getHeaderValues('body', response)[0]
        cfilter = contentfilter.ContentFilter(body, body_length=bl)
        body = cfilter.getFilteredContent()
        if cfilter.isGzip():
            filter_length = cfilter.getGzipedContentLength()
        else:
            filter_length = cfilter.getContentLength()
        removeItem('body', response)

    #add content-length if not exist
    tmp = dict(response)
    if body != None:
        if not tmp.has_key('content-length'):
            response.append(('content-length', str(filter_length)))

    _response = getDefaultResponse()
    _response = combineHeader(response, _response)
    _protocol, _statuscode = parseStatusLine(_response)


    #remove exclude header from response
    keys = getHeaderKeys(_response)
    for key in keys:
        if key.lower() == 'date':
            continue
        if ('EXCLUDE' or 'exclude') in getHeaderValues(key, _response):
            removeItem(key, _response)

    helpc.setHTTPProtocol(_protocol)
    helpc.setResponse(_statuscode)
    helpc.setHeaders(_response)
    helpc.setBodyContent(body)
    
    if _statuscode in hc.responses.keys():
        reason = hc.responses[_statuscode]
    else:
        reason = 'Unrecognized'

    if config._debug:
        myPrint('g', '[setResponse]:')
        print('%s %d %s'%(_protocol, _statuscode, reason))
        printHeader(_response)
        if filter_length <= 1024:
            print repr(body)
        else:
            print 'body is too long:',filter_length
        print


def sendRequest(helpc, conn, request, serial):
    _request = getDefaultRequest()
    _request = combineHeader(request, _request)

    _method, _uri, _protocol = parseRequestLine(_request)

    ibody = ''
    keys = getHeaderKeys(_request)
    if 'body' in keys:
        ibody = getHeaderValues('body', _request)[0]
        removeItem('body', _request)
    
    host = getHeaderValues('host', _request)[0]
    setCurrentUri(host+_uri)
    conn._http_vsn_str =  _protocol
    conn.request(_method, _uri, headers=_request, body=ibody)


    if config._debug:
        myPrint('g', '[sendRequest]:')
        print('%s %s %s'%(_method, _uri, _protocol))
        printHeader(_request)
        print

    response = conn.getresponse()
    k_d = 'D_Date_Step%d' % serial
    k_s = 'S_Date_Step%d' % serial
    stepdates.update({k_d: response.getheader('date')})
    stepdates.update({k_s: helpc.getStepDate()})
    return response
    
def serverCheck(helpc, servercheck):
    """ check request at server side for below points:
    method
    uri
    protocol
    general headers
    """
    if config._debug:
        myPrint('g', '[serverCheck]:')
        printHeader(servercheck)
        print
    
    realrequest = helpc.getRealRequestHeaders()
    if config._debug:
        print('|-Real request:')
        printHeader(realrequest)
        print

    checkHeader(servercheck, realrequest)

def version2protocol(version):
    """default support http/1.1 http/1.0 http/0.9 other version is unknown"""
    iprotocol = 'UNKNOW'
    if version == 11:
        iprotocol = 'HTTP/1.1'
    elif version == 10:
        iprotocol = 'HTTP/1.0'
    elif version == 9:
        iprotocol = 'HTTP/0.9'
    else:
        iprotocol = 'UNKNOW'

    return iprotocol
    
def clientCheck(helpc, response, clientcheck):
    """ check response at client side for below point
    protocol
    statuscode
    headers
    body
    """
    if config._debug:
        myPrint('g', '[clientCheck]:')
        printHeader(clientcheck)
        print

    #retheader = response.getheaders()
    retheader = response.msg.hlist_tuple
    version, status, reason = response.version, response.status, response.reason

    #add Real-Cache keyword framework
    
    keys = getHeaderKeys(clientcheck)
    uri = getCurrentUri()
    ishit = 'no request uri'
    if uri != '':
        count = helpc.getURLCount(uri)
        if count >= 1:
            ishit = 'MISS'
        else:
            ishit = 'HIT'
    
    xcache = ('real-cache', ishit)
    if 'real-cache' in keys:
        retheader.append(xcache)

    iprotocol = version2protocol(version)
    if config._debug:
        print('|-Real Response:')
        print iprotocol, status, reason
        printHeader(retheader)
        print

    if 'protocol' in keys:
        protocol = getHeaderValues('protocol', clientcheck)[0]
        removeItem('protocol', clientcheck)
        response.checkprotocol(protocol)

    if 'statuscode' in keys:
        statuscode = getHeaderValues('statuscode', clientcheck)[0]
        removeItem('statuscode', clientcheck)
        response.checkstatuscode(str(statuscode))

    #Begin to process body here
    try:
        body = response.read()
        """
        savebody = open(sys.argv[0]+'.body', 'wb')
        savebody.write(body)
        savebody.close()
        """
    except hc.IncompleteRead as e:
        body =  e.partial
    
    #Variable support: $real_response $response_body
    #$real_response = {'body':'abc', protocol:'HTTP/1.1', statuscode:200, reason: 'OK', date:'xxx'}...
    real_response = retheader
    real_response.append(('version', version))
    real_response.append(('status', status))
    real_response.append(('reason', reason))
    real_response.append(('body', body))
    
    #$response_body = $body
    response_body = body
    if 'body' in keys:
        ibody = getHeaderValues('body', clientcheck)[0]
        removeItem('body', clientcheck)
        
        #expect body is regex, use regex compare with real response body
        if isRaw(ibody):
            if reCompare(body, ibody):
                pass
            else:
                msg = "expect body: " + ibody + " real response body: " + body
                raise CheckResponseError(msg)
        #read expect body from file when the body is large
        elif parseBodyLine(ibody) != -1:
            bodyconf = parseBodyLine(ibody)
            bkeys = bodyconf.keys()
            if 'filename' in bkeys:
                filename = bodyconf.get('filename')
                ibody = contentfilter.file_read(filename)
                response.checkbodyhexmd5(ibody,body)
        #expect body is complete
        else:
            response.checkbodyhexmd5(ibody,body)

    if 'sh' in keys:
        all_sh = getHeaderValues('sh', clientcheck)
        removeItem('sh', clientcheck)
        i = 0
        while i < len(all_sh):
            current_sh = all_sh[i]
            current_sh = current_sh.replace('$real_response', str(real_response))
            current_sh = current_sh.replace('$response_body', response_body)
            result = agentserver.execmd(current_sh)
            #the result should be jason format data [0, Success message] or [1,'Fail message']
            print result
            is_success = result[0]
            if is_success == 0:
                pass
            else:
                msg = result[1]
                raise CheckResponseError(msg)


    checkHeader(clientcheck, retheader)

    
def doSleep(_sleep):
    myPrint('g','client sleep %d secondes...'%(_sleep))
    time.sleep(_sleep)

class YamlParseError(Exception):
    r"""Raise this exception when parsing yaml file failed"""

class CaseError(failureException):
    """
    Raise this exception when judge the case is failed
    """

    def __init__(self, msg):
        if not msg:
            msg = repr(msg)
        self.args = msg,
        self.msg = msg
    
class CheckHeaderError(failureException):
    """
    Raise this exception when header compare failed in clientcheck or
    servercheck
    """
    def __init__(self, msg):
        if not msg:
            msg = repr(msg)
        self.args = msg,
        self.msg = msg
    pass

class CheckResponseError(failureException):
    """
    raise this exception when body compare failed in clientcheck or servercheck
    """
    def __init__(self, msg):
        if not msg:
            msg = repr(msg)
        self.args = msg,
        self.msg = msg
    pass

if __name__ == '__main__':
    print getBodyContent(length=10)
