#!/usr/bin/python

import sys, signal, getopt
import time
import gi

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject, GLib


class StreamCapture:

    SLEEP_INTERVAL = 3

    def __init__(self, stream_url, output_file):

        self.pipeline = None
        self.bus = None
        self.message = None
        self.stream_url = stream_url
        self.output_file = output_file
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

        # build the pipeline

        str_pipeline = "souphttpsrc location={stream_url} is-live=true do-timestamp=true keep-alive=true retries=10 ! " \
            "multipartdemux ! image/jpeg, width={width}, height={height} ! " \
            "matroskamux ! filesink location={location}".format(
                stream_url=self.stream_url,
                width=1280,
                height=720,
                location=self.output_file
            )

        self.pipeline = Gst.parse_launch(str_pipeline)

        # start playing

        self.pipeline.set_state(Gst.State.PLAYING)
        print("pipeline playing")
        # wait until EOS or error
        self.bus = self.pipeline.get_bus()

        while True:
            msg = self.bus.timed_pop_filtered(
                100 * Gst.MSECOND,
                (Gst.MessageType.ERROR
                 | Gst.MessageType.EOS)
            )
            if msg:
                print("got error message")
                sys.exit(-1)
            time.sleep(StreamCapture.SLEEP_INTERVAL)

    def stop(self):
        # free resources
        self.pipeline.set_state(Gst.State.NULL)


def main(argv):
    output_file = ''
    stream_url = ''

    try:
        opts, args = getopt.getopt(argv, "hs:o:", ["stream=", "output_file="])
        if not len(opts):
            raise Exception
    except:
        print('capture_gs.py -s <stream> -o <output>')
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print('capture_stream.py -s <stream> -o <outputfile>')
            sys.exit()
        elif opt in ("-s", "--stream"):
            stream_url = arg
        elif opt in ("-o", "--output_file"):
            output_file = arg

    print('stream_url is ', stream_url)
    print('output_file is ', output_file)
    capture = StreamCapture(stream_url, output_file)
    capture.start()


if __name__ == "__main__":
    main(sys.argv[1:])
