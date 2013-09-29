#!/usr/local/bin/python2.7
import getopt
import sys

if __name__ == "__main__":
    usage = """
    Usage:
        userscript.py -r $real_response
    """

    try:
        options, reminder = getopt.getopt(sys.argv[1:], 'r:')
    except getopt.GetoptError as err:
        print 'ERROR: ', err
        print usage
        sys.exit(1)
    
    real_response = []
    for opt, arg in options:
        if opt == '-r':
            real_response = arg

    expectbody="content-20-123456789"
    
    msg = None
    
    if real_response.find(expectbody) >=0:
        pass
    else:
        msg = "body unmatch"

    result = []
    if msg == None:
        msg = 'Success'
        result.append(0) 
        result.append(msg)
    else:
        result.append(1)
        result.append(msg)

    sys.stdout.write(str(result))

    exit(0)


