#!/usr/bin/env python
#coding: utf-8

import time

import tornado.httpserver
import tornado.ioloop
import tornado.web

from tornado import gen
from tornado.web import asynchronous
from tornado.ioloop import IOLoop
from tornado.options import define, options


class getToken(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @gen.engine
    def get(self):
        loop = IOLoop.instance()
        yield gen.Task(loop.add_timeout, time.time() + 0.2)
        self.write("token")
        self.finish()


application = tornado.web.Application([
    (r'/hello', getToken),
])



if __name__ == '__main__':

    
    define("addr", default="0.0.0.0:8001", help="Bind address")
    options.parse_command_line()
    print 'Listening on => ', options.addr
    host, port = options.addr.split(':')
    port = int(port)
    
    http_server = tornado.httpserver.HTTPServer(application, ssl_options={
        "certfile": "cert.pem",
        "keyfile": "key.pem",
    })
    http_server.listen(port, host)
    IOLoop.instance().start()
