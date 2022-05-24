import gi

gi.require_version("Gst", "1.0")

from gi.repository import Gst, GObject, GLib

import Camera
import GstEncodingGenerator, GstRawMjpegEncodingGenerator, GstMjpegEncodingGenerator, GstRawH264EncodingGenerator, GstH264EncodingGenerator
import GstH264FromMjpegEncodingGenerator

def __get_devices():
    monitor = Gst.DeviceMonitor.new()
    monitor.add_filter("Video/Source")

    if monitor.start():
        devices = monitor.get_devices()

        monitor.stop()
        return devices
    else:
        print("Unable to initialize device monitor...")

def generate_camera_list():
    Gst.init(None)

    devices = __get_devices()
    encoding_generators = GstEncodingGenerator.GstEncodingGenerator.__subclasses__()
    
    cameras = []
    for device in devices:
        print(device.get_properties().get_string("device.path"))
        caps = device.get_caps()
        encodings = {}
        for generator in encoding_generators:
            print(generator.get_encoding_name())
            encoding = generator.generate_from_caps(caps)

            if encoding is not None:
                encodings[encoding.generator_class.get_encoding_name()] = encoding
        
        if len(encodings) > 0:
            camera = Camera.Camera(encodings, device)
            cameras.append(camera)
    return cameras