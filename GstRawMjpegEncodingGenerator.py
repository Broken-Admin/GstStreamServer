from GstEncodingGenerator import *

class GstRawMjpegEncodingGenerator(GstEncodingGenerator):
    source_encoding = "video/x-raw"
    sink_encoding = "image/jpeg"

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
            "application/x-rtp,encoding=JPEG,payload=26"
        )
        rtp_caps.append_structure(rtp_structure)

        if Gst.ElementFactory.find("nvjpegenc"):
            # nvaccelerated option exists
            jpegenc = Gst.ElementFactory.make("nvjpegenc")
        else:
            jpegenc = Gst.ElementFactory.make("jpegenc")

        videorate = Gst.ElementFactory.make("videorate")
        rtpjpegpay = Gst.ElementFactory.make("rtpjpegpay")
        pipeline = Gst.Pipeline.new("mjpeg_stream")

        # add all elements to the pipeline
        for element in [source, videorate, jpegenc, rtpjpegpay, sink]:
            pipeline.add(element)

        # filter and link elements
        if not source.link_filtered(videorate, source_caps):
            print(f"Unable to link source to video/x-raw,width=(int){resolution[0]},height=(int){resolution[1]}")   
            return False, None
        if not videorate.link_filtered(jpegenc, rate_caps):
            print("Unable to convert video/x-raw to image/jpeg for stream.")
            return False, None
        if not jpegenc.link(rtpjpegpay):
            print(f"Unable to link jpegenc to rtpjpegpay for mjpeg stream")
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
        return "raw_to_mjpeg"