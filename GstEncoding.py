

class GstEncoding:
    def __init__(self, source_encoding, sink_encoding, resolutions, framerates, generator_class):
        self.source_encoding = source_encoding
        self.sink_encoding = sink_encoding
        self.resolutions = resolutions
        self.framerates = framerates
        self.generator_class = generator_class