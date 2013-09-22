import os
import shlex
import sys
import getopt
import subprocess
import commands
import time
import glob

def usage():
    print '''
py runner.py [option][value]...
-h or --help
-v or --verbosit="unitest errlog level"
-p or --path="case path"
-s or --send ="email send to"
-c or --copy="email copy to"
-o or --output="log output to"
'''

def colorPrintMessage(color, msg):
    """
    return a message that printed with color

    :color - could choose 'r', 'g', 'b', 'y'
    :msg   - the content will be printed in color

    Usage:
        colorPrintMessage('r', 'red color message')
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
    return "%s %s\x1B[0m" % (color,msg)

    
def execmd(cmd):
    r'''Execute cmd and return the stdout value back
    This function ignore the cmd checking. If you want to
    us some dangerous command such as rm, mv, please check
    it before using
    '''
    args = shlex.split(cmd)
    try:
        proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        retV, retE = proc.communicate()
    except :
        return (None, None)
    else:
        return (retV, retE)
 
def writeTempLog(case, err):
    fd = open(case+'.tmplog', 'w')
    fd.write(err)
    fd.flush()
    fd.close()
    fd = open(case+'.tmplog')
    lines = fd.readlines()
    fd.close()
    fd = open(case+'.tmplog', 'w')
    for l in lines:
        l = l.replace('\r\n', '\n')
        s = l.find('\x1b')
        e = l.find('\r')
        if s > -1 and e > -1:
            l = l[0:s] + l[e+1:]
        fd.write(l.replace('\x1b[60G','').replace('\x1b[0;31m', '').replace('\x1b[0;32m', '').replace('\x1b[0;39m', '').replace('\x1b[1;32m', '').replace('\x1b[0m', ''))
    fd.close()

def dotest(path, python, results):
    if not os.path.exists(path):
        return
    if os.path.isdir(path):
        abs_path = os.path.abspath(path)
        for p in os.listdir(abs_path):
            dotest(os.path.join(abs_path,p), python, results)
    else:
        case_path = os.path.abspath(path)
        if case_path.endswith('.yaml'):
            commands.getoutput('%s data2case.py %s' % (python, case_path))
            c_path, c_name = os.path.split(case_path)
            c_name = c_name.rstrip('.yaml')
            print 'CASE %s is running ......' % c_name 
            output, errput= execmd('%s %s.py'%(python, case_path.split('.yaml')[0]))
            os.system('rm -f %s.py'%case_path.split('.yaml')[0])
            tmp = errput.split('\n')
            if tmp[-2] != 'OK':
                tmp[2] = 'FAIL: %s' % c_name
                results[c_name] = 'FAIL'
                print ''.join(['CASE %s ...... ', colorPrintMessage('r', 'FAIL')]) % c_name
                writeTempLog(c_name, output + '\n'.join(tmp[1:-5])+ '\n')
            else:
                results[c_name] = 'PASS'
                print ''.join(['CASE %s ...... ', colorPrintMessage('g', 'PASS')]) % c_name

def writeLog(fname, results):
    fd = open(fname,'w')
    g = glob.glob('*.tmplog')
    n = [ a[:-7] for a in g]
    for t in results.keys():
        if t not in n:
            fd.write('%s ...... PASS\n' % t)
    for t in n:
        fd.write('%s ...... FAIL\n' % t)
    fd.write('\n')    
    fd.close()
    for f in glob.glob('*.tmplog'):
        os.system('cat %s >> %s' %(f, fname))    
    
if __name__ == '__main__':
    fmt = "%Y%m%d%H%M%S"
    timestamp = time.strftime(fmt, time.localtime())
    transfile =  os.path.abspath("log/record_%s.log"%(timestamp))

    send = "wb-yinlu@taobao.com"
    copy = ""
    path =  os.path.abspath("case/new")

    opts, args = getopt.getopt(sys.argv[1:], "hp:v:s:o:c:",["help","path=","verbosity="])
    for op, value in opts:
        if op == '-p':
            path = value
        elif op == '-v':
            ver=value
        elif op == '-s':
            send=value
        elif op == '-c':
            copy =value
        elif op =='-o':
            transfile=value
        elif op == '-h':
            usage()
            sys.exit(1)
        else:
            pass
    
    python = commands.getoutput('which python2.7')
    if python.strip().lower().startswith('which'):
        print colorPrintMessage('r', 'python2.7 not installed')
        sys.exit(1)
    os.system('rm *.tmplog')
    results = dict()
    print "Test beginning........"
    print
   
    dotest(path, python, results)
    totalFail = 0
    for v in results.values():
        if v == 'FAIL':
            totalFail += 1
    print colorPrintMessage('y', "Total: %d\t\tPassed: %d\t\tFailed: %d" %(len(results), len(results) - totalFail, totalFail))
    writeLog(transfile, results)
    os.system('rm *.tmplog')
    cmd = "mailx -s 'rfc2616Case daily run' -r 'macaron' -c '%s' '%s' < %s"%(copy,send,transfile)
    commands.getoutput(cmd)
