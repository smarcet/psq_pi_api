#!/usr/bin/python

import sys, signal
import time
import gi

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject, GLib


class StreamCapture:

    def __init__(self):

        self.pipeline = None
        self.bus = None
        self.message = None
        self.stream_url = 'http://192.168.2.121:8081'
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
        # self.pipeline = Gst.parse_launch(
        #     "souphttpsrc location={stream_url} is-live=true do-timestamp=true keep-alive=true retries=10 ! "
        #     "multipartdemux ! image/jpeg, width={width}, height={height}, framerate={framerate} ! jpegdec ! "
        #     "jpegenc quality={quality} ! avimux ! filesink location={location}".format(
        #         stream_url=self.stream_url,
        #         width=1280,
        #         height=720,
        #         framerate="10/1",
        #         quality=50,
        #         location="output.avi"
        #     )
        # )

        self.pipeline = Gst.parse_launch(
            "souphttpsrc location={stream_url} is-live=true do-timestamp=true keep-alive=true retries=10 ! "
            "multipartdemux ! image/jpeg, width={width}, height={height}, framerate={framerate} ! "
            "matroskamux ! filesink location={location}".format(
                stream_url=self.stream_url,
                width=1280,
                height=720,
                framerate="10/1",
                location="output.mkv"
            )
        )

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
            time.sleep(1000)

    def stop(self):
        # free resources
        self.pipeline.set_state(Gst.State.NULL)


if __name__ == "__main__":
    capture = StreamCapture()
    capture.start()
