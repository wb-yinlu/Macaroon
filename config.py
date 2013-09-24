""" all global config """

_server = '10.232.38.121'
_port = 8080
'''
#Test Server's IP and Port
#_host should directed to mockserver host
_server = '10.232.37.74'
_port = 81
'''
_host = 'www.mm.cn'
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
