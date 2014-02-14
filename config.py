""" all global config """


_server = '10.125.202.112'
#_server = '10.125.9.41'
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
'''
DUT_Start = '/sbin/service swift start'
DUT_Stop = '/sbin/service swift stop'
DUT_Clean = 'rm /home/cdn/swift/sht_filename'
'''
DUT_Start = '/etc/init.d/trafficserver start'
DUT_Stop = '/etc/init.d/trafficserver stop'
DUT_Clean = 'traffic_server -Cclear'
