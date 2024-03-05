from GstEncodingGenerator import *

class GstRawVP8EncodingGenerator(GstEncodingGenerator):
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
            "application/x-rtp,encoding=VP8,payload=96"
        )
        rtp_caps.append_structure(rtp_structure)

        videorate = Gst.ElementFactory.make("videorate")
        rtpvp8pay = Gst.ElementFactory.make("rtpvp8pay")
        pipeline = Gst.Pipeline.new("mjpeg_stream")

        jpegdec = Gst.ElementFactory.make("jpegdec")
        vp8enc = Gst.ElementFactory.make("vp8enc")

        tee = Gst.ElementFactory.make("tee")
        rtpqueue = Gst.ElementFactory.make("queue")
        aviqueue = Gst.ElementFactory.make("queue")
        avimux = Gst.ElementFactory.make("avimux")
        filesink = Gst.ElementFactory.make("filesink")

        device_path = source.get_property("device")
        file_directory = f"./recordings{device_path}"
        os.makedirs(file_directory, exist_ok=True)
        id = len(os.listdir(file_directory))
        file_path = f"{file_directory}/{id}.mp4"

        filesink.set_property("location", file_path)

        # add all elements to the pipeline
        for element in [source, videorate, tee, rtpqueue, jpegdec, vp8enc, rtpvp8pay, sink, aviqueue, avimux, filesink]:
            pipeline.add(element)

        # filter and link elements
        if not source.link_filtered(videorate, source_caps):
            print(f"Unable to link source to image/jpeg,width=(int){resolution[0]},height=(int){resolution[1]}")   
            return False, None
        if not videorate.link_filtered(tee, rate_caps):
            print(f"Unable to link videorate to tee for vp8 stream")
            return False, None
        if not tee.link(rtpqueue):
            print("Unable to link tee to rtpqueue.")
            return False, None
        if not rtpqueue.link(jpegdec):
            print("Unable to link rtpqueue to jpegdec.")
            return False, None
        if not jpegdec.link(vp8enc):
            print("Unable to link jpegdec to vp8enc.")
            return False, None
        if not vp8enc.link(rtpvp8pay):
            print("Unable to link vp8enc to rtpvp8pay.")
            return False, None
        if not rtpvp8pay.link_filtered(sink, rtp_caps):
            print("Unable to link rtpvp8pay to sink for vp8 stream")
            return False, None
        
        if not tee.link(aviqueue):
            print("Unable to link tee to aviqueue.")
            return False, None
        if not aviqueue.link(avimux):
            print("Unable to link aviqueue to avimux.")
            return False, None
        if not avimux.link(filesink):
            print("Unable to link avimux to filesink.")
            return False, None
        
        return True, pipeline

    @classmethod
    def get_framerates(cls, caps):
        # 5 fps to 30 fps in increments of 5
        return [5 + 5*i for i in range(6)]

    @staticmethod
    def get_encoding_name():
        return "raw_mjpeg"