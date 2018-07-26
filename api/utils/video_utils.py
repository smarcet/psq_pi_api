import subprocess


def get_video_len(filename):
    pipe = subprocess.Popen(["/usr/local/bin/gst-discoverer-1.0", filename],
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out, err = pipe.communicate()
    for line in out.decode('ascii').split('\n'):
        if line.strip().lower().startswith("duration"):
            str_len =  line.split()[1].split(":")
            hours = int(str_len[0])
            minutes = int(str_len[1])
            seconds = float(str_len[2])
            return {'hours': hours, 'minutes': minutes, 'seconds': seconds}
    return {'hours': 0, 'minutes': 0, 'seconds': 0}