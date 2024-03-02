from base64 import decode
import gi
gi.require_version("Gst", "1.0")

from Camera import Camera
from gi.repository import Gst, GObject, GLib
from GstEncodingGenerator import GstEncodingGenerator
from GstRawMjpegEncodingGenerator import GstRawMjpegEncodingGenerator as GstMjpegEncodingGenerator

# Create a client using the following command: gst-launch-1.0 udpsrc port={self.recv_port} ! application/x-rtp,encoding=JPEG,payload=26 ! rtpjpegdepay ! decodebin ! autovideosink

def test_mjpeg_rtp_stream(timeout_seconds):
    source = Gst.ElementFactory.make("v4l2src")
    source.set_property("device", "/dev/video0") # 4 is usb camera
    
    res = (640, 480)
    framerate = 30

    sink = Gst.ElementFactory.make("udpsink")
    sink.set_property("host", "127.0.0.1")
    sink.set_property("port", 11429)

    pipeline = GstMjpegEncodingGenerator.generate_pipeline(
        source, sink,
        res, framerate
    )
    
    if pipeline[0]:
        pipeline = pipeline[1]
    else:
        print("Unable to create pipeline.")
        return

    pipeline.set_state(Gst.State.PLAYING)
    # wait until EOS or Error
    bus = pipeline.get_bus()
    msg = bus.timed_pop_filtered(
        timeout_seconds*Gst.SECOND,
        Gst.MessageType.ERROR | Gst.MessageType.EOS
    )
    
    if msg and msg.type == Gst.MessageType.ERROR:
        err, dbg = msg.parse_error()
        print(err.message, dbg)

    pipeline.set_state(Gst.State.NULL)

if __name__ == '__main__':
    Gst.init(None)
    test_mjpeg_rtp_stream(30)