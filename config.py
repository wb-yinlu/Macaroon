""" all global config """

_server = '192.168.56.93'
_port = 8080
_host = 'macaroon.zymlinux.net'
_timeout = 15
_msport = 8192 

#log config, True - print, False - no print
_debug = True

#Agent Server port
_agentport = 8192
_agentserver = 'http://' + _server + ':' + str(_agentport)

#DUT related cmd

DUT_Start = '/etc/init.d/trafficserver start'
DUT_Stop = '/etc/init.d/trafficserver stop'
DUT_Clean = 'traffic_server -Cclear'

'''
DUT_Start = '/usr/local/squid/sbin/squid -s'
DUT_Stop = '/usr/local/squid/sbin/squid -k shutdown'
DUT_Clean = 'rm /usr/local/squid/var/cache/00/00/*'
'''
