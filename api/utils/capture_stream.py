#!/usr/bin/python

import sys, getopt, signal
import cv2
import logging

class Daemon:

    def __init__(self, stream_url, output_file):
        self.kill_now = False
        self.output_file = output_file
        self.stream_url = stream_url
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        self.kill_now = True

    def run(self):
        try:
            cap = cv2.VideoCapture(self.stream_url)
            logger = logging.getLogger(__name__)
            print(__name__)
            fps = cap.get(cv2.CAP_PROP_FPS)
            logger.info("get fps {fps} from source".format(fps=fps))
            size = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                    int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
            fps = 20.0
            size = (1280, 720)
            four_cc = cv2.VideoWriter_fourcc(*'MJPG')

            out = cv2.VideoWriter(self.output_file, four_cc, fps, size, True)

            if not out.isOpened():
                raise Exception

            while cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    out.write(frame)
                else:
                    break
                if self.kill_now:
                    break
        except:
            print("Unexpected error:", sys.exc_info()[0])
            sys.exit(-1)
        finally:
            # Release everything if job is finished
            cap.release()
            out.release()
            cv2.destroyAllWindows()


def main(argv):
    output_file = ''
    stream_url = ''

    try:
        opts, args = getopt.getopt(argv, "hs:o:", ["sStream=", "ofile="])
        if not len(opts):
            raise Exception
    except:
        print('capture_stream.py -s <streamurl> -o <outputfile>')
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print('capture_stream.py -s <streamurl> -o <outputfile>')
            sys.exit()
        elif opt in ("-s", "--sStream"):
            stream_url = arg
        elif opt in ("-o", "--ofile"):
            output_file = arg

    print('StreamUrl is ', stream_url)
    print('Output file is ', output_file)

    daemon = Daemon(stream_url.strip(" "), output_file.strip(" "))
    daemon.run()


if __name__ == "__main__":
    main(sys.argv[1:])
