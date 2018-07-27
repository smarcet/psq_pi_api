#!/usr/bin/python

import sys, signal, getopt
import time
import gi

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject, GLib


class StreamBroadcaster:

    SLEEP_INTERVAL = 3

    def __init__(self, stream_url, rtmp_url, stream_key, exercise_id, user_id, type):

        self.pipeline = None
        self.bus = None
        self.message = None
        self.stream_url = stream_url
        self.rtmp_server = rtmp_url
        self.stream_key = stream_key
        self.exercise_id = exercise_id
        self.user_id = user_id
        self.type = type
        self.broadcasting = False
        self.must_stop = False
        print('registering signals')
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        print("exiting ...")
        self.stop()
        sys.exit(0)

    def start(self):
        # initialize GStreamer
        Gst.init(None)
        if self.type == 'PI':
            h264enc = 'omxh264enc'
            h264opt = 'target-bitrate=1000000 control-rate=variable'
        else:
            h264enc = 'x264enc'
            h264opt = 'speed-preset=3 tune=zerolatency bitrate=5000 threads=4 option-string=scenecut=0'

        str_pipeline =  "souphttpsrc location={stream_url} ! multipartdemux ! " \
            "image/jpeg, width={width}, height={height} ! " \
            "jpegdec ! {h264enc} {h264opt} ! video/x-h264,profile=baseline ! " \
            "h264parse ! flvmux ! " \
            "rtmpsink location='{rtmp_server}/live/{stream_key}?exercise_id={exercise_id}&user_id={user_id} live=1'".format(
                stream_url=self.stream_url,
                h264enc=h264enc,
                h264opt=h264opt,
                rtmp_server=self.rtmp_server,
                stream_key=self.stream_key,
                width=1280,
                height=720,
                exercise_id=self.exercise_id,
                user_id=self.user_id
            )

        self.pipeline = Gst.parse_launch(str_pipeline)

        # start playing
        while True:

            self.pipeline.set_state(Gst.State.PLAYING)
            print("pipeline broadcasting")
            self.broadcasting = True
            # wait until EOS or error
            self.bus = self.pipeline.get_bus()

            while self.broadcasting:
                print("broadcasting")
                msg = self.bus.timed_pop_filtered(
                    1000 * Gst.MSECOND,
                    (Gst.MessageType.ERROR
                     | Gst.MessageType.EOS)
                )
                if msg:

                    if msg.type == Gst.MessageType.ERROR:
                        print("broadcast fatal error :/ !!!!")
                        res = msg.parse_error()
                        print(msg.src.name)
                        print(res[1])
                        exit(-1)
                    if msg.type == Gst.MessageType.EOS:
                        print("broadcast error. EOS Reached")

                    print("retrying ...")
                    self.broadcasting = False

                time.sleep(StreamBroadcaster.SLEEP_INTERVAL)

            if self.must_stop:
                print("end of broadcasting")
                break

    def stop(self):
        # free resources
        self.must_stop = True
        self.pipeline.set_state(Gst.State.NULL)


def main(argv):
    rtmp_url = ''
    stream_url = ''
    stream_key = ''
    exercise_id = 0
    user_id = 0
    type = 'PI'
    try:
        opts, args = getopt.getopt(argv, "hs:o:k:e:u:t:")
        if not len(opts):
            raise Exception
    except:
        print("Unexpected error:", sys.exc_info()[0])
        print('streamer_gs.py -s <stream> -o <output> -k <stream_key> -e <exercise> -u <user> -t <type>')
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print('streamer_gs.py -s <stream> -o <output> -k <stream_key> -e <exercise> -u <user> -t <type>')
            sys.exit()
        elif opt in ("-s", "--stream"):
            stream_url = arg
        elif opt in ("-o", "--output"):
            rtmp_url = arg
        elif opt in ("-k", "--stream_key"):
            stream_key = arg
        elif opt in ("-e", "--exercise"):
            exercise_id = arg
        elif opt in ("-u", "--user"):
            user_id = arg
        elif opt in ("-t", "--type"):
            type = arg

    broadcast = StreamBroadcaster(stream_url, rtmp_url, stream_key, exercise_id, user_id, type)
    broadcast.start()


if __name__ == "__main__":
    main(sys.argv[1:])
