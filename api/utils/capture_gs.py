#!/usr/bin/python

import sys, signal, getopt
import time
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject, GLib


class StreamCapture:

    SLEEP_INTERVAL = 3

    def __init__(self, stream_url, output_file, type):

        self.pipeline = None
        self.bus = None
        self.message = None
        self.stream_url = stream_url
        self.output_file = output_file
        self.type = type
        self.running  = True
        self.is_live = False
        print('registering signals')
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        self.stop()

    def start(self):
        # initialize GStreamer
        Gst.init(None)

        # build the pipeline

        str_pipeline = "souphttpsrc location={stream_url} is-live=true do-timestamp=true keep-alive=true retries=10 ! " \
            "multipartdemux ! image/jpeg, width={width}, height={height}, framerate={framerate} ! " \
            "matroskamux ! filesink location={location}".format(
                stream_url=self.stream_url,
                width=1280,
                height=720,
                framerate="20/1",
                location=self.output_file
            )

        self.pipeline = Gst.parse_launch(str_pipeline)

        # start playing
        print("CAPTURE_GS - running pipeline {pipeline}".format(pipeline=str_pipeline))

        print("CAPTURE_GS - Setting pipeline to PAUSED ...")
        res = self.pipeline.set_state(Gst.State.PAUSED)

        if res == Gst.StateChangeReturn.NO_PREROLL:
            print("CAPTURE_GS - Pipeline is live and does not need PREROLL ...\n")
            self.is_live = True;

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
                    print("CAPTURE_GS - Error received from element %s: %s" % (
                        msg.src.get_name(), err))
                    print("CAPTURE_GS - Debugging information: %s" % debug)
                    exit(-1)
                elif msg.type == Gst.MessageType.EOS:
                    print("CAPTURE_GS - Got EOS from element {element} ".format(element=msg.src.get_name()))
                    break

        print("CAPTURE_GS - Execution ending ...")
        print("CAPTURE_GS - Setting pipeline to PAUSED ...\n")
        res = self.pipeline.set_state(Gst.State.PAUSED)
        print("CAPTURE_GS - Setting pipeline to READY ...\n")
        res = self.pipeline.set_state(Gst.State.READY)
        print("CAPTURE_GS - Setting pipeline to NULL ...\n")
        res = self.pipeline.set_state(Gst.State.NULL)
        print("CAPTURE_GS - Freeing pipeline ...\n")
        self.pipeline = None
        self.bus = None

    def stop(self):
        print("CAPTURE_GS - EOS on shutdown enabled -- Forcing EOS on the pipeline\n")
        self.pipeline.send_event(Gst.Event.new_eos())


def main(argv):
    output_file = ''
    stream_url = ''
    type = 'PI'
    try:
        opts, args = getopt.getopt(argv, "hs:o:t:")
        if not len(opts):
            raise Exception
    except:
        print('capture_gs.py -s <stream> -o <output> -t <type>')
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print('capture_stream.py -s <stream> -o <outputfile> -t <type>')
            sys.exit()
        elif opt in ("-s", "--stream"):
            stream_url = arg.strip()
        elif opt in ("-o", "--output_file"):
            output_file = arg.strip()
        elif opt in ("-t", "--type"):
            type = arg.strip()

    print('stream_url is ', stream_url)
    print('output_file is ', output_file)
    capture = StreamCapture(stream_url, output_file, type)
    capture.start()


if __name__ == "__main__":
    main(sys.argv[1:])
