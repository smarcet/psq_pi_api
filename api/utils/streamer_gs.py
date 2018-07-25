#!/usr/bin/python

import sys, signal
import time
import gi

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject, GLib


class StreamBroadcaster:

    def __init__(self):

        self.pipeline = None
        self.bus = None
        self.message = None
        self.stream_url = 'http://192.168.2.121:8081'
        self.rtmp_server = 'rtmp://35.206.98.247'
        self.stream_key = '3edff929197192cf95b6f4b7ce19ca3f'
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
        self.pipeline = Gst.parse_launch(
            "souphttpsrc location={stream_url} ! multipartdemux ! image/jpeg, width={width}, height={height}, framerate={framerate} ! "
            "jpegdec ! {h264enc} {h264opt} ! video/x-h264,profile=baseline ! "
            "h264parse ! flvmux ! rtmpsink location='{rtmp_server}/live/{stream_key}?exercise_id={exercise_id}&user_id={user_id} live=1'".format(
                stream_url=self.stream_url,
                #h264enc='omxh264enc',
                h264enc='x264enc',
                #h264opt='target-bitrate=1000000 control-rate=variable',
                h264opt='speed-preset=3 tune=zerolatency bitrate=5000 threads=4 option-string=scenecut=0',
                rtmp_server=self.rtmp_server,
                stream_key=self.stream_key,
                width=1280,
                height=720,
                framerate="10/1",
                exercise_id=1,
                user_id=3
            )
        )

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
                print("waiting 5 secs ....")
                time.sleep(5)

            if self.must_stop:
                print("end of broadcasting")
                break

    def stop(self):
        # free resources
        self.must_stop = True
        self.pipeline.set_state(Gst.State.NULL)


if __name__ == "__main__":
    broadcast = StreamBroadcaster()
    broadcast.start()
