from GstEncodingGenerator import *

class GstH264EncodingGenerator(GstEncodingGenerator):
    source_encoding = "video/x-raw"
    sink_encoding = "video/x-h264"

    @staticmethod
    def generate_pipeline(source, sink, resolution, framerate):
        # get video, filter to correct resolution
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
            h264enc.set_property("insert-sps-pps", 1)
            h264enc.set_property("MeasureEncoderLatency", 1)
            h264enc.set_property("maxperf-enable", 1)
            h264enc.set_property("bitrate", 500000)
            h264enc.set_property("preset-level", 1)
            h264enc.set_property("iframeinterval", int(framerate))
            videorate = Gst.ElementFactory.make("videorate")
            nvvidconv = Gst.ElementFactory.make("nvvidconv")
            rtpqueue = Gst.ElementFactory.make("queue")
            rtph264pay = Gst.ElementFactory.make("rtph264pay")

            tee = Gst.ElementFactory.make("tee")
            mp4queue = Gst.ElementFactory.make("queue")
            h264parse = Gst.ElementFactory.make("h264parse")
            mp4mux = Gst.ElementFactory.make("mp4mux")
            filesink = Gst.ElementFactory.make("filesink")

            device_path = source.get_property("device")
            file_directory = f"./recordings{device_path}"
            os.makedirs(file_directory, exist_ok=True)
            id = len(os.listdir(file_directory))
            file_path = f"{file_directory}/{id}.mp4"

            filesink.set_property("location", file_path)

            pipeline = Gst.Pipeline.new("h264_stream")

            for element in [source, videorate, nvvidconv, h264enc, tee, rtpqueue, rtph264pay, sink, mp4queue, h264parse, mp4mux, filesink]:
                pipeline.add(element)
            
            # filter and link elements
            if not source.link_filtered(videorate, source_caps):
                print(f"Unable to link source to video/x-raw,width=(int){resolution[0]},height=(int){resolution[1]}")   
                return False, None
            if not videorate.link_filtered(nvvidconv, rate_caps):
                print("Unable to convert video/x-raw to video/x-raw(NVMM) for stream.")
                return False, None
            if not nvvidconv.link(h264enc):
                print("Unable to link nvvidconv to nvv4l2h264nec for h264 stream")
                return False, None
            if not h264enc.link(tee):
                print(f"Unable to link h264enc to tee for h264 stream")
                return False, None
            if not tee.link(rtpqueue):
                print("Unable to link tee to rtpqueue.")
                return False, None
            if not rtpqueue.link(rtph264pay):
                print("Unable to link rtpqueue to rtph264pay.")
                return False, None
            if not rtph264pay.link_filtered(sink, rtp_caps):
                print("Unable to link rtph264pay to sink for h264 stream")
                return False, None

            if not tee.link(mp4queue):
                print("Unable to link tee to mp4queue.")
                return False, None
            if not mp4queue.link(h264parse):
                print("Unable to link mp4queue to h264parse.")
                return False, None
            if not h264parse.link(mp4mux):
                print("Unable to link h264parse to mp4mux.")
                return False, None
            if not mp4mux.link(filesink):
                print("Unable to link mp4mux to filesink.")
                return False, None
            
            return True, pipeline
        elif Gst.ElementFactory.find("v4l2h264enc"):
            # nvaccelerated option exists
            h264enc = Gst.ElementFactory.make("v4l2h264enc")
            # h264enc.set_property("insert-sps-pps", 1)
            h264enc.set_property("MeasureEncoderLatency", 1)
            h264enc.set_property("maxperf-enable", 1)
            h264enc.set_property("bitrate", 500000)
            h264enc.set_property("preset-level", 1)
            h264enc.set_property("iframeinterval", int(framerate))
            videorate = Gst.ElementFactory.make("videorate")
            vidconv = Gst.ElementFactory.make("videoconvert")
            rtph264pay = Gst.ElementFactory.make("rtph264pay")
            pipeline = Gst.Pipeline.new("h264_stream")

            for element in [source, videorate, nvvidconv, h264enc, rtph264pay, sink]:
                pipeline.add(element)
            
            # filter and link elements
            if not source.link_filtered(videorate, source_caps):
                print(f"Unable to link source to video/x-raw,width=(int){resolution[0]},height=(int){resolution[1]}")   
                return False, None
            if not videorate.link_filtered(nvvidconv, rate_caps):
                print("Unable to convert video/x-raw to video/x-raw(NVMM) for stream.")
                return False, None
            if not vidconv.link(h264enc):
                print("Unable to link videoconvert to v4l2h264nec for h264 stream")
                return False, None
            if not h264enc.link(rtph264pay):
                print(f"Unable to link h264enc to rtph264pay for h264 stream")
                return False, None
            if not rtph264pay.link_filtered(sink, rtp_caps):
                print("Unable to link rtph264pay to sink for h264 stream")
                return False, None
            
            return True, pipeline
        else:
            h264enc = Gst.ElementFactory.make("x264enc")
            h264enc.set_property("tune", "zerolatency")
            videorate = Gst.ElementFactory.make("videorate")
            videoconvert = Gst.ElementFactory.make("videoconvert")
            rtpqueue = Gst.ElementFactory.make("queue")
            rtph264pay = Gst.ElementFactory.make("rtph264pay")

            tee = Gst.ElementFactory.make("tee")
            mp4queue = Gst.ElementFactory.make("queue")
            h264parse = Gst.ElementFactory.make("h264parse")
            mp4mux = Gst.ElementFactory.make("mp4mux")
            filesink = Gst.ElementFactory.make("filesink")

            device_path = source.get_property("device")
            file_directory = f"./recordings{device_path}"
            os.makedirs(file_directory, exist_ok=True)
            id = len(os.listdir(file_directory))
            file_path = f"{file_directory}/{id}.mp4"

            filesink.set_property("location", file_path)

            pipeline = Gst.Pipeline.new("h264_stream")

            vidconv_caps = Gst.Caps.new_empty()
            vidconv_structure = Gst.Structure.new_from_string(
                f"video/x-raw,format=I420"
            )
            vidconv_caps.append_structure(vidconv_structure)

            # add all elements to the pipeline
            for element in [source, videorate, videoconvert, h264enc, rtph264pay, sink, tee, rtpqueue, mp4queue, h264parse, mp4mux, filesink]:
                pipeline.add(element)

            # filter and link elements
            if not source.link_filtered(videorate, source_caps):
                print(f"Unable to link source to video/x-raw,width=(int){resolution[0]},height=(int){resolution[1]}")   
                return False, None
            if not videorate.link_filtered(videoconvert, rate_caps):
                print(f"Unable to link videorate to videoconvert for stream.")
                return False, None
            if not videoconvert.link_filtered(h264enc, vidconv_caps):
                print("Unable to convert video/x-raw to video/x-h264 for stream.")
                return False, None
            if not h264enc.link(tee):
                print(f"Unable to link h264enc to tee for h264 stream")
                return False, None
            if not tee.link(rtpqueue):
                print("Unable to link tee to rtpqueue.")
                return False, None
            if not rtpqueue.link(rtph264pay):
                print("Unable to link rtpqueue to rtph264pay.")
                return False, None
            if not rtph264pay.link_filtered(sink, rtp_caps):
                print("Unable to link rtph264pay to sink for h264 stream")
                return False, None

            if not tee.link(mp4queue):
                print("Unable to link tee to mp4queue.")
                return False, None
            if not mp4queue.link(h264parse):
                print("Unable to link mp4queue to h264parse.")
                return False, None
            if not h264parse.link(mp4mux):
                print("Unable to link h264parse to mp4mux.")
                return False, None
            if not mp4mux.link(filesink):
                print("Unable to link mp4mux to filesink.")
                return False, None
            
            return True, pipeline

    @classmethod
    def get_framerates(cls, caps):
        # 5 fps to 30 fps in increments of 5
        return [5 + 5*i for i in range(6)]

    @staticmethod
    def get_encoding_name():
        return "h264"