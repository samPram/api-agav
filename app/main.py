from __future__ import unicode_literals
import flask
from flask import request, jsonify, send_file
from flask.helpers import send_from_directory
import youtube_dl
import os
from pydub import AudioSegment
import collections
import contextlib
import sys
import wave
import webrtcvad
from flask_cors import CORS, cross_origin
import time
from io import BytesIO
import zipfile
import shutil
import glob

app = flask.Flask(__name__, static_url_path='')
CORS(app)
app.config["DEBUG"]=True
app.config["CORS_HEADERS"] = 'Content-Type'

@app.route("/")
def hello_world():
    print(os.path.join(request.base_url, 'audio/'));
    return "<p>Hello, World!</p>"

def read_wave(path):
    """Reads a .wav file.

    Takes the path, and returns (PCM audio data, sample rate).
    """
    with contextlib.closing(wave.open(path, 'rb')) as wf:
        num_channels = wf.getnchannels()
        assert num_channels == 1
        sample_width = wf.getsampwidth()
        assert sample_width == 2
        sample_rate = wf.getframerate()
        assert sample_rate in (8000, 16000, 32000, 48000)
        pcm_data = wf.readframes(wf.getnframes())
        return pcm_data, sample_rate


def write_wave(path, audio, sample_rate):
    """Writes a .wav file.

    Takes path, PCM audio data, and sample rate.
    """
    with contextlib.closing(wave.open(path, 'wb')) as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio)


class Frame(object):
    """Represents a "frame" of audio data."""
    def __init__(self, bytes, timestamp, duration):
        self.bytes = bytes
        self.timestamp = timestamp
        self.duration = duration


def frame_generator(frame_duration_ms, audio, sample_rate):
    """Generates audio frames from PCM audio data.

    Takes the desired frame duration in milliseconds, the PCM data, and
    the sample rate.

    Yields Frames of the requested duration.
    """
    n = int(sample_rate * (frame_duration_ms / 1000.0) * 2)
    offset = 0
    timestamp = 0.0
    duration = (float(n) / sample_rate) / 2.0
    while offset + n < len(audio):
        yield Frame(audio[offset:offset + n], timestamp, duration)
        timestamp += duration
        offset += n


def vad_collector(sample_rate, frame_duration_ms,
                  padding_duration_ms, vad, frames):
    """Filters out non-voiced audio frames.

    Given a webrtcvad.Vad and a source of audio frames, yields only
    the voiced audio.

    Uses a padded, sliding window algorithm over the audio frames.
    When more than 90% of the frames in the window are voiced (as
    reported by the VAD), the collector triggers and begins yielding
    audio frames. Then the collector waits until 90% of the frames in
    the window are unvoiced to detrigger.

    The window is padded at the front and back to provide a small
    amount of silence or the beginnings/endings of speech around the
    voiced frames.

    Arguments:

    sample_rate - The audio sample rate, in Hz.
    frame_duration_ms - The frame duration in milliseconds.
    padding_duration_ms - The amount to pad the window, in milliseconds.
    vad - An instance of webrtcvad.Vad.
    frames - a source of audio frames (sequence or generator).

    Returns: A generator that yields PCM audio data.
    """
    num_padding_frames = int(padding_duration_ms / frame_duration_ms)
    # We use a deque for our sliding window/ring buffer.
    ring_buffer = collections.deque(maxlen=num_padding_frames)
    # We have two states: TRIGGERED and NOTTRIGGERED. We start in the
    # NOTTRIGGERED state.
    triggered = False

    voiced_frames = []
    for frame in frames:
        is_speech = vad.is_speech(frame.bytes, sample_rate)

        sys.stdout.write('1' if is_speech else '0')
        if not triggered:
            ring_buffer.append((frame, is_speech))
            num_voiced = len([f for f, speech in ring_buffer if speech])
            # If we're NOTTRIGGERED and more than 90% of the frames in
            # the ring buffer are voiced frames, then enter the
            # TRIGGERED state.
            if num_voiced > 0.9 * ring_buffer.maxlen:
                triggered = True
                sys.stdout.write('+(%s)' % (ring_buffer[0][0].timestamp,))
                # We want to yield all the audio we see from now until
                # we are NOTTRIGGERED, but we have to start with the
                # audio that's already in the ring buffer.
                for f, s in ring_buffer:
                    voiced_frames.append(f)
                ring_buffer.clear()
        else:
            # We're in the TRIGGERED state, so collect the audio data
            # and add it to the ring buffer.
            voiced_frames.append(frame)
            ring_buffer.append((frame, is_speech))
            num_unvoiced = len([f for f, speech in ring_buffer if not speech])
            # If more than 90% of the frames in the ring buffer are
            # unvoiced, then enter NOTTRIGGERED and yield whatever
            # audio we've collected.
            if num_unvoiced > 0.9 * ring_buffer.maxlen:
                sys.stdout.write('-(%s)' % (frame.timestamp + frame.duration))
                triggered = False
                yield b''.join([f.bytes for f in voiced_frames])
                ring_buffer.clear()
                voiced_frames = []
    if triggered:
        sys.stdout.write('-(%s)' % (frame.timestamp + frame.duration))
    sys.stdout.write('\n')
    # If we have any leftover voiced audio when we run out of input,
    # yield it.
    if voiced_frames:
        yield b''.join([f.bytes for f in voiced_frames])

