#!/usr/bin/env python
#-*- coding: UTF-8 -*-

# 多进程安全的午夜自动切分回滚日志类，
# 解决TimedRotatingFileHandler多进程场景下可能导致先前回滚的存档日志被其他进程的回滚操作覆盖的问题

from logging import FileHandler
import os, re, errno, stat, datetime


class MidnightRotatingFileHandler(FileHandler):
    def __init__(self, filename, backupCount=0, encoding=None, delay=False):
        self._filename = filename
        self._backupCount = backupCount
        self._rotateAt = self._getNextRotateTime()
        self._extMatch = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        FileHandler.__init__(self, filename, 'a', encoding, delay)

    @staticmethod
    def _getNextRotateTime():
        # rotate at midnight
        now = datetime.datetime.now()
        return now.replace(hour=0, minute=0, second=0) + datetime.timedelta(days=1)

    def _open(self):
        now = datetime.datetime.now()
        log_today = "%s.%s" % (self._filename, now.strftime('%Y-%m-%d'))
        try:
            # create the log file atomically
            fd = os.open(log_today, os.O_CREAT|os.O_EXCL, stat.S_IWUSR|stat.S_IRUSR|stat.S_IRGRP|stat.S_IROTH)
            # if coming here, the log file was created successfully
            os.close(fd)
        except OSError as e:
            if e.errno != errno.EEXIST:
                # should not happen
                raise
        self.baseFilename = log_today
        self._makeSymLink(log_today)
        return FileHandler._open(self)

    def emit(self, record):
        now = datetime.datetime.now()
        if now > self._rotateAt:
            # time to rotate
            self._rotateAt = self._getNextRotateTime()
            self.close()
            self._tryCleanFiles()

        FileHandler.emit(self, record)

    def getFilesToDelete(self):
        dirName, baseName = os.path.split(self._filename)
        result = []
        prefix = baseName + "."
        plen = len(prefix)
        for fileName in os.listdir(dirName):
            if not fileName.startswith(prefix): continue
            suffix = fileName[plen:]
            if self._extMatch.match(suffix):
                result.append(os.path.join(dirName, fileName))
        result.sort()
        if len(result) < self._backupCount:
            result = []
        else:
            result = result[:len(result) - self._backupCount]
        return result

    def _tryCleanFiles(self):
        if 0 == self._backupCount:
            return

        for s in self.getFilesToDelete():
            os.remove(s)

    def _makeSymLink(self, srcFile):
        try:
            if os.path.exists(self._filename):
                os.unlink(self._filename)
            os.symlink(srcFile, self._filename)
        except Exception, e:
            print "EXCEPTION: {0}".format(e)

if __name__ == "__main__":
    import logging, time
    log = logging.getLogger('test')
    h = MidnightRotatingFileHandler('/tmp/log/test.log', backupCount=3)
    f = logging.Formatter('%(asctime)s [%(threadName)s] %(message)s -- [%(levelname)s][%(filename)s:%(lineno)d]')
    h.setFormatter( f )
    log.addHandler( h )
    log.setLevel(logging.DEBUG)

    while True:
        log.info('test log: %r', datetime.datetime.now());
        time.sleep(5)
