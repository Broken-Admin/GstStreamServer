from GstEncodingGenerator import *

class GstH264EncodingGenerator(GstEncodingGenerator):
    source_encoding = "video/x-raw"
    sink_encoding = "video/x-h264"

    @staticmethod
    def generate_pipeline(source, sink, resolution, framerate):
        # get jpegs, filter to correct resolution
        source_caps = Gst.Caps.new_empty()
        source_structure = Gst.Structure.new_from_string(
            f"video/x-raw,width=(int){resolution[0]},height=(int){resolution[1]}"
        )
        source_caps.append_structure(source_structure)

        # filter to tell videorate element what framerate to generate
        rate_caps = Gst.Caps.new_empty()
        rate_structure = Gst.Structure.new_from_string(
            f"video/x-raw,framerate={framerate}/1"
        )
        rate_caps.append_structure(rate_structure)

        rtp_caps = Gst.Caps.new_empty()
        rtp_structure = Gst.Structure.new_from_string(
            "application/x-rtp,encoding=H264,payload=[26,127]"
        )
        rtp_caps.append_structure(rtp_structure)

        if Gst.ElementFactory.find("nvv4l2h264enc"):
            # nvaccelerated option exists
            h264enc = Gst.ElementFactory.make("nvv4l2h264enc")
        else:
            h264enc = Gst.ElementFactory.make("xh264enc")

        videorate = Gst.ElementFactory.make("videorate")
        rtph264pay = Gst.ElementFactory.make("rtph264pay")
        pipeline = Gst.Pipeline.new("mjpeg_stream")

        # add all elements to the pipeline
        for element in [source, videorate, h264enc, rtph264pay, sink]:
            pipeline.add(element)

        # filter and link elements
        if not source.link_filtered(videorate, source_caps):
            print(f"Unable to link source to video/x-raw,width=(int){resolution[0]},height=(int){resolution[1]}")   
            return False, None
        if not videorate.link_filtered(h264enc, rate_caps):
            print("Unable to convert video/x-raw to video/x-h264 for stream.")
            return False, None
        if not h264enc.link(rtph264pay):
            print(f"Unable to link h264enc to rtph264pay for h264 stream")
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
        return "h264"