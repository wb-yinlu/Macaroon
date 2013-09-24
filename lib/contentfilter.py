import os
import sys
sys.path.append('..')
import mutil

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

#adapt with pyunit framework
failureException = AssertionError

def file_size(filename):
    try:
        size = os.path.getsize(filename)
        return size
    except Exception, reason:
        msg = str(reason)
        raise FileReadError(msg)
        return -1
        
def file_read(filename, bufsize=1024):
    content = ''
    buf = ''
    filein = open(filename, 'rb')
    buf = filein.read(bufsize)
    while buf != '':
        content += buf
        buf = filein.read(bufsize)

    filein.close()
    return content 

def file_copy(src, dst):
    filein = open(src, 'rb')
    fileout = open(dst, 'wb')
    buf = ''
    buf = filein.read(1024)
    while buf != '':
        fileout.write(buf)
        buf = filein.read(1024)

    filein.close()
    fileout.close()

    return True

def compress_gzip_string(rawdata, icompresslevel):
    import gzip

    output = StringIO.StringIO()
    f = gzip.GzipFile(fileobj=output, mode='wb', compresslevel=icompresslevel)
    f.write(rawdata)
    f.close()

    cdata = output.getvalue()
    return cdata

class ContentFilter:
    def __init__(self, body, contentencoding=None, transferencoding=None, body_length=-1):
        self.rawbody = body
        self.body_len = body_length

        self.content_raw = None
        self.Content_filtered = ''
        self.content_length = -1

        self.contentlength_raw = -1
        self.contentlength_gziped = -1

        self.ce = contentencoding
        self.te = transferencoding

        # file related config
        self.filename = ''
        self.filelength = -1
        
        #chunk config
        self.chunk = False
        self.chunksize = -1
        self.chunksize_start = 0
        self.chunksize_end = 0

        self.chunkcount = 0
        self.chunkcount_start = 0
        self.chunkcount_end = 0

        #gzip config
        self.gzip = False
        self.gzip_compresslevel = 9
        self.gziped_contentlength = -1

    def setContentEncoding(self, contentencoding):
        '''
        Content-Encoding: gzip
        '''
        self.ce = contentencoding

    def setTransferEncoding(self, transferencoding):
        '''
        Transfer-Encoding: chunked
        '''
        self.te = transferencoding
        
    def setGzip(self, gzip):
        '''
        Content-Encoding:gzip
        value: True|False
        '''
        self.gzip = gzip

    def setChunk(self, ischunk):
        '''
        value: True|False
        '''
        self.chunk = ischunk
    
    
    def isGzip(self):
        return self.gzip

    def isChunk(self):
        return self.chunk

    def getGzipedContentLength(self):
        return self.gziped_contentlength

    def getContentLength(self):
        return self.content_length

    def chunked_encoder_s(self, content, sizestart=1, sizeend=5):
        import random
        def generator():
            total_len = len(content)
            left_len = total_len
            index = 0

            while left_len >= 0:
                size = random.randint(sizestart, sizeend)
                value = ''
                if size < left_len:
                    value = content[index:index+size]
                else:
                    value = content[index:]
                size = len(value)
                index = index + size
                left_len = total_len - size
                if size:
                    yield '%x\r\n' % size
                    yield '%s\r\n' % value
                else:
                    yield '0\r\n'
                    #yield '\r\n'
                    return

        return generator()


    def parsebodyline(self, bodyline):
        ''' 
        parse body cmd line: file(filename='123.gz', chunk-size=1-10B/K/M,
        chunk-count=0-100, gzipcompresslevel=9)
        '''
        import re

        pattern = re.compile('file(.*)', re.IGNORECASE)
        match = pattern.search(bodyline)
        if match == None:
            self.content_raw = bodyline
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

        keys = bodyconf.keys()
        #parse filename chunk-size chunk-count gzip-compresslevel
        if 'filename' in keys:
            self.filename = bodyconf.get('filename')

        if 'chunk-size' in keys:
            userinput = bodyconf.get('chunk-size')
            self.chunksize_start, self.chunksize_end = parsenum(userinput)
            self.chunk = True

        if 'chunk-count' in keys:
            userinput = bodyconf.get('chunk-count')
            self.chunkcount_start, self.chunkcount_end = parsenum(userinput)
            self.chunk = True

        if 'gzip-compresslevel' in keys:
            self.gzip_compresslevel = int(bodyconf.get('gzip-compresslevel'))
            self.gzip = True

    def getRawContent(self):
        '''
        if rawcontent = 'file(...)' parse cmdline and read from file
        else: rawcontent is  rawcontent
        '''
        import random
        
        # 1: get content from user input or body-length
        if self.content_raw != None:
            self.content_length = len(self.content_raw)
            return
        # 2: get content from file
        elif self.filename != '':
            self.filename_length = file_size(self.filename)
            self.content_raw = file_read(self.filename)
            self.content_length = len(self.content_raw)
            return

        # 3: get body from body-length header
        elif self.body_len != -1:
            self.content_raw = mutil.getBodyContent(self.body_len)
            self.content_length = len(self.content_raw)
            return

        # 4. get content from chunk-size and chunk-count
        elif self.chunksize_start >=0 and self.chunkcount_start > 0:
            content = ''
            count = random.randint(self.chunkcount_start, self.chunkcount_end)
            i=0
            while i < count:
                tmpsize = random.randint(self.chunksize_start, self.chunksize_start)
                content += mutil.getBodyContent(length=tmpsize)
                i += 1
            self.content_raw = content
            self.content_length = len(self.content_raw)
            return

        else:
            msg = '''invalid information to get body,format\r\n 
              file(filename=xxx,chunksize=xxx,
              chunk-count=xxx.gzip-compresslevel)'''
            raise UnknownError(msg)
            
    def begin_filter(self):
        self.content_filtered = self.content_raw

    def gzip_filter(self):
        import gzip
        try:
            from cStringIO import StringIO
        except ImportError:
            from StringIO import StringIO

        if self.gzip:
            try:
                output = StringIO()
                f = gzip.GzipFile(fileobj=output, mode='wb',
                compresslevel=self.gzip_compresslevel)
                f.write(self.content_filtered)
                f.close()

                self.content_filtered = output.getvalue()
                self.gziped_contentlength = len(self.content_filtered)

            except Exception, reason:
                msg = 'gzip file error ' + str(reason)
                raise UnknownError(msg)
        
        return True
        
    def chunk_filter(self):
        if self.chunk:
            chunked = ''
            for tmpchunk in self.chunked_encoder_s(self.content_filtered, sizestart=self.chunksize_start, sizeend=self.chunksize_end):
                chunked += tmpchunk
                self.content_filtered = chunked

        return True
    
    def getFilteredContent(self):
        '''
        filter the body step by step, return the filtered body
        '''
        self.content_filtered = self.content_raw
        self.parsebodyline(self.rawbody)
        self.getRawContent()

        self.begin_filter()
        self.gzip_filter()
        self.chunk_filter()

        return self.content_filtered

    
