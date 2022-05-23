import gi
gi.require_version("Gst", "1.0")

from gi.repository import Gst, GObject, GLib
from GstEncoding import GstEncoding

class GstEncodingGenerator():
    source_encoding = ""
    sink_encoding = ""

    @classmethod
    def generate_from_caps(cls, caps):
        cap_pattern = Gst.Caps.new_empty_simple(cls.source_encoding)
        matching_caps = caps.intersect(cap_pattern)
        cap_pattern.unref()

        # If no caps match the generator, then return None
        if matching_caps.is_empty():
            matching_caps.unref()
            return None
        
        num_structures = matching_caps.get_size()
        resolutions = []
        framerates = cls.get_framerates(caps)

        for i in range(num_structures):
            structure = matching_caps.get_structure(i)
            width = structure.get_int("width")
            height = structure.get_int("height")

            if width[0] and height[0]:
                res = (width.value, height.value)
                print(res)
                if res not in resolutions:
                    resolutions.append(res)

        matching_caps.unref()

        return GstEncoding(
            cls.source_encoding, cls.sink_encoding,
            resolutions, framerates, cls
        )

    @staticmethod
    def get_encoding_name():
        raise NotImplementedError()

    @staticmethod
    def generate_pipeline(source, sink, resolution, framerate):
        raise NotImplementedError()

    @classmethod
    def get_framerates(cls, caps):
        raise NotImplementedError()



    