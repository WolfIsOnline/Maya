"""Voice Manager"""

import subprocess

from elevenlabs import set_api_key, generate, save

import wolfiebot
from wolfiebot.logger import Logger

log = Logger(__name__, wolfiebot.LOG_LEVEL)


class VoiceManager:
    """Manages Voices"""

    BASE_PATH = "./wolfiebot/content"
    AUDIO_PATH = f"{BASE_PATH}/reply.wav"
    IMAGE_PATH = f"{BASE_PATH}/wolfie.jpg"
    OUTPUT_PATH = f"{BASE_PATH}/reply.mp4"
    VOICE = "odIaJLeGoie42cwJszUp"
    MODEL = "eleven_multilingual_v2"

    def __init__(self, text: str):
        self.text = text
        self.audio = None
        set_api_key(wolfiebot.ELEVENLABS_API_KEY)

    def generate_reply(self):
        """Generate reply from text"""
        if self.text is None or self.text == "":
            log.error(
                'generate_reply():  invalid string. text can\'t be equal "%s"',
                self.text,
            )
            return

        log.debug("generate_reply(): generating speech...")
        self.audio = generate(text=self.text, voice=self.VOICE, model=self.MODEL)
        log.debug(
            'generate_reply(): audio has been generated with "%s" voice using model "%s"',
            self.VOICE,
            self.MODEL,
        )

    def save_audio(self):
        """Save voice into audio file"""
        if self.audio is None:
            return
        save(self.audio, self.AUDIO_PATH)
        log.debug("save_audio(): saved audio to %s", self.AUDIO_PATH)

    def convert_to_video(self):
        """Combines image and audio into video."""
        command = [
            "ffmpeg",
            "-loop",
            "1",
            "-framerate",
            "1",
            "-i",
            self.IMAGE_PATH,
            "-i",
            self.AUDIO_PATH,
            "-c:v",
            "libx264",
            "-tune",
            "stillimage",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-vf",
            "scale=150:150",
            "-pix_fmt",
            "yuv420p",
            "-shortest",
            "-y",
            self.OUTPUT_PATH,
        ]

        subprocess.run(command, check=True)
