from enum import Enum


class AudioSource(str, Enum):
    uploaded_file = "uploaded_file"
    in_app_recording = "in_app_recording"
