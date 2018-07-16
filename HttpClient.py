#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'JiaSong'

import urllib2
import json
import md5
import re
import logger

MAX_READ_LEN = 4096


class HttpClient(object):
    '''
    HTTP客户端
    '''

    def get_url(self, host, port, uri, **query_args):
        '''
        拼接完整的url

        Parameters:
            - host - ip
            - port - 端口
            - uri - 要请求的http接口名
            - **query_args - 请求参数

        Example:
            | get_url | host | port | uri | **query_args |
            | get_url | 192.168.199.149 | 6610 | nginx-status | p1=1,p2=2 |

        Returnd: http://192.168.199.149:6610/nginx-status?p1=1&p2=2
        '''
        url = 'http://{}:{}/{}'.format(host, port, uri)
        if len(query_args) > 0:
            query_str = '&'.join(['{}={}'.format(k, v) for k, v in query_args.items()])
            url = '{}?{}'.format(url, query_str)
        return url

    def to_json(self, body):
        '''
        消息体字符串转json格式

        Parameters:
            - body - 消息体字符串

        Example:
            | to_json | body |
            | to_json | {"key":"value"} |

        Returnd: {"key":"value"}
        '''
        return json.loads(body)

    def head(self, url, headers=None, body=None, xauth=None):
        '''
        发起HEAD请求, 返回(status_code, rsp_body)元组

        Parameters:
            - url - 请求的url
            - headers - HTTP请求头
            - xauth - 消息加密认证信息，格式为(usr, pwd)，如('user', 'pwd')
        Example:
            | head | url | headers | xauth |
            | head | http://192.168.199.149:6610/nginx-status | | |
        '''
        return self._request('HEAD', url, headers, body, xauth)

    def get(self, url, headers=None, body=None, xauth=None):
        '''
        发起GET请求, 返回(status_code, rsp_body)元组

        Parameters:
            - url - 请求的url
            - headers - HTTP请求头
            - xauth - 消息加密认证信息，格式为(usr, pwd)，如('user', 'pwd')
        Example:
            | get | url | headers | xauth |
            | get | http://192.168.199.149:6610/nginx-status | | |
        '''
        return self._request('GET', url, headers, body, xauth)

    def post(self, url, headers=None, body=None, xauth=None):
        '''
        发起POST请求, 返回(status_code, rsp_body)元组

        Parameters:
            - url - 请求的url
            - headers - HTTP请求头
            - body - 请求消息体
            - xauth - 消息加密认证信息，格式为(usr, pwd)，如('user', 'pwd')
        Example:
            | post | url | headers | body | xauth |
            | post | http://192.168.199.149:6610/nginx-status | hello | | |
        '''
        return self._request('POST', url, headers, body, xauth)

    def json_request(self, url, method='POST', json_data=None, headers=None, xauth=None):
        '''
        发起json格式的请求，消息体格式化为json格式， 返回(status_code, rsp_body)元组

        Parameters:
            - url - 请求的url
            - json_data - 请求消息体，json格式
            - headers - HTTP请求头
            - xauth - 消息加密认证信息，格式为(usr, pwd)，如('user', 'pwd')
        Example:
            | json_request | url | method | json_data | headers | xauth |
            | json_request | http://192.168.199.149:6610/nginx-status | POST | {"key":"value"} | | |
        '''
        headers = headers or {}
        headers['Accept'] = headers.get('Accept', 'application/json')
        headers['Content-Type'] = headers.get('Content-Type', 'application/json; charset=UTF-8')

        body = json.dumps(json_data) if type(json_data) in (dict, list) else (json_data or '')
        status_code, rsp_body = self._request(method, url, headers, body, xauth)
        return status_code, json.loads(rsp_body or '')

    def _request(self, method, url, headers=None, body=None, xauth=None):
        '''发起HTTP请求'''
        req = urllib2.Request(url)
        req.get_method = lambda: method

        if headers:
            for k, v in headers.items():
                req.add_header(k, v)

        if xauth:
            uri = self._get_uri(url)
            req.add_header('X-Auth', self._get_xauth(xauth, uri, body))

        logger.debug('Request:\n{}'.format(self._req2str(req, body)))

        status_code, hdrs, rsp_body = -1, {}, None
        try:
            rsp = urllib2.urlopen(req, body)
            status_code, hdrs = rsp.getcode(), rsp.info()
            ctype = hdrs.get('Content-Type', '')
            if ctype.startswith('text') or 'application/json' in ctype:
                rsp_body = rsp.read(MAX_READ_LEN)
            else:
                logger.info('Http client not read http body yet.')
            logger.debug('Response:\n{}\r\n\r\n{}'.format(rsp.info(), rsp_body))
        except urllib2.HTTPError, e:
            logger.error(
                'HTTP request error:\n{} {}\r\n{}'.format(e.code, e.msg, e.hdrs), logtrace=False)
        except Exception, e:
            logger.error('Exception: {}'.format(e), logtrace=True)

        return status_code, rsp_body

    def _req2str(self, req, body):
        hdrs = '\r\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items())
        return '{} {}\r\n{}\r\n\r\n{}'.format(req.get_method(),
                                              req.get_full_url(), hdrs, body or '')

    def _get_xauth(self, xauth, uri, body):
        '''计算md5(usr:body:pwd:uri)'''
        usr, pwd = tuple(xauth)
        m = md5.new()
        m.update('{}:{}:{}:{}'.format(usr, body, pwd, uri))
        return m.hexdigest()

    def _get_uri(self, url):
        '''从url中获取uri'''
        m = re.search(r'[^/](?P<uri>/[^/].*)', url)
        return m.group('uri') if m else ''


if __name__ == '__main__':
    http = HttpClient()
    print http.get_url('192.168.199.149', 6610, 'nginx-status', p1=1, p2=2)
    print http.get('http://192.168.199.149:6610/nginx-status')