""" python3 example.py 3 leak-test.wav
3 merupakan params tingkat aggresive
 """

@app.route("/urls/", methods=['POST', 'OPTIONS'])
@cross_origin()
def post_url(rate=8000, aggressive=3, min_duration=0, max_duration=30, frame=10):
    record = request.json

    if "sample_rate" in record:
        rate = record['sample_rate']
    if "aggressive" in record:
        aggressive = record['aggressive']
    if "frame" in record:
        frame = record['frame']
    if "min_duratioin" in record:
        min_duration = record['min_duration']
    if "max_duration" in record:
        max_duration = record['max_duration']

    # Time to miliseconds
    startTime = int(min_duration)*1000
    endTime = int(max_duration)*1000

    SAVE_PATH = os.path.dirname(app.instance_path)+'/downloaded'

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
        'outtmpl': SAVE_PATH+'/%(id)s.%(ext)s',
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([record['url']])
        info = ydl.extract_info(record['url'], download=True)
        filename = info.get('id', None)
    
    # print(type(filename))
    new_filename = str(filename).lower()
    os.rename(SAVE_PATH+'/'+filename+'.wav', SAVE_PATH+'/'+new_filename+'.wav')
    sound = AudioSegment.from_file(SAVE_PATH+'/'+new_filename+".wav", format="wav")

    if startTime > len(sound):
        return jsonify({
            'status': 400,
            'message': 'Minimum duration cannot be greater than the length of the audio duration!'
        }), 400

    if endTime > len(sound):
        return jsonify({
            'status': 400,
            'message': 'Maximum duration cannot be greater than the length of the audio duration!'
        }), 400

    if startTime > endTime: 
        return jsonify({
            'status': 400,
            'message': 'Minimum duration cannot be greater than the maximum duration'
        }), 400

    if endTime < startTime: 
        return jsonify({
            'status': 400,
            'message': 'Maximum duration cannot be less than the minimum duration'
        }), 400

    extract = sound[startTime:endTime]

    file_handle = extract.export("downloaded/convert-"+new_filename+".wav",
                        format="wav",
                        bitrate="192k",
                        parameters=["-ac", "1", "-ar", str(rate)])

    audio, sample_rate = read_wave('downloaded/convert-'+new_filename+'.wav')
    """ end read audio wave """

    """ mendefinisikan aggresive model VAD """
    vad = webrtcvad.Vad(int(aggressive))
    """ generate frame tiap 30 ms, jadi 1 detik ada 33 frames """
    frames = frame_generator(frame, audio, sample_rate)
    frames = list(frames)
    """ end modal VAD """
    segments = vad_collector(sample_rate, frame, 300, vad, frames)
    os.makedirs(os.path.join('audio', new_filename), exist_ok=True)
    for i, segment in enumerate(segments):
        path = 'audio/'+new_filename+'/chunk-%002d.wav' % (i,)
        print(' Writing %s' % (path,))
        write_wave(path, segment, sample_rate)

    data = []
    dir_output = os.listdir('audio/'+new_filename+'/')
    for audio_output in sorted(dir_output):
        data.append({
            'title': audio_output,
            # 'path': os.path.dirname(app.instance_path)+'/audio/'+new_filename+'/'+audio_output,
            'path': request.host_url+'audio/'+new_filename+'/'+audio_output,
            'isVerified': False
        })

    response = {
        'status': 200,
        'message': 'Success',
        'data': data
    }
    
    return jsonify(response), 200

@app.route('/audio/<path:filename>')
def get_audio(filename):
    print(os.path.dirname(app.instance_path))
    return send_from_directory(os.path.join(request.host_url, 'audio/'), filename)


@app.route('/verify/', methods=['POST', 'OPTIONS'])
@cross_origin()
def post_vefify():
    record = request.json

    last_endpoint = record['data'][0]['path'].rfind('/')
    endpoint = record['data'][0]['path'][0:last_endpoint+1]

    for i in range(len(record['data'])):
    # print(record['data'][i])
        if record['data'][i]['isVerified'] == False:
            # print('ok')
            os.remove(record['data'][i]['path'])

    timestr = time.strftime("%Y%m%d-%H%M%S")
    fileName = "data_audio_{}.zip".format(timestr)
    memory_file = BytesIO()
    
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(endpoint):
            # print(root)
            for file in files:
                # print(file)
                zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), os.path.join(endpoint, '..')))

    memory_file.seek(0)
    return send_file(memory_file, attachment_filename=fileName, as_attachment=True)

@app.after_request
def after_verify(response):
    method = request.method
    path = request.path
    if path == '/verify/' and method == 'POST':

        record = request.json
        # REMOVE FILE IN DOWNLOADED
        PATH = os.path.dirname(app.instance_path)+'/downloaded'
        item = record['data'][0]['path'].split('/')
        id_file = item[len(item)-2]
        print(id_file)
        
        os.chdir(PATH)
        for file in glob.glob('*'+id_file+'.wav'):
            # print(file)
            os.remove(PATH+'/'+file)

        # REMOVE FOLDER CHUNK
        last_endpoint = record['data'][0]['path'].rfind('/')
        endpoint = record['data'][0]['path'][0:last_endpoint+1]
        shutil.rmtree(endpoint)
    
    return response
