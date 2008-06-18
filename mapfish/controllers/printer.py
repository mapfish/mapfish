import logging

from os.path import basename, getsize
from os import unlink, listdir, sep, stat
import time
from subprocess import Popen, PIPE
from tempfile import NamedTemporaryFile, gettempdir
import re
import simplejson

from routes.util import url_for
from pylons.controllers import WSGIController
from pylons import config, request, response, session

def addRoutes(map, baseUrl="print/", controller="printer"):
    """
    Add the pylons routes for the print module to the given map
    """
    map.connect(baseUrl + "info.json", controller = controller,
                action = 'info', conditions = dict(method = ['GET']))
    map.connect(baseUrl + "print.pdf", controller = controller,
                action = 'doPrint', conditions  =  dict(method = ['GET']))
    map.connect(baseUrl + "create.json", controller = controller,
                action = 'create', conditions = dict(method = ['POST']))
    map.connect(baseUrl + ":id.pdf", controller = controller,
                action = 'get', conditions = dict(method = ['GET']))

log = logging.getLogger(__name__)

class PrinterController(WSGIController):
    TEMP_FILE_PREFIX = "mfPrintTempFile"
    TEMP_FILE_SUFFIX = ".pdf"
    TEMP_FILE_PURGE_SECONDS = 60

    def __init__(self):
        WSGIController.__init__(self)
        self._setupConfig()

    def info(self):
        """
        To get (in JSON) the information about the available formats and CO.
        """
        cmd = ['java', '-cp', self.jarPath, 'org.mapfish.print.ShellMapPrinter',
               '--config=' + self.configPath, '--clientConfig', '--verbose=0']
        exe = Popen(cmd, stdout = PIPE, stderr = PIPE)
        result = exe.stdout.read()
        error = exe.stderr.read()
        if len(error)>0:
            log.error(error)
        ret = exe.wait()
        if ret == 0:
            self.start_response('200 OK', [
                    ('Content-Type','application/json; charset=utf-8')])
            result = self._addURLs(result)
            if request.params.has_key('var'):
                return 'var ' + request.params['var'].encode('utf8') + '=' + result + ';'
            else:
                return result
        else:
            self.start_response('500 Java error '+ret, [
                    ('Content-Type','text/plain; charset=utf-8')])
            return "ERROR\n\n" + error

    def doPrint(self):
        """
        All in one method: creates and returns the PDF to the client.
        """
        cmd = ['java', '-cp', self.jarPath, 'org.mapfish.print.ShellMapPrinter',
             '--config=' + self.configPath, '--verbose=0']
        exe = Popen(cmd, stdin = PIPE, stdout = PIPE, stderr = PIPE)
        spec = request.params['spec'].encode('utf8')
        exe.stdin.write(spec)
        exe.stdin.close()
        result = exe.stdout.read()
        error = exe.stderr.read()
        if len(error)>0:
            log.error(error)
        ret = exe.wait()
        if ret == 0:
            self.start_response('200 OK', [
                    ('Content-Type','application/x-pdf')])
            return result
        else:
            self.start_response('500 Java error', [
                    ('Content-Type','text/plain; charset=utf-8')
            ])
            return "ERROR(" + str(ret) + ")\n\nspec=" + spec + "\n\n" + error

    def create(self):
        """
        Create the PDF and returns to the client (in JSON) the URL to get the
        PDF.
        """
        self._purgeOldFiles()
        pdfFile = NamedTemporaryFile("w+b", -1, self.TEMP_FILE_SUFFIX, self.TEMP_FILE_PREFIX)
        pdfFilename = pdfFile.name
        pdfFile.close()
        cmd = ['java',
               '-cp', self.jarPath,
               'org.mapfish.print.ShellMapPrinter',
               '--config=' + self.configPath,
               '--verbose=0',
               '--output=' + pdfFilename]
        exe = Popen(cmd, stdin = PIPE, stderr = PIPE)
        spec = request.environ['wsgi.input'].read()
        exe.stdin.write(spec)
        exe.stdin.close()
        error = exe.stderr.read()
        if len(error)>0:
            log.error(error)
        ret = exe.wait()
        if ret == 0:
            curId = basename(pdfFilename)[len(self.TEMP_FILE_PREFIX):-len(self.TEMP_FILE_SUFFIX)]

            self.start_response('200 OK', [
                    ('Content-Type','application/json; charset=utf-8')])
            baseURL = self._getBaseURL()
            return simplejson.dumps({
                'getURL': baseURL + url_for(action = "get", id = curId)
            })
        else:
            unlink(pdfFilename)
            self.start_response('500 Java error', [
                    ('Content-Type','text/plain; charset=utf-8')
            ])
            return "ERROR(" + str(ret) + ")\n\nspec=" + spec + "\n\n" + error
        return request

    def get(self, id):
        """
        To get the PDF created previously.
        """
        name = gettempdir() + sep + self.TEMP_FILE_PREFIX + id + self.TEMP_FILE_SUFFIX

        response.headers['Content-Type'] = 'application/x-pdf'
        response.headers['Content-Length'] = getsize(name)
        response.content = FileIterable(name)
        return

    def _setupConfig(self):
        self.jarPath = config['print.jar']
        self.configPath = config['print.config']
        if config.has_key('print.url') and config['print.url']!='':
            #we cannot trust the URL from the request to get the hostname (proxy)
            self.url = config['print.url']
        else:
            self.url = None

    def _getBaseURL(self):
        if self.url:
            return self.url
        else:
            return "http://" + request.host

    def _addURLs(self, json):
        expr = re.compile('}$')
        baseURL = self._getBaseURL()
        printURL = simplejson.dumps(baseURL + url_for(action = "doPrint"))
        createURL = simplejson.dumps(baseURL + url_for(action = "create")) 
        return expr.sub(',"printURL":' + printURL + ',' +
                        '"createURL":' + createURL + '}', json)

    def _purgeOldFiles(self):
        """
        Delete temp files that are more than TEMP_FILE_PURGE_SECONDS seconds old
        """
        files=listdir(gettempdir())
        for file in files:
            if file.startswith(self.TEMP_FILE_PREFIX) and file.endswith(self.TEMP_FILE_SUFFIX):
                fullname = gettempdir() + sep + file
                age = time.time() - stat(fullname).st_mtime
                if age > self.TEMP_FILE_PURGE_SECONDS:
                    log.info("deleting leftover file :" + fullname + " (age=" + str(age) + "s)")
                    unlink(fullname)


# taken here: http://pythonpaste.org/webob/file-example.html
class FileIterable(object):
     def __init__(self, filename, start = None, stop = None):
         self.filename = filename
         self.start = start
         self.stop = stop
     def __iter__(self):
         return FileIterator(self.filename, self.start, self.stop)
     def app_iter_range(self, start, stop):
         return self.__class__(self.filename, start, stop)
        
class FileIterator(object):
     chunk_size = 4096
     def __init__(self, filename, start, stop):
         self.filename = filename
         self.fileobj = open(self.filename, 'rb')
         if start:
             self.fileobj.seek(start)
         if stop is not None:
             self.length = stop - start
         else:
             self.length = None
     def __iter__(self):
         return self
     def next(self):
         if self.length is not None and self.length <= 0:
             unlink(self.filename)
             raise StopIteration
         chunk = self.fileobj.read(self.chunk_size)
         if not chunk:
             unlink(self.filename)
             raise StopIteration
         if self.length is not None:
             self.length -= len(chunk)
             if self.length < 0:
                 # Chop off the extra:
                 chunk = chunk[:self.length]
         return chunk
