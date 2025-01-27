import os
import urllib.request

import flask

# initialize our Flask application and the Keras model
from utils.dirs import verify_folder
from utils.sound import SoundUtils
from utils.utils import get_root
from webserver.loader import predict_class_audio, MODEL_TYPE, MODEL_NUM
from pydub import AudioSegment

from webserver.storage.factory import StorageFactory

app = flask.Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(get_root(), "webserver", "uploads")

verify_folder(app.config['UPLOAD_FOLDER'])


def convert_mp3(current_file):
    # files
    dst = current_file + ".wav"

    # convert wav to mp3
    sound = AudioSegment.from_mp3(current_file)
    sound.export(dst, format="wav")

    return dst


@app.route("/", methods=["GET"])
def index():
    return "Welcome to the AccentTrainer Keras REST API!"


def save_file_from_request(request):
    """
    Get a file object in the request and save it locally for predicition
    :param request:
    :return:
    """
    file = request.files.get('file')

    if not file:
        full_path = None
        file_uploaded = False
        return file_uploaded, full_path

    storage = StorageFactory.local()
    full_path = storage.save_file(file, root=app.config['UPLOAD_FOLDER'])

    file_uploaded = True

    return file_uploaded, full_path


def download_remote_file(file_path_url):
    name = file_path_url.split("/")[-1]
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], name)
    current_file = urllib.request.urlretrieve(file_path_url, save_path)
    return save_path


def get_prediction(sound_file):
    mfcc = SoundUtils.segment_request_file(sound_file)
    prediction = predict_class_audio(mfcc)
    return str(prediction)


@app.route("/bot", methods=["POST"])
def bot():
    response = {"success": False}

    if flask.request.method == "POST":
        data = flask.request.get_json()
        if "path" not in data:
            return "missing path"
        print(data)

        try:
            sound_file_path = download_remote_file(data["path"])

            prediction = get_prediction(sound_file_path)

            # indicate that the request was a success
            response["success"] = True
            response["predictions"] = prediction
            print(response)

        except Exception as e:
            return flask.jsonify({"error": e})

    # upload prediction to cloud storage
    storage = StorageFactory.cloud()
    storage.upload_prediction(source=sound_file_path,
                              model_type=MODEL_TYPE,
                              model_num=MODEL_NUM,
                              status=response["predictions"])

    return flask.jsonify(response)


@app.route("/predict", methods=["POST"])
def predict():
    # initialize the data dictionary that will be returned from the
    # view
    response = {"success": False}

    # ensure an image was properly uploaded to our endpoint
    if flask.request.method == "POST":

        # make sure we received a file in the request
        if not flask.request.files.get("file"):
            response["error"] = "missing file key: 'file'"
            return flask.jsonify(response)

        # read the sound file
        status, sound_file = save_file_from_request(flask.request)

        prediction = get_prediction(sound_file)
        response["predictions"] = prediction

        # indicate that the request was a success
        response["success"] = True

        # upload prediction to cloud storage
        storage = StorageFactory.cloud()
        storage.upload_prediction(source=sound_file,
                                  model_type=MODEL_TYPE,
                                  model_num=MODEL_NUM,
                                  status=response["predictions"])

    # return the data dictionary as a JSON response
    return flask.jsonify(response)


# if this is the main thread of execution first load the model and
# then start the server
if __name__ == "__main__":
    print(("* Loading Keras model and Flask starting server..."
           "please wait until server has fully started"))
    app.run()
