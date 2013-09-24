#-*- coding: UTF-8 -*-

"""
user write case in yaml file and this script aimimg to translate yaml file to python
file, and each python file include a unittest case

Usage:
    python data2case.py test_case1.yaml

result:
    test_case1.py

this is a case base on pyunit framework

#Author <buke@taobao.com>
#Date   2013/07/13
"""

import sys
import os
spath = os.path.split(os.path.realpath(__file__))[0]
lib = spath + '/lib'
sys.path.append(lib)

import parseyaml
import config

import getopt

def printDoc(fd, step):
    """
    this method is to write annotation from yaml file as the case file's docString

    :fd - case file written in python
    :step - the annotation from the yaml file
    """

    code = '#-*- coding: UTF-8 -*-\n\n'
    fd.write(code)
    fd.write('"""')

    casename, casedesp, casestep, caseinfo = ['', '', '', '']
    for i in step:
        if i[0] == 'case name':
            casename = i[1]
        elif i[0] == 'case description':
            casedesp = i[1]
        elif i[0] == 'testing steps':
            casestep = i[1]
        elif i[0] == 'other':
            caseinfo = i[1]

    if casename == '':
        yaml = sys.argv[1]
        casename = yaml[0:-5]
    msg = """
||Test Case|| """  + casename
    fd.write(msg)

    msg = """
|-Case Desp-|\n""" + casedesp
    if casedesp != '':
        fd.write(msg)

    msg = """
|-Case step-|\n""" + casestep

    if casestep != '':
        fd.write(msg)

    msg = """
|-Case Info-|\n""" + caseinfo
    if caseinfo != '':
        fd.write(msg)

    fd.write('"""')

def printImport(fd):
    """
    print the case's all import module here
    """

    im = """

import unittest
import logging
import os

import httpmockclient as hc
from httpmockclient import HTTPHeaders as hh
import httpmockserver
import config
import mutil
import deploy

import thread
import socket
import time
import datetime
    """
    fd.write(im)

def printAddLibPath(fd):
    """
    auto find the parent's abs path, and add it to sys.path
    """

    mpath = os.path.split(os.path.realpath(__file__))[0]
    msg = """\n
import sys
sys.path.append('""" + mpath + "')"
    fd.write(msg)
    lib = mpath + '/lib'
    msg = """
sys.path.append('""" + lib + "')"    
    fd.write(msg)
    
def printTestClassName(fd):
    defclassline = """
class TestClassName(unittest.TestCase):\n
    """
    fd.write(defclassline)

def printCleanDUT(fd):
    clean = """
        op = deploy.OperateDUT()
        op.cleanDUT()
    """
    fd.write(clean)

def printSetUp(fd):
    setup = """
    def setUp(self):
        logging.info('case setUp...')
        self.helpc = mutil.startMockServer(config._msport)
    """
    fd.write(setup)
    
def printTearDown(fd):
    teardown = """
    def tearDown(self):
        logging.info('case tearDown...')
        mutil.stopMockServer(self.helpc)
    """
    fd.write(teardown)

def printSetUpClass(fd):
    setupclass = """
    @classmethod
    def setUpClass(self):
        print __doc__
        logging.info('class setUp')
    """
    fd.write(setupclass)

def printTearDownClass(fd):
    teardownclass = """
    @classmethod
    def tearDownClass(self):
        logging.info('class tearDown...')
    """
    fd.write(teardownclass)

def printTestCaseName(fd):
    defcase = """
    def test_casename(self):\n\n"""
    fd.write(defcase)

