from base64 import decode
import gi
gi.require_version("Gst", "1.0")

from Camera import Camera
from gi.repository import Gst, GObject, GLib
from GstEncodingGenerator import GstEncodingGenerator
from GstRawMjpegEncodingGenerator import GstMjpegEncodingGenerator

def main():
    pipeline = Gst.parse_launch(
        "videotestsrc ! decodebin ! autovideosink"
    )

    # start playing
    pipeline.set_state(Gst.State.PLAYING)

    # wait until EOS or Error
    bus = pipeline.get_bus()
    msg = bus.timed_pop_filtered(
        Gst.CLOCK_TIME_NONE,
        Gst.MessageType.ERROR | Gst.MessageType.EOS
    )

    get_devices()

    pipeline.set_state(Gst.State.NULL)


def get_resolutions(caps):
    num_structures = caps.get_size()

    resolutions = []

    for i in range(num_structures):
        structure = caps.get_structure(i)
        width = structure.get_int("width")
        height = structure.get_int("height")

        if width[0] and height[0]:
            resolutions.append((width.value, height.value))
        else:
            print("invalid caps")
        # structure.set("framerate=50/1")
        rate = structure.get_value("framerate")
        rate.value_numerator = 50
        # rate.set_fraction(50, 1)

        Gst.Structure.set_value(structure, "framerate", rate)
        framerate = structure.get_fraction("framerate")
        print(structure.to_string())

    return resolutions

def get_devices():
    test = Gst.DeviceMonitor.new()
    test.add_filter("Video/Source")
    caps = Gst.Caps.new_empty_simple("image/jpeg")

    if test.start():
        devices = test.get_devices()
        return devices
        caps = devices[0].get_caps()
        paths = [device.get_properties().get_string("device.path") for device in devices]
        print(paths)
        print(get_resolutions(caps))
    else:
        print("Unable to initialize device monitor...")

def create_element_pipeline():
    source = Gst.ElementFactory.make("videotestsrc")
    sink = Gst.ElementFactory.make("autovideosink")
    
    pipeline = Gst.Pipeline.new("test-pipeline")

    pipeline.add(source, sink)
    source.link(sink)

    pipeline.set_state(Gst.State.PLAYING)
        # wait until EOS or Error
    bus = pipeline.get_bus()
    msg = bus.timed_pop_filtered(
        10*Gst.SECOND,
        Gst.MessageType.ERROR | Gst.MessageType.EOS
    )

def create_element_mjpeg_stream():
    source = Gst.ElementFactory.make("v4l2src")
    source.set_property("device", "/dev/video0")
    jpegdec = Gst.ElementFactory.make("jpegdec")
    sink = Gst.ElementFactory.make("autovideosink")
    
    # caps_structure = Gst.Structure.new("image/jpeg",
    #                             "width", GObject.TYPE_INT, 1280,
    #                             "height", GObject.TYPE_INT, 720)
    caps_structure = Gst.Structure.new_from_string("image/jpeg,width=(int)1280,height=(int)720")
    source_caps = Gst.Caps.new_empty()
    source_caps.append_structure(caps_structure)
    # source_caps = Gst.Caps.new_full(caps_structure)

    pipeline = Gst.Pipeline.new("test-pipeline")

    pipeline.add(source, jpegdec, sink)

    if not source.link_filtered(jpegdec, source_caps):
        print("unable to link to jpegdec")
    jpegdec.link(sink)

    pipeline.set_state(Gst.State.PLAYING)
        # wait until EOS or Error
    bus = pipeline.get_bus()
    msg = bus.timed_pop_filtered(
        1*Gst.SECOND,
        Gst.MessageType.ERROR | Gst.MessageType.EOS
    )
    
    if msg and msg.type == Gst.MessageType.ERROR:
        err, dbg = msg.parse_error()
        print(err.message, dbg)

    pipeline.set_state(Gst.State.NULL)


