# api-agav

Selamat datang di API agav untuk VAD(Voice Activity Detector) dari video YouTube

# Required
* virtual environment
* Flask
* youtube-dl
* pydub
* py-webrtcvad
* flask-cors

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
  * Flask
    ```sh
    $ pip install Flask
    ```
  * youtube-dl
    ```sh
    $ pip install --upgrade youtube-dl
    ```
  * pydub
    ```sh
    $ pip install pydub
    ```
  * py-webrtcvad
    ```sh
    $ pip install webrtcvad
    ```
  * flask-cors
    ```sh
    $ pip install -U flask-cors
    ```
4. Jalankan aplikasi
  ```sh
  $ python3 app.py
  ```
3. Enjoy API agav
