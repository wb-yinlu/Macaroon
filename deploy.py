"""
Description:This module provides methods for operating DUT
    including start, stop and clean

Author: tutong@taobao.com

Date: Fri, 12 Jul 2013
"""
import sys
import os
spath = os.path.split(os.path.realpath(__file__))[0]
lib = spath + '/lib'
sys.path.append(lib)

import agentclient
import config

import socket
import logging
import time


class OperateDUT(object):
    '''for operating proxy via an agent.
    implemented three actions:
    start, stop and clean
    '''
    def __init__(self):
        url = 'http://%s:%s'%(config._server, config._agentport)
        self.agentclient = agentclient.AgentClient(url)

    def startDUT(self):
        cmd = config.DUT_Start
        ret = self.agentclient.execmd(cmd)
        print ret
        return ret

    def stopDUT(self):
        cmd = config.DUT_Stop
        ret = self.agentclient.execmd(cmd)
        print ret
        return ret

    def cleanDUT(self):
        if config._debug == True:
            print '|-Clean DUT...'
        self.stopDUT()
        cmd = config.DUT_Clean
        print self.agentclient.execmd(cmd)
        self.startDUT()
        time.sleep(5)

    def closeAgent(self):
        '''for closing the agentserver'''
        agentclient.closeServerAgent(self.agentclient)

    def doConfig(self, _opconfig):
        for k, v in _opconfig:
            if k == 'sh':
                cmd = v
                print "|-Run cmd '" + cmd + "' on " + config._server
                print self.agentclient.execmd(cmd)

if __name__ == '__main__':
    a = OperateDUT()
    a.cleanDUT()
    a.closeAgent()
