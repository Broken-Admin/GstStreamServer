from base64 import decode
import gi
gi.require_version("Gst", "1.0")

from Camera import Camera
from gi.repository import Gst, GObject, GLib
from GstEncodingGenerator import GstEncodingGenerator
from GstRawVP8EncodingGenerator import GstRawVP8EncodingGenerator

# Create a client using the following command: gst-launch-1.0 udpsrc port=11429 ! application/x-rtp,encoding-name=VP8,payload=96 ! rtpvp8depay ! vp8dec ! autovideosink
#,encoding=vp8,payload=96
def test_mjpeg_rtp_stream(timeout_seconds):
    source = Gst.ElementFactory.make("v4l2src")
    source.set_property("device", "/dev/video0") # 4 is usb camera
    
    res = (640, 480)
    framerate = 30

    sink = Gst.ElementFactory.make("udpsink")
    sink.set_property("host", "127.0.0.1")
    sink.set_property("port", 11429)

    pipeline = GstRawVP8EncodingGenerator.generate_pipeline(
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
    test_mjpeg_rtp_stream(15)