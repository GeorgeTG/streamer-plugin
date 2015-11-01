#!/usr/bin/env python2
from multiprocessing import Process
from threading import Thread, Event
from subprocess import Popen
import time
import tempfile
import os
import errno
import livestreamer

class StreamerThread(Thread):
    def __init__(self, stream):
        super(StreamerThread, self).__init__()
        tmpdir = tempfile.mkdtemp()
        self._close_event = Event()
        self._pipe_ready = Event()
        self.filename = os.path.join(tmpdir, 'vlc_stream')
        self._stream = stream

    def run(self):
        try:
            os.mkfifo(self.filename)
            print("Made pipe at %s" % self.filename)
            with open(self.filename, 'w') as pipe:
                self._pipe_ready.set()
                with self._stream.open() as steam:
                    while not self._close_event.is_set():
                        data = steam.read(1024)
                        pipe.write(data)
                    else:
                        print("Stopped")
        except OSError as e:
            self.clean_up()
            print ("Error[%s]" % e.errno)
        except IOError as io_error:
            self.clean_up()
            if io_error.errno == errno.EPIPE:
                print ("Streaming programm closed. Bye!")
            else:
                print ("Error[%s]" % e.errno)
        except Exception as ex:
            print("Error: " + str(ex))

    def clean_up(self):
        if os.path.isfile(self.filename):
            os.remove(self.filename)

    def get_fifo_path(self):
        return self.filename

    def wait_for_stream(self, timeout):
        print("waiting for pipe")
        self._pipe_ready.wait(timeout)

    def stop(self):
        self._close_event.set()

def start_streaming(stream, timeout):
    """
    Start streaming from the specified stream,
    waiting Timeout seconds until the pipe is ready.
    """
    #start the streaming thread
    thread = StreamerThread(stream)
    thread.daemon = True
    thread.start()

    thread.wait_for_stream(timeout)
    with open(thread.get_fifo_path()) as pipe:
        vlc = Popen(["/usr/bin/vlc", "-"], stdin = pipe)

        while vlc.poll() is None:
            time.sleep(0.2)
            continue
        else:
            print("VLC closed. Cya!")
            thread.stop()

class LivestreamerError(Exception):
    def __init__(self, message):
        super(LivestreamerError, self).__init__(message)

class LivestreamerAsync(object):
    def __init__(self, url):
        self._streams = LivestreamerAsync.get_available_quality(url)

    def start_streamer(self, quality):
        if not self._streams:
            return False
        if quality not in self._streams.keys():
            raise LivestreamerError("Bad quality selection: %s" % quality)

        p = Process(target = start_streaming, args=(self._streams[quality], 5))
        p.start()
        return True

    def get_quality(self):
        if not self._streams:
            return None
        return self._streams.keys()

    @staticmethod
    def start_streamer_async(self, url, quality):
        streams = LivestreamerAsync.get_available_quality(url)
        if not streams:
            return False
        p = Process(target = start_streaming, args=(streams[quality],))
        p.start()
        return True


    @staticmethod
    def get_available_quality(url):
        try:
            streams = livestreamer.streams(url)
            return streams
        except livestreamer.NoPluginError as err:
            raise LivestreamerError("No plugin for this url")
        except livestreamer.PluginError as err:
            raise LivestreamerError(str(err))
        except Exception as ex:
            raise LivestreamerError(str(ex))

