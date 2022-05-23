from flask import Flask
from flask import request, jsonify
import platform
import StreamManager

app = Flask(__name__)

manager = StreamManager.StreamManager()

@app.route("/cameras")
def get_cameras():
    return jsonify(manager.camera_dictionary)

@app.route("/cameras/start")
def start_camera_stream():
    path = request.args.get("path")
    encoding = request.args.get("encoding")
    resolution = (request.args.get("width"), request.args.get("height"))
    framerate = request.args.get("framerate")
    host = request.remote_addr
    port = request.args.get("port")

    return manager.start_stream(path, encoding, resolution
                        , framerate, host, port)

@app.route("/cameras/stop")
def stop_camera_stream():
    path = request.args.get("path")

    return manager.stop_stream(path)

@app.route("/name")
def get_name():
    return str(platform.node())
