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
        self.running = True
        self.is_live = False
        self.broadcasting = False
        self.must_stop = False
        print('registering signals')
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        self.stop()

    def start(self):
        # initialize GStreamer
        Gst.init(None)
        if self.type == 'PI':
            h264enc = 'omxh264enc'
            h264opt = 'target-bitrate=8000 control-rate=variable'
        else:
            h264enc = 'x264enc'
            h264opt = 'tune=zerolatency bitrate=8000 threads=4 option-string=scenecut=0'

        str_pipeline =  "souphttpsrc location={stream_url} ! multipartdemux ! " \
            "image/jpeg, width={width}, height={height}, framerate={framerate} ! " \
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
                framerate="10/1",
                exercise_id=self.exercise_id,
                user_id=self.user_id
            )

        self.pipeline = Gst.parse_launch(str_pipeline)

        # start playing
        print("CAPTURE_GS - running pipeline {pipeline}".format(pipeline=str_pipeline))

        print("CAPTURE_GS - Setting pipeline to PAUSED ...")
        res = self.pipeline.set_state(Gst.State.PAUSED)

        if res == Gst.StateChangeReturn.NO_PREROLL:
            print("CAPTURE_GS - Pipeline is live and does not need PREROLL ...\n")
            self.is_live = True

        # wait until EOS or error
        self.bus = self.pipeline.get_bus()
        print("CAPTURE_GS - Setting pipeline to PLAYING ...")
        res = self.pipeline.set_state(Gst.State.PLAYING)

        while self.running:
            msg = self.bus.timed_pop_filtered(
                5 * 1000 * Gst.MSECOND,
                (Gst.MessageType.ANY)
            )
            if msg:
                if msg.type == Gst.MessageType.ERROR:
                    err, debug = msg.parse_error()
                    print("STREAMER_GS - Error received from element %s: %s" % (
                        msg.src.get_name(), err))
                    print("STREAMER_GS - Debugging information: %s" % debug)
                    exit(-1)
                elif msg.type == Gst.MessageType.EOS:
                    print("STREAMER_GS - Got EOS from element {element} ".format(element=msg.src.get_name()))
                    break

        print("STREAMER_GS - Execution ending ...")
        print("STREAMER_GS - Setting pipeline to PAUSED ...\n")
        res = self.pipeline.set_state(Gst.State.PAUSED)
        print("STREAMER_GS - Setting pipeline to READY ...\n")
        res = self.pipeline.set_state(Gst.State.READY)
        print("STREAMER_GS - Setting pipeline to NULL ...\n")
        res = self.pipeline.set_state(Gst.State.NULL)
        print("STREAMER_GS - Freeing pipeline ...\n")
        self.pipeline = None
        self.bus = None

    def stop(self):
        print("STREAMER_GS - EOS on shutdown enabled -- Forcing EOS on the pipeline\n")
        self.pipeline.send_event(Gst.Event.new_eos())


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
            stream_url = arg.strip()
        elif opt in ("-o", "--output"):
            rtmp_url = arg.strip()
        elif opt in ("-k", "--stream_key"):
            stream_key = arg.strip()
        elif opt in ("-e", "--exercise"):
            exercise_id = arg.strip()
        elif opt in ("-u", "--user"):
            user_id = arg.strip()
        elif opt in ("-t", "--type"):
            type = arg.strip()

    broadcast = StreamBroadcaster(stream_url, rtmp_url, stream_key, exercise_id, user_id, type)
    broadcast.start()


if __name__ == "__main__":
    main(sys.argv[1:])