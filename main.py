"""
author - Yuval Hayun
date   - 26/01/24
"""

import socket
import os
import logging

logging.basicConfig(filename='my_log.log', level=logging.DEBUG)

QUEUE_SIZE = 10
IP = '127.0.0.1'
PORT = 80
SOCKET_TIMEOUT = 2
BUFFER_SIZE = 1024
DEFAULT_URL = 'index.html'
CONTENT_TYPES = {
    'html': 'text/html',
    'css': 'text/css',
    'js': 'application/javascript',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
    'gif': 'image/gif',
    'ico': 'image/x-icon'
    }
UPLOADS_PATH = r'C:\Users\nati2\PycharmProjects\project4\webroot\uploads'


def get_file_data(path):
    """
    Returns the content of a file given its path.

    :param path: The path of the file.
    :type path: str
    :return: The content of the file.
    :rtype: bytes
    """
    with open(path, 'rb') as file:
        txt = file.read()
    return txt


def send_page_response(resource, webroot):
    """
    Sends an HTTP response for a requested resource.

    :param resource: The requested resource.
    :type resource: str
    :param webroot: The root directory for web content.
    :type webroot: str
    :return: The HTTP response message.
    :rtype: bytes
    """
    path = webroot + resource
    print('path: ' + path)
    logging.debug('path: ' + path)
    if os.path.isfile(path):
        page = get_file_data(path)
        header = 'HTTP/1.1 200 OK\r\n'.encode()

        end_resource = resource.split('.')[-1]

        content_type = f'Content-Type: {CONTENT_TYPES[end_resource]}\r\n'.encode()
        content_length = f'Content-Length: {len(page)}\r\n\r\n'.encode()

        msg = header + content_type + content_length + page
        return msg


def ret_next_num(resource):
    """
    Returns an HTTP response with the next number.

    :param resource: The requested resource.
    :type resource: str
    :return: The HTTP response message.
    :rtype: bytes
    """
    num = int(resource.split('=')[-1]) + 1
    msg = construct_msg('200 OK', 'text/plain', str(num))
    return msg


def ret_area(resource):
    """
    Returns an HTTP response with the calculated area.

    :param resource: The requested resource.
    :type resource: str
    :return: The HTTP response message.
    :rtype: bytes
    """
    lst = resource.split('?')[-1].split('&')
    height = lst[0].split('=')[-1]
    width = lst[-1].split('=')[-1]
    area = (int(width) * int(height))/2
    msg = construct_msg('200 OK', 'text/plain', str(area))
    return msg


def upload(resource, request,  client_socket):
    """
    Handles file uploads and returns an HTTP response.

    :param resource: The requested resource.
    :type resource: str
    :param request: The HTTP request message.
    :type request: bytes
    :param client_socket: The client socket.
    :type client_socket: socket.socket
    :return: The HTTP response message.
    :rtype: bytes
    """
    try:
        file_name = resource.split('=')[-1]
        file_path = os.path.join(UPLOADS_PATH, file_name)
        msg = construct_msg('200 OK', 'text/plain', '')
        request = request.decode()
        content_length = request.split('\r\n')
        for i in content_length:
            if 'Content-Length' in i:
                content_length = int(i.split(':')[1])
                break
        body = client_socket.recv(content_length)
        with open(file_path, 'wb') as file:
            file.write(body)
        return msg
    except socket.error as err:
        logging.error('received socket exception - ' + str(err))


def image(resource):
    """
    Returns an HTTP response for an image resource.

    :param resource: The requested resource.
    :type resource: str
    :return: The HTTP response message.
    :rtype: bytes
    """

    file_name = resource.split('=')[-1]
    return send_page_response(file_name, UPLOADS_PATH + '/')