def parsenum(cmdline):
    '''
    B|K|M|G: default is B
    xxx=1-n
    xxx=5
    '''
    units = ['B', 'K', 'M', 'G']
    unit = 'B'
    cmdline = cmdline.upper()
    cmdline = cmdline.replace('MB', 'M')
    cmdline = cmdline.replace('KB', 'K')
    cmdline = cmdline.replace('GB', 'G')
    cmdline = cmdline.replace('B', 'B')

    first = ''
    second = ''
    try:
        if cmdline.find('-') >= 0:
            first = cmdline.split('-')[0]
            second = cmdline.split('-')[1]
            first = first.strip()
            second = second.strip()
        else:
            second = cmdline
    except Exception ,reason:
        msg = str(reason)
        #msg = cmdline + ' parse body config number error, format: xxx=1-n[B|K|M|G] |n[B|K|M|G]'
        raise ParseConfError(msg)
    
    for uu in units:
        if second.endswith(uu):
            unit = uu
    
    if first.isdigit():
        first = first + unit

    second = second.replace('B', ' * 1')
    second = second.replace('K', ' * 1024')
    second = second.replace('M', ' * 1024 * 1024')
    second = second.replace('G', ' * 1024 * 1024 * 1024')
    
    first = first.replace('B', ' * 1')
    first = first.replace('K', ' * 1024')
    first = first.replace('M', ' * 1024 * 1024')
    first = first.replace('G', ' * 1024 * 1024 * 1024')
    
    if first == '':
        first = second
    try:
        second = eval(second)
        first = eval(first)
    except Exception, reason:
        msg = str(reason)
        raise ParseConfError(msg)
    
    if first < 0 or second < 0:
        msg = cmdline + ' parse number error, format: 1-n [B|K|M|G], n [B|K|M|G]'
        raise ParseConfError(msg)

    print first, second
    return first, second
    

class FileReadError(failureException):
    """
    Raise this exception when judge the case is failed
    """
    def __init__(self, msg):
        if not msg:
            msg = repr(msg)
        self.args = msg,
        self.msg = msg
    pass

class UnknownError(failureException):
    def __init__(self, msg):
        if not msg:
            msg = repr(msg)
        self.args = msg,
        self.msg = msg
    pass

class ParseConfError(failureException):
    '''
    Raise while parse conf from user define yaml file
    especially: body: ...
    '''
    def __init__(self, msg):
        if not msg:
            msg = repr(msg)
        self.args = msg,
        self.msg = msg
    pass

def socket_makefile():
    import socket
    ADDR = ("localhost", 12345)

    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(ADDR)
    listener.listen(1)

    client = socket.create_connection(ADDR)
    cf = client.makefile("rb", bufsize=0)

    server, client_addr = listener.accept()
    sf = server.makefile("wb", bufsize=0)

    sf.write(b"Hello World!")
    sf.flush()
    sf.close()
    server.close()
    print(cf.read(99))         # prints "Hello World!"


def itest():
    print parsenum("65536B")

if __name__ == "__main__":
    itest()
