#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'JiaSong'

import threading
import urllib2
import base64
import uuid
import logger


class RepeatTimer(threading.Thread):
    '''重复运行的定时器'''

    def __init__(self, interval, func):
        super(RepeatTimer, self).__init__()
        self.stopped = threading.Event()
        self.interval = interval
        self.func = func

    def run(self):
        while not self.stopped.wait(self.interval):
            self.func()

    def cancel(self):
        '''取消定时器运行'''
        self.stopped.set()


class MultiThreadDownloader(object):
    '''
    多线程下载器
    当HTTP服务器支持Range时，启用多线程下载，否则单线程下载
    '''

    def __init__(self, url, dstfile, threadnum=5, timeout=30):
        '''
        url - 要下载的文件对应的url
        dstfile - 下载到本地的文件保存路径
        threadnum - 下载线程数
        timeout - 超时时间，HTTP响应超过该时间认为失败，默认30s超时
        '''
        self.url = url
        self.dstfile = dstfile
        self.threadnum = max(int(threadnum), 1)
        self.timeout = int(timeout or 30)
        self.filesize = 0
        self.recv_bytes = 0
        self.auth = None

    def set_base_auth_info(self, auth=None):
        '''
        设置Authorization: Basic认证信息，用于从Jenkins下载需要用户认证的情况
        参数格式: auth = ('ias_dev', 'ias_dev')
        '''
        self.auth = tuple(auth)

    def download(self):
        '''下载文件'''
        try:
            if not self._is_server_support_range():
                self.threadnum = 1  # 采用单线程下载
                logger.info('Server does not support multi-threaded download, use single thread')

            logger.info('Filesize: %d, download thread number: %d' % (self.filesize, self.threadnum))
            self._create_file()

            threads = []
            # 向上取整
            part = (self.filesize - 1) // self.threadnum + 1
            for i in range(self.threadnum):
                start = part * i
                end = min(self.filesize, start + part) - 1
                logger.debug('thread %d download range: %d-%d' % (i, start, end))
                t = threading.Thread(
                    target=self._handler, kwargs={'idx': i,
                                                  'start': start,
                                                  'end': end})
                t.start()
                threads.append(t)

            timer = RepeatTimer(5.0, self._print_progress)
            timer.start()
            for t in threads:
                t.join()
            timer.cancel()
            logger.info('Download progress: 100%%, %d/%d' % (self.recv_bytes, self.filesize))
        except Exception as e:
            logger.error('Download error: {}'.format(e), logtrace=True)
            return False
        return True

    def _request(self, method, url, headers={}, auth=None, timeout=30):
        '''发起HTTP请求'''
        req = urllib2.Request(url)
        req.get_method = lambda: method
        for k, v in headers.items():
            req.add_header(k, v)
        if auth:
            base64str = base64.b64encode('%s:%s' % auth)
            req.add_header("Authorization", "Basic %s" % base64str)
        uuid_str = uuid.uuid1()
        rsp = None
        try:
            logger.debug('Request(uuid:%s):\n%s' % (uuid_str, self._req2str(req)))
            rsp = urllib2.urlopen(req, timeout=timeout)
            logger.debug('Response(uuid:%s):\n%s' % (uuid_str, rsp.info()))
        except urllib2.HTTPError, e:
            logger.error('HTTP request error:\n{} {}\r\n{}'.format(e.code, e.msg, e.hdrs), logtrace=False)
        except Exception, e:
            logger.error('Exception: {}'.format(e), logtrace=True)
        return rsp

    def _is_server_support_range(self):
        '''检查HTTP服务器是否支持多线程下载，并获取文件大小'''
        is_support = False
        rsp = self._request('HEAD', self.url, headers={'Range': 'bytes=0-99'}, auth=self.auth, timeout=self.timeout)
        # 当http服务器返回的Content-Length等于请求的长度时，支持Range
        content_len = int(rsp.info().get('Content-Length', 0))
        is_support = (content_len == 100)
        if is_support:
            self._get_file_size()  # 再获取一次文件大小
        elif content_len > 100:
            self.filesize = content_len  # Content-Length大于请求的长度时，作为文件大小
        return is_support

    def _get_file_size(self):
        '''通过HEAD指令获取文件大小，服务器不返回Content-Length时，文件大小为0'''
        rsp = self._request('HEAD', self.url, auth=self.auth, timeout=self.timeout)
        self.filesize = int(rsp.info().get('Content-Length', 0))

    def _create_file(self):
        '''创建一个和要下载文件一样大小的文件'''
        with open(self.dstfile, "wb") as fp:
            fp.truncate(self.filesize)

    def _handler(self, idx, start, end):
        '''下载处理函数'''
        headers = {}
        remain_size = -1
        if end > start:
            headers['Range'] = 'bytes=%d-%d' % (start, end)
            remain_size = end - start + 1

        rsp = self._request('GET', self.url, headers=headers, auth=self.auth, timeout=self.timeout)

        # 写入文件对应位置
        with open(self.dstfile, "rb+") as fp:
            fp.seek(start)
            while True:
                chunk = rsp.read(512 * 1024)
                data = chunk[:remain_size]
                datalen = len(data)
                self.recv_bytes += datalen
                remain_size -= datalen
                fp.write(chunk)
                if 0 == remain_size:
                    logger.info('Download thread %d finished!' % (idx))
                    break

    def _req2str(self, req):
        return '{} {}\r\n{}\r\n\r\n'.format(req.get_method(),
                                            req.get_full_url(), '\r\n'.join(
                                                '{}: {}'.format(k, v)
                                                for k, v in req.headers.items()))

    def _print_progress(self):
        progress = self.recv_bytes * 100 / self.filesize
        logger.info('Download progress: %2d%%, %d/%d' % (progress, self.recv_bytes, self.filesize))


if __name__ == '__main__':
    import sys, time
    # downloader.py http://10.46.150.101:8080/test.zip test.zip 30
    if len(sys.argv) < 4:
        print 'Usage: %s url dstfile threadnum [timeout]' % sys.argv[0]
        exit(0)

    url, dstfile, threadnum = sys.argv[1:4]
    timeout = sys.argv[4:5] or None
    start = time.time()
    dl = MultiThreadDownloader(url, dstfile, threadnum, timeout)
    dl.set_base_auth_info(('user', 'pwd'))
    dl.download()
    end = time.time()
    print '\ncost time: %ds' % (end - start)