def construct_msg(header_type, content_type, body):
    """
    Constructs an HTTP response message.

    :param header_type: The HTTP header type.
    :type header_type: str
    :param content_type: The content type.
    :type content_type: str
    :param body: The body of the response.
    :type body: str
    :return: The HTTP response message.
    :rtype: bytes
    """
    if header_type.startswith('302'):
        location_to = f'Location: /\r\n'.encode()
    else:
        location_to = b''
    body = body.encode()
    header = f'HTTP/1.1 {header_type}\r\n'.encode()
    content_type = f'Content-Type: {content_type}\r\n'.encode()
    content_length = f'Content-Length: {len(body)}\r\n\r\n'.encode()
    msg = header + content_type + location_to + content_length + body
    return msg


def handle_client_request(resource, request, client_socket):
    """
    Handles the client request and sends an appropriate HTTP response.

    :param resource: The requested resource.
    :type resource: bytes
    :param request: The HTTP request message.
    :type request: bytes
    :param client_socket: The client socket.
    :type client_socket: socket.socket
    """
    resource = resource.decode()
    if resource == '/':
        resource = '/' + DEFAULT_URL

    msg = ''
    if resource == '/forbidden':
        msg = construct_msg('403 forbidden', 'text/html', '403 FORBIDDEN')
    elif resource == '/moved':
        msg = construct_msg('302 moved temporarily', 'text/html', '302 MOVED TEMPORARILY')
    elif resource == '/error':
        msg = construct_msg('500 error', 'text/html', '500 INTERNAL SERVER ERROR')
    elif resource.startswith('/calculate-next'):
        msg = ret_next_num(resource)
    elif resource.startswith('/calculate-area'):
        msg = ret_area(resource)
    elif resource.startswith('/upload'):
        msg = upload(resource, request, client_socket)
    elif resource.startswith('/image'):
        msg = image(resource)
    else:
        msg = send_page_response(resource, 'webroot/')

    if msg is not None:
        try:
            logging.debug('the message is:' + str(msg))
            client_socket.send(msg)
        except socket.error as err:
            logging.error('received socket exception while trying to send the message ' + str(err))
    client_socket.close()


def validate_http_request(request):
    """
    Validates the HTTP request and returns the resource.

    :param request: The HTTP request message.
    :type request: bytes
    :return: A tuple with a boolean indicating validity and the resource.
    :rtype: tuple
    """
    parts = request.split(b' ')
    if parts[0] == b'GET' or parts[0] == b'POST':
        return True, parts[1]
    else:
        return False, None


def receive(client_socket):
    """
    Receives the headers of the HTTP request.

    :param client_socket: The client socket.
    :type client_socket: socket.socket
    :return: The received headers.
    :rtype: str
    """
    headers = ''
    try:
        while not headers.endswith('\r\n\r\n'):
            chunk = client_socket.recv(1).decode()
            if not chunk:   # empty msg
                break
            headers += chunk
        return headers
    except socket.error as err:
        logging.error('received socket exception - ' + str(err))
        return ''


def handle_client(client_socket):
    """
    Handles the client connection and processes the HTTP request.

    :param client_socket: The client socket.
    :type client_socket: socket.socket
    """
    logging.debug('Client connected')
    request = receive(client_socket).encode()
    valid_http, resource = validate_http_request(request)
    if valid_http:
        logging.debug('Got a valid HTTP request')
        handle_client_request(resource, request, client_socket)
    else:
        logging.error('Error: Not a valid HTTP request')
    logging.debug('Closing connection')


def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind((IP, PORT))
        server_socket.listen(QUEUE_SIZE)
        logging.debug('Listening for connections on port %d' % PORT)
        while True:
            client_socket, client_address = server_socket.accept()
            try:
                logging.debug('New connection received')
                client_socket.settimeout(SOCKET_TIMEOUT)
                handle_client(client_socket)
            except socket.error as err:
                logging.error('received socket exception - ' + str(err))
            finally:
                client_socket.close()
    except socket.error as err:
        logging.error('received socket exception - ' + str(err))
    finally:
        server_socket.close()


if __name__ == "__main__":
    main()
