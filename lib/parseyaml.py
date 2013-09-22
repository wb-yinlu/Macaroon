'''
This module is for processing yaml formatted data file. In this module, it
processes list structure in yaml 1.1 specification and other parts of the
specification will cause the case abnormal.
Author: tutong@taobao.com
Date: Wed, 10 Jul 2013
'''
import sys
sys.path.append('..')
import yaml
import random
from mutil import YamlParseError
global keys_in_yaml
keys_in_yaml = list()

def renameKey(k, keys):
    '''Rename the same key to a new name
    in yaml file
    '''
    i = 0
    key = k
    while keys.has_key(key):
        key = k + '_' + str(i)
        i += 1
    return key

def renameDupliName(fname, keys_l, desc):
    '''preprocessing the yaml file
    1. Getting the comments at beginning
    2. ignore the empty line and commnet line in data sections
    '''
    keys = dict()
    lines = list()
    step_kws = list()
    with open(fname) as f:
        for l in f:
            if l.strip().startswith('--- {'):
                del step_kws[:]
            t_a = l.lower().strip().replace(' ', '')
             
            if t_a.startswith('request:'):
                step_kws.append('request')
            if t_a.startswith('response:'):
                step_kws.append('response')
            if t_a.startswith('servercheck:'):
                step_kws.append('servercheck')
            if t_a.startswith('clientcheck:'):
                step_kws.append('clientcheck')
            if t_a.startswith('config:'):
                if len(step_kws) > 0 :
                   raise  YamlParseError("Control section must be the first in each step")
                step_kws.append('config')
                 
            if l.endswith(','):
                l = l.strip(',').strip()+','
            lines.append(l)
            if l.startswith('#'):
                desc.append(l)
                continue

            if len(l.strip()) == 0:
                lines.pop()
                continue

            if l.strip().strip(',').endswith('{') or l.strip().strip(',').endswith(':') or l.strip().strip(',').endswith('}'):
                if desc and len(lines)>2:
                    if lines[-2].startswith('#'):
                        desc.pop()
                continue
            t = l.strip().strip('}').strip('{').strip(',').split(':', 1)
            if lines[-2].startswith('#'):
                lines.pop(-2)
                desc.pop()
            if len(t) == 1:
                continue
            global keys_in_yaml
            if keys.has_key(t[0]):
                n = renameKey(t[0], keys)
                keys[n] = t[0]
                keys_in_yaml.append(n.lower())
                keys_l.append((n.lower(), t[0].lower()))
                lines.pop()
                lines.append(l.replace(t[0], n, 1))
            else:
                keys[t[0]] = t[0]
                keys_in_yaml.append(t[0].lower())
                keys_l.append((t[0].lower(), t[0].lower()))
            if keys_in_yaml[-1].lower().startswith('sleep'):
                if lines[-2].startswith('--- {'):
                    keys_in_yaml.pop()
    if lines[-1].strip().startswith('#'):
        lines.pop()
        desc.pop()

    processChunkedBody(lines)
    new_b = processCommaInVal(lines)
    return ''.join(new_b)

def processChunkedBody(lines):
    new_lines = []
    i = 0
    while True:
        if lines[i].strip().startswith('body'):
            c = i
            while True:
                if lines[c].strip().endswith('",') or lines[c].strip().endswith("',"):
                    new_lines.append(c)
                    break
                else:
                    new_lines.append(c)
                    if lines[c].strip().endswith('}') or lines[c].strip().endswith('},'):
                       break
                    c += 1
        i += 1
        if i == len(lines):
            break
    for i in new_lines:
        tmp = lines.pop(i)
        lines.insert(i, tmp.strip())
    return lines

def processCommaInVal(lines):
    '''if a comma in value, it must be processed'''
    new_b = list()
    for l in lines:
        if l.startswith('#'):
            new_b.append(l)
            continue
        t = l.strip().split(':', 1)
        if len(t) == 1:
            new_b.append(l)
        else:
           tt_1 = t[1].strip()[:-1]
           tt_2 = t[1].strip()[-1]
           idx = t[1].find(',')
           if idx == -1:
               new_b.append(t[0] + ': ' + t[1].strip())
           elif idx < len(t[1].strip()):
               if t[1].strip().startswith("'"):
                   new_b.append(t[0] + ': ' + t[1].strip())
               else:
                   tt = repr(t[1].strip()[:-1])
                   new_b.append(t[0] + ': ' + tt + tt_2)
           else:
               new_b.append(t[0] + ': ' + t[1].strip())
    return new_b

def processTime(v): 
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
    
    import datetime
    now = datetime.datetime.utcnow()
    delta_s = newV[3:]
    if not delta_s:
        delta_s = '0'
    delta = datetime.timedelta(seconds = eval(delta_s))
    tm = (now + delta).strftime('%a, %d %b %Y %H:%M:%S GMT')
    return tm

def removeEmptyFields(data):
    global keys_in_yaml
    if type(data) is not dict:
        return False
    for k, v in data.items():
        if type(v) is dict:
            return False
        if v == 0:
            continue
        if not v:
            data.pop(k)
            keys_in_yaml.remove(k.lower())
            continue
    return True