def printRequestStep(fd, step, serial):
    """
    the request step include 4 different subprocess:

    _response   set response in mockserver to mock upstream server's response
    _request    send a request to proxy or cache
    _servercheck check request from cache or proxy in server side
    _clientcheck check response from cache or proxy in client size
    
    this  4 subprocess's variable is read from user defined yaml file


    """
    #clear url count before step
    zero = '        self.helpc.zeroURLCount()\n'
    fd.write(zero)
    zero = '        self.helpc.clearHeaders()\n'
    fd.write(zero)
    now = '        now = datetime.datetime.utcnow()\n'
    fd.write(now)

    #add configuration step before test
    opconfig = step[0]
    if opconfig != None:
        line1 = '        _opconfig = ' + str(opconfig) + '\n'
        line2 = '        op = deploy.OperateDUT()\n'
        line3 = '        op.doConfig(_opconfig)\n\n'
        fd.write(line1)
        fd.write(line2)
        fd.write(line3)


    response = step[1]
    if response != None:
        line1 = '        _response = ' + str(response) + '\n'
        line2 = '        mutil.replaceNow(_response, now)\n'
        line3 = '        mutil.setResponse(self.helpc, _response)\n\n'
        fd.write(line1)
        fd.write(line2)
        fd.write(line3)

    request = step[2]
    if request != None:
        line0 = '        conn = hc.HTTPConnection(config._server, config._port, config._timeout)\n'
        line1 = '        _request = ' + str(request) + '\n'
        line2 = '        mutil.replaceNow(_request, now)\n'
        line3 = '        response = mutil.sendRequest(self.helpc, conn, _request, %d)\n\n' % serial
        fd.write(line0)
        fd.write(line1)
        fd.write(line2)
        fd.write(line3)

    servercheck = step[3]
    if servercheck != None:
        line1 = '        _servercheck = ' + str(servercheck) + '\n'
        line2 = '        mutil.replaceNow(_servercheck, now)\n'
        line3 = '        mutil.serverCheck(self.helpc, _servercheck)\n\n'
        fd.write(line1)
        fd.write(line2)
        fd.write(line3)

    clientcheck = step[4]
    if clientcheck != None:
        line1 = '        _clientcheck = ' + str(clientcheck) + '\n'
        line2 = '        mutil.replaceNow(_clientcheck, now)\n'
        line3 = '        mutil.clientCheck(self.helpc, response, _clientcheck)\n\n'
        fd.write(line1)
        fd.write(line2)
        fd.write(line3)


def printSleepStep(fd, step):
    """
    if define sleep in yaml file, we add a sleep function here
    """

    line1 = '        _sleep = ' + str(step[0][1]) + '\n'
    line2 = '        mutil.doSleep(_sleep)\n\n'
    fd.write(line1)
    fd.write(line2)
    

def printStepByStep(fd, steps):
    """
    control all step here and distinguish different step here
    """

    num = 0
    #print len(steps)
    for step in steps:
        if step[0] != None and 'sleep' == step[0][0]:
            printSleepStep(fd, step)
        else:
            num = num + 1
            msg = '        print "|*****************Step ' + str(num) +'**********|"\n'
            fd.write(msg)
            printRequestStep(fd, step, num)

def printMain(fd):
    main = """
if __name__ == "__main__":
    unittest.main()
    """
    fd.write(main)

    
if __name__ == '__main__':
    """
    call diff method in order to complete a case file
    you should modified this file much more carefully or the case is not completed or wrong order
    """
    usage = """
    Usage:
      data2case.py --skip env-clean\r\n
    """
    ENV_CLEAN = True

    try:
        options, reminder = getopt.getopt(sys.argv[1:], 's:', ['skip='])
    except getopt.GetoptError as err:
        print 'ERROR: ', err
        print usage
        sys.exit(1)

    for opt, arg in options:
        if opt in ('-s', '--skip'):
            if arg in ('clean', 'env-clean'):
                ENV_CLEAN = False


    casedata = sys.argv[-1]
    casename = casedata[0:-5] + '.py'
    fd = open(casename, 'w')
    steps = parseyaml.getStepData(casedata)

    casenote = steps[0]
    steps.pop(0)

    printDoc(fd, casenote)
    printAddLibPath(fd)
    printImport(fd)
    printTestClassName(fd)
    printSetUp(fd)
    if ENV_CLEAN:
        printCleanDUT(fd)
    printTearDown(fd)
    printSetUpClass(fd)
    printTearDownClass(fd)
    printTestCaseName(fd)

    printStepByStep(fd, steps)

    printMain(fd)
    fd.close()
    
    print 'OK! to run case:'
    print '    python2.7 ',casename
