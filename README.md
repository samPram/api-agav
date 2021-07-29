# api-agav

Selamat datang di API agav untuk VAD(Voice Activity Detector) dari video YouTube

# Required

- virtual environment
- Flask
- youtube-dl
- pydub
- py-webrtcvad
- flask-cors
- ffmpeg

# Usage

1. Install virtual environment

```sh
$ python3 -m venv venv
```

2. Aktifkan virtual environment

```sh
$. venv/bin/activate
```

3. Instal dependensi-dependensi

- Flask
  ```sh
  $ pip install Flask
  ```
- youtube-dl
  ```sh
  $ pip install --upgrade youtube-dl
  ```
- pydub
  ```sh
  $ pip install pydub
  ```
- py-webrtcvad
  ```sh
  $ pip install webrtcvad
  ```
- flask-cors
  ```sh
  $ pip install -U flask-cors
  ```
  ffmpeg
  ```sh
  $ sudo apt install ffmpeg
  ```

4. Jalankan aplikasi

- Development mode
  ```sh
  $ export FLASK_APP=wsgi
  $ export FLASK_ENV=development
  $ flask run
  ```
  server berjalan pada
  `http://localhost:5000/`
- Memberi akses ke luar
  ```sh
  $ flask run --host=0.0.0.0
  ```
  server berjalan pada
  `http://ip_anda:5000/`

3. Penggunaan API

- **POST** - `/urls/` - Download audio dari Youtube yang akan di VAD

  - **url** - **string** link youtube yang ingin diambil audionya. example --> `https://www.youtube.com/watch?v=UVzLd304keA`
  - **sample_rate** - **number**(Optional) isikan dengan sample rate (8000, 16000, 32000, atau 48000) ([dokumentasi](https://github.com/wiseman/py-webrtcvad))
  - **frame** - **number**(Optional) isikan dengan frame (10, 20, atau 30) ([dokumentasi](https://github.com/wiseman/py-webrtcvad))
  - **aggressive** - **number**(Optional) isikan dengan aggresive (1, 2, atau 3) ([dokumentasi](https://github.com/wiseman/py-webrtcvad))
  - **min_duration** - **number**(Optional) durasi minimal dari audio yang akan di download dalam satuan detik. example --> 5
  - **max_duration** - **number**(Optional) durasi maksimal dari audio yang akan di download dalam satuan detik. example --> 40

- **POST** - `/verify` - Memferifikasi audio yang telah terpotong-potong dari VAD
  - **data** - **array of object** - data hasil dari `/urls/` yang akan diverifikasi dengan mengubah nilai isVerified menjadi **true**.
    example -->
  ```sh
  { "data": [
   {
            "isVerified": false,
            "path": "http://localhost:5000/audio/uvzld304kea/chunk-00.wav",
            "title": "chunk-00.wav"
        },
        {
            "isVerified": false,
            "path": "http://localhost:5000/audio/uvzld304kea/chunk-01.wav",
            "title": "chunk-01.wav"
        },
        {
            "isVerified": true,
            "path": "http://localhost:5000/audio/uvzld304kea/chunk-02.wav",
            "title": "chunk-02.wav"
        },
        {
            "isVerified": false,
            "path": "http://localhost:5000/audio/uvzld304kea/chunk-03.wav",
            "title": "chunk-03.wav"
        },
        {
            "isVerified": false,
            "path": "http://localhost:5000/audio/uvzld304kea/chunk-04.wav",
            "title": "chunk-04.wav"
        },
        {
            "isVerified": false,
            "path": "http://localhost:5000/audio/uvzld304kea/chunk-05.wav",
            "title": "chunk-05.wav"
        },
        {
            "isVerified": false,
            "path": "http://localhost:5000/audio/uvzld304kea/chunk-06.wav",
            "title": "chunk-06.wav"
        },
        {
            "isVerified": false,
            "path": "http://localhost:5000/audio/uvzld304kea/chunk-07.wav",
            "title": "chunk-07.wav"
        },
        {
            "isVerified": true,
            "path": "http://localhost:5000/audio/uvzld304kea/chunk-08.wav",
            "title": "chunk-08.wav"
        }
    ]}
  ```
