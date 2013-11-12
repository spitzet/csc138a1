CPE 138 Programming Assignment 1
================================



This is a simple HTTP Server written in [python][1] for the CPE 138 course at
[California State University, Sacramento][2] taught by Isaac Ghansah, PhD for
the Fall 2013 semester.

[1]: <http://www.python.org>

[2]: <http://www.csus.edu>



This HTTP server currently implements support for only the GET HTTP method, and
gracefully provides error handling for unsupported methods or invalid requests.
It has basic security to protect against directory traversal attacks.



There are two implementations:

-   A single-threaded server (server.py)

-   A multi-threaded server (server_threaded.py)



The single-threaded will only accept one client connection at a time

The multi-threaded server will accept simultaneous client connections and
processes them simultaneously



This server was created by:

-   Greg M. Crist, Jr. (<gmcrist@gmail.com>)

-   Travis Spitze (<travissp87@gmail.com>)


