##
# Programming Assignment 1
# CPE 138, Fall 2013
# California State University, Sacramento
#
# This is a single blocking HTTP server implementation
#
# Created by Greg M. Crist, Jr. <gmcrist@gmail.com> & Travis Spitze <travissp87@gmail.com>
##

import logging      # For logging / debug messages
import os.path      # For filesystem path handling
import signal       # For handling graceful shutdowns
import socket       # Network socket coding
import sys          # For exiting
import time         # Date / time functions


# Default configuration for the server
config = {
    'host': '0.0.0.0',
    'port': '9999',
    'maxconnections': 5,
    'wwwroot': './public_html/',
    'indexfile': 'index.html',
    'loglevel': logging.INFO
}

class HttpServer ():
    _defaultConfig = {
        'host': '0.0.0.0',
        'port': '80',
        'maxconnections': 5,
        'wwwroot': './public_html',
        'indexfile': 'index.html',
    }

    _responseCodes = {
        200: 'OK',
        403: 'Forbidden',
        404: 'Not Found',
        500: 'Internal Server Error',
        501: 'Method not implemented'
    }

    def __init__(self, config):
        self.config = dict(self._defaultConfig.items() + config.items())
        self._logger = logging.getLogger('HttpServer')
        self._methodHandlers = { 'GET': self._getHandler }

    ##
    # Starts the server and establishes the server socket
    ##
    def start(self):
        self._logger.info('Starting HTTP server')
        self.wwwroot = os.path.abspath(self.config['wwwroot'])
        self._logger.info('Set www root to ' + self.wwwroot)

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host = str(self.config['host'])
        port = str(self.config['port'])

        try:
            self._logger.info('HTTP server binding to ' + host + ':' + port)
            self.socket.bind((host, int(port)))

        except Exception as e:
            self._logger.critical('Unable to bind HTTP server on ' + host + ':' + port)
            self.stop()
            sys.exit(1)
        
        self._logger.info('HTTP server started and listening on ' + host + ':' + port)
        self._wait()

    ##
    # Closes the server socket
    ##
    def stop(self):
        self._logger.info('Stopping HTTP server')

        try:
            self.socket.shutdown(socket.SHUT_RDWR)
         
        except Exception as e:
            self._logger.error('Could not close socket:' + str(e))

    ##
    # Connection handling logic
    #   * runs a continuous loop and waits for client socket connections
    #   * processes each request and hands it off to a handler for the specified HTTP method
    #   * returns 
    ##
    def _wait(self):
        self.socket.listen(self.config['maxconnections'])

        self._logger.info('Waiting for connections...')

        while (True):
            # Default values
            method = ''
            uri = ''
            body = ''
            response_code = 200

            client, remote_addr = self.socket.accept();
            self._logger.info('Received connection from ' + str(remote_addr))
            
            data = client.recv(1024)
            body = bytes.decode(data)
            parts = body.split(' ');

            method = parts[0].upper()
            
            if (len(parts) > 1):
                uri = parts[1]
            
            self._logger.debug('Method: ' + method)
            self._logger.debug('Request URI: ' + uri)
            self._logger.debug('Request Body: ' + body)

            # Check to see if the request method is implemented and if so, pass off handling to the appropriate handler function
            if (method in self._methodHandlers):
                self._logger.info('Handling ' + method + ' request for URI: ' + uri)
                (response_code, response) = self._methodHandlers[method](uri, body)
            else:
                # If we don't have a support method, generate the appropriate HTTP response status code
                response_code = 501;
                response = self._genErrorHtml(response_code, 'Method ' + method + ' is not implemented on this server')

            
            # Send HTTP response headers and response body to client
            self._logger.info('Sending response to client with response code ' + str(response_code))
            headers = self._genHeaders(response_code);
            client.send(str(headers))
            for i in range(0, len(response)):
                client.send(response[i])
            
            self._logger.info('Closing connection with client')
            client.close()

    ##
    # GET method handler
    ##
    def _getHandler(self, uri, body):
        response = ''
        uri_parts = self._parseURI(uri)

        filename = uri_parts['filename']
        
        self._logger.info('Requesting file: ' + filename)

        # Check to see if the file exists
        if (os.path.isfile(filename)):
            # Open and read the file to be returned
            try:
                fh = open(filename, 'rb')
                data = fh.read()
                while data != '':
                    response += data
                    data = fh.read()
                
                fh.close()
                
                response_code = 200
                
            except Exception as e:
                # There must have been an error of some sort reading the file
                self._logger.error(str(e))
                response_code = 500
                response = self._genErrorHtml(response_code, 'There was an error processing the request. Please try again later.')
                
        elif (os.path.isdir(filename) or ((os.path.basename(filename) == 'index.html') and os.path.isdir(os.path.dirname(filename)))):
            # We don't allow directory file listing with this server
            response_code = 403;
            response = self._genErrorHtml(response_code, 'You don\'t have permission to access {original_file} on this server.'.format(original_file=uri_parts['original_filename']))
            
        else:
            # If the file does not exist, then generate a 404 status code
            response_code = 404
            response = self._genErrorHtml(response_code, 'The requested URL {original_file} was not found on this server.'.format(original_file=uri_parts['original_filename']))
            
        return (response_code, response)

    ##
    # Generate basic headers
    ##
    def _genHeaders(self, response_code):
        headers = ''

        if (response_code in self._responseCodes):
            headers = 'HTTP/1.1 ' + str(response_code) + ' ' + self._responseCodes[response_code] + '\n'
    
        headers += 'Date: ' + time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime()) + '\n'
        headers += 'Server: CPE138-HttpServer\n'
        headers += 'Connection: close\n\n'

        return headers

    ##
    # Generates error HTML for standardizing error message output for the client
    ##
    def _genErrorHtml(self, response_code, message):
        self._logger.info('Running error HTML generation for error code ' + str(response_code))
        return  """<!DOCTYPE html>
                <html>
                    <head>
                        <title>{code} {error}</title>
                    </head>
                    <body>
                        <h1>{error}</h1>
                        <p>{message}</p>
                    </body>
                </html>""".format(code=response_code, error=self._responseCodes[response_code], message=message)

    ##
    # Parses the URI to extract the correct path information for the file
    ##
    def _parseURI(self, uri):
        filename = ''
        query_string = ''

        # The file name portion of the URI is before the '?' character; the query string is after the '?' character
        uri_parts = uri.split('?');

        # Separate the query string just in case we want to parse it further later on
        if (len(uri_parts) > 1):
            query_string = uri_parts[1]

        # Ensure that the file we are requesting is within the specified root path
        # This is to prevent directory traversal attacks (e.g. GET /../../../../../etc/passwd)
        original_filename = uri_parts[0];
        
        relative_filename = os.path.relpath(self.wwwroot + '/' + original_filename, self.wwwroot)
        absolute_filename = os.path.abspath(self.wwwroot + '/' + relative_filename)

        if (os.path.commonprefix([absolute_filename, self.wwwroot]) == self.wwwroot):
            filename = os.path.abspath(absolute_filename)

        # Force the use of an index file (e.g. index.html) when the requested URI is a directory and we are using an indexfile
        if (self.config['indexfile'] != False and os.path.isdir(filename)):
            filename = filename + '/' + os.path.basename(self.config['indexfile'])

        return {
            'original_filename': original_filename,
            'filename': filename,
            'query_string': query_string
        }


##
# Handles graceful shutdown of the server in the event that the process is interrupted / terminated
##
def shutdown(sig, dummy):
    server.stop()
    sys.exit(1)


# General application configuration
logging.basicConfig(format='%(levelname)s:%(message)s', level=config['loglevel'])

signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGINT, shutdown)

# Create an instance of the HTTP server and start it.
server = HttpServer(config)
server.start()