def generate_mjpeg_playbin():
    bin = Gst.Bin.new("mjpeg_playbin")
    jpegdec = Gst.ElementFactory.make("jpegdec")
    sink = Gst.ElementFactory.make("autovideosink")
    bin.add(jpegdec)
    bin.add(sink)
    if jpegdec.link(sink):
        pad = jpegdec.get_static_pad("sink")
        ghost_pad = Gst.GhostPad.new("sink", pad)
        ghost_pad.set_active(True)
        bin.add_pad(ghost_pad)
        return bin
    else:
        print("Unable to link jpegdec to autovideosink")


def create_simple_mjpeg_stream():
    source = Gst.ElementFactory.make("v4l2src")
    source.set_property("device", "/dev/video0")
    
    # caps_structure = Gst.Structure.new("image/jpeg",
    #                             "width", GObject.TYPE_INT, 1280,
    #                             "height", GObject.TYPE_INT, 720)
    caps_structure = Gst.Structure.new_from_string("image/jpeg,width=(int)1280,height=(int)720")
    source_caps = Gst.Caps.new_empty()
    source_caps.append_structure(caps_structure)
    # source_caps = Gst.Caps.new_full(caps_structure)

    pipeline = Gst.Pipeline.new("test-pipeline")

    sink = generate_mjpeg_playbin()
    pipeline.add(source, sink)

    if not source.link_filtered(sink.children[0], source_caps):
        print("unable to link to sink")

    pipeline.set_state(Gst.State.PLAYING)
        # wait until EOS or Error
    bus = pipeline.get_bus()
    msg = bus.timed_pop_filtered(
        5*Gst.SECOND,
        Gst.MessageType.ERROR | Gst.MessageType.EOS
    )
    
    if msg and msg.type == Gst.MessageType.ERROR:
        err, dbg = msg.parse_error()
        print(err.message, dbg)

    pipeline.set_state(Gst.State.NULL)


def test_mjpeg_pipeline_generator():
    source = Gst.ElementFactory.make("v4l2src")
    source.set_property("device", "/dev/video0") # 4 is usb camera

    res = (640, 480)
    framerate = 5

    sink = generate_mjpeg_playbin()
    if not sink:
        return

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
        10*Gst.SECOND,
        Gst.MessageType.ERROR | Gst.MessageType.EOS
    )
    
    if msg and msg.type == Gst.MessageType.ERROR:
        err, dbg = msg.parse_error()
        print(err.message, dbg)

    pipeline.set_state(Gst.State.NULL)

def get_device_path(device):
    return device.get_properties().get_string("device.path")

def test_mjpeg_rtp_stream():
    source = Gst.ElementFactory.make("v4l2src")
    source.set_property("device", "/dev/video0") # 4 is usb camera
    
    res = (640, 480)
    framerate = 5

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
        10*Gst.SECOND,
        Gst.MessageType.ERROR | Gst.MessageType.EOS
    )
    
    if msg and msg.type == Gst.MessageType.ERROR:
        err, dbg = msg.parse_error()
        print(err.message, dbg)

    pipeline.set_state(Gst.State.NULL)
    


def get_cameras_by_encoding():
    devices = get_devices()
    encoding_generators = GstEncodingGenerator.__subclasses__()
    cameras = []
    for device in devices:
        caps = device.get_caps()
        path = get_device_path(device)
        encodings = {}
        for generator in encoding_generators:
            encoding = generator.generate_from_caps(caps)

            if encoding is not None:
                encodings[encoding.generator_class.get_encoding_name()] = encoding
        
        if len(encodings) > 0:
            camera = Camera(path, encodings, device)
            cameras.append(camera)
    return cameras

if __name__ == '__main__':
    Gst.init(None)
    test_mjpeg_rtp_stream()



x = {
    "encodings": {
      "mjpeg": {
        "framerates": [
          5,
          10,
          15,
          20,
          25,
          30
        ],
        "resolutions": [
          [
            640,
            480
          ],
          [
            640,
            360
          ],
          [
            352,
            288
          ],
          [
            320,
            240
          ],
          [
            176,
            144
          ],
          [
            1920,
            1080
          ],
          [
            1280,
            720
          ]
        ]
      }
    }
  }
