from GstEncodingGenerator import *

class GstRawH264EncodingGenerator(GstEncodingGenerator):
    source_encoding = "video/x-h264"
    sink_encoding = "video/x-h264"

    @staticmethod
    def generate_pipeline(source, sink, resolution, framerate):
        # get jpegs, filter to correct resolution
        source_caps = Gst.Caps.new_empty()
        source_structure = Gst.Structure.new_from_string(
            f"video/x-h264,width=(int){resolution[0]},height=(int){resolution[1]}"
        )
        source_caps.append_structure(source_structure)

        # filter to tell videorate element what framerate to generate
        rate_caps = Gst.Caps.new_empty()
        rate_structure = Gst.Structure.new_from_string(
            f"video/x-h264,framerate={framerate}/1"
        )
        rate_caps.append_structure(rate_structure)

        rtp_caps = Gst.Caps.new_empty()
        rtp_structure = Gst.Structure.new_from_string(
            "application/x-rtp,encoding=H264,payload=[26,127]"
        )
        rtp_caps.append_structure(rtp_structure)

        videorate = Gst.ElementFactory.make("videorate")
        rtph264pay = Gst.ElementFactory.make("rtph264pay")
        pipeline = Gst.Pipeline.new("raw_h264_stream")

        # add all elements to the pipeline
        for element in [source, videorate, rtph264pay, sink]:
            pipeline.add(element)

        # filter and link elements
        if not source.link_filtered(videorate, source_caps):
            print(f"Unable to link source to video/x-h264,width=(int){resolution[0]},height=(int){resolution[1]}")   
            return False, None
        if not videorate.link_filtered(rtph264pay, rate_caps):
            print("Unable to convert video/x-h264 to video/x-h264 for stream.")
            return False, None
        if not rtph264pay.link_filtered(sink, rtp_caps):
            print("Unable to link rtph264pay to sink for h264 stream")
            return False, None
        
        return True, pipeline

    @classmethod
    def get_framerates(cls, caps):
        # 5 fps to 30 fps in increments of 5
        return [5 + 5*i for i in range(6)]

    @staticmethod
    def get_encoding_name():
        return "raw_h264"