from GstHelperFunctions import *

class StreamManager:
    def __init__(self):
        self.cameras = generate_camera_list()
        self.camera_dictionary = {}
        self.__camera_dictionary = {}
        self.streams = {}

        for camera in self.cameras:
            encodings = {}
            for title, encoding in camera.encodings.items():
                if len(encoding.resolutions) == 0:
                    continue

                encodings[title] = {
                    "resolutions": encoding.resolutions,
                    "framerates": encoding.framerates
                }
            data = {
                "encodings" : encodings
            }

            self.camera_dictionary[camera.path] = data
            self.__camera_dictionary[camera.path] = camera

    # start stream
    def start_stream(self, path, encoding, resolution, framerate, host, port):
        if path in self.streams:
            self.stop_stream(path)

        camera = self.__camera_dictionary[path]
        encodingGenerator = camera.encodings[encoding].generator_class
        
        source = camera.generate_source()
        sink = Gst.ElementFactory.make("udpsink")
        print(host, camera, source)

        sink.set_property("host", host)
        sink.set_property("port", int(port))
        sink.set_property("sync", False)

        pipeline = encodingGenerator.generate_pipeline(source, sink, resolution, framerate)

        if pipeline[0]:
            pipeline = pipeline[1]
            pipeline.set_state(Gst.State.PLAYING)
            self.streams[path] = pipeline
            return "Success!"
        else:
            return "Unable to create pipeline."


    # pause stream

    # stop stream
    def stop_stream(self, path):
        if path in self.streams:
            pipeline = self.streams.pop(path)

            pipeline.set_state(Gst.State.NULL)

            return "Stopped!"
        
        else:
            return "Stream was not running!"
        