def mappingKeys(data):
   '''rename key if data contains key response and request'''
   for k , v in data.items():
       if k.lower() == 'response':
           data.update({'setresponse':v})
           data.pop(k)
       elif k.lower() == 'request':
           data.update({'sendrequest':v})
           data.pop(k)

def removeStepEmpty(data):
    '''Remove empty steps from yaml file'''
    if type(data) is not dict:
        return False
    for k, v in data.items():
        if not removeEmptyFields(v):
            removeStepEmpty(v)
    return True

def lowercaseKeys(d):
    for k, v in d.items():
        if type(v) is str and v.lower() == 'exclude':
            d.update({k.lower():v.upper()})
        else:
            d.update({k.lower():v})
        if not k.islower():
            d.pop(k)
        if type(v) is dict:
            lowercaseKeys(v)

def convertDictToTuple(d):
    '''convert dict to tuple'''
    tmp = list()
    global keys_in_yaml
    for i in range(len(d)):
        try:
            k = keys_in_yaml[i]
            v = d[k]
        except:
            raise  YamlParseError("Sections' order may be incorrect, please check the file!")
        if k.lower().startswith('body') and v.endswith('0\r\n'):
            tmp.append((k, v+'\r\n'))
        else:
            tmp.append((k, v))
    del keys_in_yaml[:len(d)]
    return tmp

def mapDictToList(d):
    steps = list()

    if d.has_key('config'):
        steps.append(convertDictToTuple(d['config']))
        d.pop('config')
    else:
        steps.append(None)

    if d.has_key('request'):
        steps.append(convertDictToTuple(d['request']))
        d.pop('request')
    else:
        steps.append(None)

    if d.has_key('servercheck'):
        steps.append(convertDictToTuple(d['servercheck']))
        d.pop('servercheck')
    else:
        steps.append(None)

    if d.has_key('response'):
        steps.append(convertDictToTuple(d['response']))
        d.pop('response')
    else:
        steps.append(None)

    if d.has_key('clientcheck'):
        steps.append(convertDictToTuple(d['clientcheck']))
        d.pop('clientcheck')
    else:
        steps.append(None) 
    tmp = steps.pop(3)
    steps.insert(1, tmp)
    if len(d):
        del steps[:]
        for k, v in d.items():
            steps.append((k, v))
    return steps

def replaceBack(steps, keys_l):
    '''Replace key's name back'''
    steps_s = repr(steps)
    for k, v in keys_l:
        if k != v:
            steps_s = steps_s.replace(k, v, 1)
    return eval(steps_s)

def addDetail(desc, index, info, key):
    msg = ''
    idx = -1
    for i in range(index + 1, len(desc)):
        if (not desc[i][2:].startswith(' ')) or desc[i][2:].startswith('-'):
            idx = i
            break
        msg += desc[i][2:].strip(' ')
    info.append((key, msg))
    return idx

def addOthers(desc, index, info):
    msg = ''
    for i in range(index, len(desc)):
        msg += desc[i][1:].strip(' ').strip('-')
    info.append(('other', msg))

def getCaseDesc(desc):
    arr = list()
    info = list()
    t_idx = -1
    desc_idx = -1
    step_idx = -1
    for l in range(len(desc)):
        if desc[l][1:].strip().lower().find('case name') > -1:
            t_idx = l   
        if desc[l][1:].strip().lower().find('case description') > -1:
            desc_idx = l
        if desc[l][1:].strip().lower().find('testing steps') > -1:
            step_idx = l

    addDetail(desc, t_idx, info, 'case name')
    addDetail(desc, desc_idx, info, 'case description')
    idx = addDetail(desc, step_idx, info, 'testing steps')
    if idx > 0:
        addOthers(desc, idx, info)
    else:
        info.append(('other', ''))
    return info

def getStepData(path):
    '''parse a yaml file to case steps' data.
    it returns a list with each elements is a list which
    contains tuple as elements
    e.g. [[('case name', ''), ('other', '')], [(), ()], ..., []]
    '''
    keys_l = list()
    case_desc = list()
    lines = renameDupliName(path, keys_l, case_desc)
    
    data = yaml.load_all(lines)
    steps=list()
    for d in data:
        removeStepEmpty(d)
        lowercaseKeys(d)
        steps.append(mapDictToList(d))
    steps = replaceBack(steps, keys_l)
    steps.insert(0, getCaseDesc(case_desc))
    tmp = eval(repr(steps).replace('\\\\r\\\\n', '\\r\\n'))
    return tmp
    
def test():
    import sys, os
    if len(sys.argv) != 2:
        print "Incorrect arguments number"
        sys.exit(1)
    if not os.path.exists(sys.argv[1]):
        print "yaml file [%s] Not exists" % sys.argv[1]
    steps = getStepData(sys.argv[1])
    for i in steps:
        print i, '\n'

if __name__ == '__main__':
    test()
