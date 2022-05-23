from GstEncodingGenerator import *

class GstMjpegEncodingGenerator(GstEncodingGenerator):
    source_encoding = "image/jpeg"
    sink_encoding = "image/jpeg"

    @staticmethod
    def generate_pipeline(source, sink, resolution, framerate):
        # get jpegs, filter to correct resolution
        source_caps = Gst.Caps.new_empty()
        source_structure = Gst.Structure.new_from_string(
            f"image/jpeg,width=(int){resolution[0]},height=(int){resolution[1]}"
        )
        source_caps.append_structure(source_structure)

        # filter to tell videorate element what framerate to generate
        rate_caps = Gst.Caps.new_empty()
        rate_structure = Gst.Structure.new_from_string(
            f"image/jpeg,framerate={framerate}/1"
        )
        rate_caps.append_structure(rate_structure)

        rtp_caps = Gst.Caps.new_empty()
        rtp_structure = Gst.Structure.new_from_string(
            "application/x-rtp,encoding=JPEG,payload=26"
        )
        rtp_caps.append_structure(rtp_structure)

        videorate = Gst.ElementFactory.make("videorate")
        rtpjpegpay = Gst.ElementFactory.make("rtpjpegpay")
        pipeline = Gst.Pipeline.new("mjpeg_stream")

        # add all elements to the pipeline
        pipeline.add(source, videorate, rtpjpegpay, sink)

        # filter and link elements
        if not source.link_filtered(videorate, source_caps):
            print(f"Unable to link source to image/jpeg,width=(int){resolution[0]},height=(int){resolution[1]}")   
            return False, None
        if not videorate.link_filtered(rtpjpegpay, rate_caps):
            print(f"Unable to link videorate to rtpjpegpay for mjpeg stream")
            return False, None
        if not rtpjpegpay.link_filtered(sink, rtp_caps):
            print("Unable to link rtpjpegpay to sink for mjpeg stream")
            return False, None
        
        return True, pipeline

    @classmethod
    def get_framerates(cls, caps):
        # 5 fps to 30 fps in increments of 5
        return [5 + 5*i for i in range(6)]

    @staticmethod
    def get_encoding_name():
        return "mjpeg"