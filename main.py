"""
author - Yuval Hayun
date   - 09/01/24
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


def get_file_data(path):
    """
    Reads file data from the given path.

    :param path: Path to the file
    :type path: str

    :return: File data
    :rtype: bytes
    """
    with open(path, 'rb') as file:
        txt = file.read()
    return txt


def send_page_response(resource):
    """
    Constructs an HTTP response for a requested resource.

    :param resource: Requested resource
    :type resource: str

    :return: HTTP response message
    :rtype: bytes
    """
    path = 'webroot/' + resource
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
    Returns the next number after parsing the resource string.

    :param resource: Resource string
    :type resource: str

    :return: HTTP response message with the next number
    :rtype: bytes
    """
    num = int(resource.split('=')[-1]) + 1
    msg = construct_msg('200 OK', 'text/plain', str(num))
    return msg


def ret_area(resource):
    """
    Calculates the area and constructs an HTTP response.

    :param resource: Resource string
    :type resource: str

    :return: HTTP response message with the area calculation
    :rtype: bytes
    """
    lst = resource.split('?')[-1].split('&')
    height = lst[0].split('=')[-1]
    width = lst[-1].split('=')[-1]
    area = (int(width) * int(height))/2
    area = int(area)
    msg = construct_msg('200 OK', 'text/plain', str(area))
    return msg


def construct_msg(header_type, content_type, body):
    """
    Constructs an HTTP response message.

    :param header_type: Type of HTTP header
    :type header_type: str
    :param content_type: Type of content in the response
    :type content_type: str
    :param body: Body of the message
    :type body: str

    :return: HTTP response message
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


def handle_client_request(resource, client_socket):
    """
    Handles client requests and sends appropriate responses.

    :param resource: Requested resource
    :type resource: bytes
    :param client_socket: Client socket for communication
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
    else:
        msg = send_page_response(resource)

    if msg is not None:
        try:
            logging.debug('the message is:' + str(msg))
            client_socket.send(msg)
        except socket.error as err:
            logging.error('received socket exception while trying to send the message ' + str(err))
    client_socket.close()


def validate_http_request(request):
    """
    Validates an HTTP request.

    :param request: HTTP request data
    :type request: bytes

    :return: Tuple with validation result and resource
    :rtype: tuple[bool, bytes or None]
    """
    parts = request.split(b' ')
    if parts[0] == b'GET':
        return True, parts[1]
    else:
        return False, None


def handle_client(client_socket):
    """
    Handles incoming client connections.

    :param client_socket: Client socket for communication
    :type client_socket: socket.socket
    """
    logging.debug('Client connected')
    request = client_socket.recv(BUFFER_SIZE)
    valid_http, resource = validate_http_request(request)
    if valid_http:
        logging.debug('Got a valid HTTP request')
        handle_client_request(resource, client_socket)
    else:
        logging.error('Error: Not a valid HTTP request')
    logging.debug('Closing connection')


def main():
    """
    Main function to set up a server and handle incoming connections.
    """
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
