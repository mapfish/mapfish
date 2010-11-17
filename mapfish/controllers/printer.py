# 
# Copyright (c) 2008-2011 Camptocamp.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. Neither the name of Camptocamp nor the names of its contributors may 
#    be used to endorse or promote products derived from this software 
#    without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

import logging

from os.path import basename, getsize
from os import unlink, listdir, sep, stat
import time
from subprocess import Popen, PIPE
from tempfile import NamedTemporaryFile, gettempdir
import re
import simplejson
import urlparse

from pylons.controllers import WSGIController
from pylons import config, request, response, session, url
from pylons.controllers.util import forward

from paste.fileapp import FileApp

def addRoutes(map, baseUrl="/print/", controller="printer"):
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
    TEMP_FILE_PURGE_SECONDS = 600

    def __init__(self):
        WSGIController.__init__(self)
        self._setupConfig()

    def info(self):
        """
        To get (in JSON) the information about the available formats and CO.
        """
        cmd = ['java', '-cp', self.jarPath, 'org.mapfish.print.ShellMapPrinter',
               '--config=' + self.configPath, '--clientConfig', '--verbose='+_getJavaLogLevel()]
        self._addCommonJavaParams(cmd)
        exe = Popen(cmd, stdout = PIPE, stderr = PIPE)
        result = exe.stdout.read()
        error = exe.stderr.read()
        if len(error)>0:
            log.error(error)
        ret = exe.wait()
        if ret == 0:
            response.status = 200
            result = self._addURLs(result)
            if request.params.has_key('var'):
                response.headers['Content-Type'] = 'text/javascript; charset=utf-8'
                return 'var ' + request.params['var'].encode('utf8') + '=' + result + ';'
            else:
                response.headers['Content-Type'] = 'application/json; charset=utf-8'
                return result
        else:
            response.status = 500
            response.headers['Content-Type'] = 'text/plain; charset=utf-8'
            return "ERROR(" + str(ret) + ")\n\n" + error

    def doPrint(self):
        """
        All in one method: creates and returns the PDF to the client.
        """
        cmd = ['java', '-cp', self.jarPath, 'org.mapfish.print.ShellMapPrinter',
             '--config=' + self.configPath, '--verbose='+_getJavaLogLevel()]
        self._addCommonJavaParams(cmd)
        spec = request.params['spec'].encode('utf8')
        exe = Popen(cmd, stdin = PIPE, stdout = PIPE, stderr = PIPE)
        exe.stdin.write(spec)
        exe.stdin.close()
        result = exe.stdout.read()
        error = exe.stderr.read()
        if len(error)>0:
            log.error(error)
        ret = exe.wait()
        if ret == 0:
            response.status = 200
            response.headers['Content-Type'] = 'application/pdf'
            return result
        else:
            response.status = 500
            response.headers['Content-Type'] = 'text/plain; charset=utf-8'
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
               '--verbose='+_getJavaLogLevel(),
               '--output=' + pdfFilename]
        self._addCommonJavaParams(cmd)
        spec = request.environ['wsgi.input'].read()
        exe = Popen(cmd, stdin = PIPE, stderr = PIPE)
        exe.stdin.write(spec)
        exe.stdin.close()
        error = exe.stderr.read()
        if len(error)>0:
            log.error(error)
        ret = exe.wait()
        if ret == 0:
            curId = basename(pdfFilename)[len(self.TEMP_FILE_PREFIX):-len(self.TEMP_FILE_SUFFIX)]

            response.status = 200
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            getURL = self._urlForAction("get", id = curId)
            return simplejson.dumps({
                'getURL': getURL,
                'messages': error
            })
        else:
            try:
                unlink(pdfFilename)
            except OSError:
                pass
            response.status = 500
            response.headers['Content-Type'] = 'text/plain; charset=utf-8'
            return "ERROR(" + str(ret) + ")\n\nspec=" + spec + "\n\n" + error
        return request

    def get(self, id):
        """
        To get the PDF created previously.
        """
        name = gettempdir() + sep + self.TEMP_FILE_PREFIX + id + self.TEMP_FILE_SUFFIX
        headers = {
            'Content-Length' : getsize(name),
            'Content-Type' : 'application/pdf',
            'Content-Disposition' : 'attachment; filename='+id+'.pdf',
            'Pragma' : 'public',
            'Expires' : '0',
            'Cache-Control' : 'private'
            }
        return forward(FileApp(name, **headers))

    def _addCommonJavaParams(self, cmd):
        """
        Adds the java system properties for the locale. Gets it from the request
        parameter "locale" or try to guess it from the "Accept-Language" HTTP
        header parameter.
        Adds as well the referer.
        """
        if request.headers.has_key('REFERER'):
            cmd.append("--referer="+request.headers['REFERER'])

        #allows to run the process without X11
        cmd.insert(1, "-Djava.awt.headless=true")

        if request.params.has_key('locale'):
            locale = request.params['locale']
        else:
            if request.headers.has_key('Accept-Language'):
                locale = request.headers['Accept-Language'].split(',')[0]
            else:
                return
        splitted = re.split("[-_]", locale)
        language = splitted[0]
        cmd.insert(1, "-Duser.language="+language)
        if len(splitted)>1:
            country = splitted[1]
            cmd.insert(1, "-Duser.country="+country)

    def _setupConfig(self):
        self.jarPath = config['print.jar']
        self.configPath = config['print.config']

    def _urlForAction(self, actionName, id = None):
        """
        We cannot trust the URL from the request to get the hostname (proxy).
        This method is returning the base URL for accessing the different
        actions of this controller.
        """
        actionUrl = url(controller="printer", action=actionName, id=id)
        if request.params.has_key('baseurl'):
            return request.params['baseurl'].encode('utf8') + actionUrl.split('/')[-1]
        return urlparse.urlunparse((request.scheme, request.host, actionUrl, None, None, None))

    def _addURLs(self, json):
        expr = re.compile('}$')
        printURL = simplejson.dumps(self._urlForAction("doPrint"))
        createURL = simplejson.dumps(self._urlForAction("create"))
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


def _getJavaLogLevel():
    """
    Convert the python log level into a value to be used with the java
    "--verbose" parameter
    """
    level = log.getEffectiveLevel()
    if level >= 30:
        return '0'
    elif level >= 20:
        return '1'
    else:
        return '2'
