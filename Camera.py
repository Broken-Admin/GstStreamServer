import gi
gi.require_version("Gst", "1.0")

from gi.repository import Gst, GObject, GLib

class Camera:
    def __init__(self, encodings, device):
        self.encodings = encodings
        self.device = device
        self.path = self.__get_path()

    def generate_source(self):
        source = Gst.ElementFactory.make("v4l2src")
        source.set_property("device", self.path)
        source.set_property("io-mode", 4)

        return source

    def __get_path(self):
        return self.device.get_properties().get_string("device.path")