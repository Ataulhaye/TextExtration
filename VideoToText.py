import multiprocessing
import os
import speech_recognition as sr
from moviepy.editor import VideoFileClip
from google.cloud import speech
from pydub import AudioSegment
from pathlib import Path
import shutil
from os import walk
from multiprocessing import Pool
from google.cloud import speech

# https://cloud.google.com/speech-to-text/docs/libraries
# https://pypi.org/project/SpeechRecognition/2.1.3/
from pydub.silence import split_on_silence


class VideoToText:
    processing_language = ''
    video_link = ''

    audio_file_name = ''
    audio_file_fullname = ''
    audio_file_path = ''

    audio_formate = ''
    chunks_dir_name = ''
    chunks_dir_path = ''

    min_silence_length = 500
    silence_threshold = -36
    keep_silence_len = 400

    audio_file = False
    cnt = 0

    def __init__(self, video_source, audio_formate='wav', language="de-DE", min_silence_len=500, silence_thresh=-36,
                 keep_silence=400):
        self.processing_language = language
        self.min_silence_length = min_silence_len
        self.keep_silence_len = keep_silence
        self.silence_threshold = silence_thresh
        self.video_link = video_source
        self.audio_file_name = self.get_audiofile_name()
        self.audio_formate = audio_formate
        self.chunks_dir_name = '{}_{}'.format('AudioChunks', self.audio_file_name)
        self.set_pathfile()
        self.chunks_dir_path = self.make_directory()

    def s(self):
        self.video_to_audio()
        self.split_audio_file_on_silence()
        self.read_text_parallel()
        
    def get_audiofile_name(self):
        name = self.video_link.split('/')[-1].strip().split('.')[0]
        return name

    def set_pathfile(self):
        self.audio_file_fullname = f'{self.audio_file_name}.{self.audio_formate}'
        self.audio_file_path = Path(self.audio_file_fullname).resolve()

    def video_to_audio(self):
        print(f"Starting converting video to audio")
        video_clip = VideoFileClip(self.video_link)
        # self.audio_file_fullname = f'{self.audio_file_name}.{self.audio_formate}'
        video_clip.audio.write_audiofile(self.audio_file_fullname)
        # self.audio_file_path = Path(self.audio_file_fullname).resolve()
        self.audio_file = True
        print(f"Video to audio conversion is finished")

    def make_directory(self):
        try:
            print(f"Making Directory")
            dir_path = Path(Path().resolve(), self.chunks_dir_name)
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Directory has been created")
            return dir_path
        except OSError as exc:
            print('Directory has not been created!', exc.args)
            raise RuntimeError from exc

    def split_audio_file(self):
        audio = AudioSegment.from_file(self.audio_file_path, format=self.audio_formate)
        counter = 5
        while counter <= audio.duration_seconds:
            ten_seconds = counter * 1000
            segment = audio[counter:ten_seconds]
            counter = counter + 10
            segment.export(
                '{}/{}__{}.{}'.format(self.chunks_dir_path, self.audio_file_name, (counter // 5), self.audio_formate),
                format=self.audio_formate)

    def split_audio_file_on_silence(self):
        print(f"Started audio splitting on silence")
        sound_file = AudioSegment.from_file(self.audio_file_path, format=self.audio_formate)
        audio_chunks = split_on_silence(sound_file, min_silence_len=self.min_silence_length,
                                        silence_thresh=self.silence_threshold, keep_silence=self.keep_silence_len)
        total_chunks = len(audio_chunks)
        print(f"Audio splitting finished.It splitted in: {total_chunks} chunks")

        for i, chunk in enumerate(audio_chunks):
            chunk.export(
                '{}/{}__{}.{}'.format(self.chunks_dir_path, self.audio_file_name, str(i), self.audio_formate),
                format=self.audio_formate)
        print(f"Exported: {total_chunks} chunks to the specified directory")

    def delete_directory(self):
        try:
            print(f"Deleting directory")
            shutil.rmtree(self.chunks_dir_path)  # Delete an entire directory tree
            if self.audio_file:
                self.audio_file_path.unlink()  # delete the single file
            print(f"Directory has been deleted!")
        except OSError as exc:
            print('Directory has Not been deleted!', exc)
            raise RuntimeError from exc

    def read_text(self):
        files = next(walk(self.chunks_dir_path), (None, None, []))[2]

        print(f"Start converting speech to text")
        cnt = 0
        for file in files:
            try:
                r = sr.Recognizer()
                audio_path = '{}/{}'.format(self.chunks_dir_path, file)
                print(f"Started processing audio chunk: {file}")
                with sr.AudioFile(audio_path) as source:
                    audio_file = r.record(source)
                result = r.recognize_google(audio_file, language=self.processing_language)

                with open('recognized.txt', mode='a', encoding='utf-8') as f:
                    f.write(result + '\n')
                print(f"Finished processing audio chunk: {file}")
            except sr.UnknownValueError:
                cnt = cnt + 1
                print(f"Google Speech Recognition could not understand the following chunk: {file}")
            except sr.RequestError:
                print(f"Could not request results from Google Speech Recognition service: {file}")
        print(f"Could not extract text from {cnt} audio chunks")
        print(f"Finished converting speech to text")

    def read_text_parallel(self):
        try:
            files = next(walk(self.chunks_dir_path), (None, None, []))[2]
            #pool = Pool(len(files))
            #pool = Pool(self.pools)
            pool = Pool(multiprocessing.cpu_count())
            recognized_text = pool.map(self.func, files)
            # print(output)
            #text = " ".join(recognized_text)
            self.write_text_file(" ".join(recognized_text))            
        except Exception as e:
            print("An error occurred while parallelisation", e)

    def write_text_file(self, text):
        with open(f'{self.audio_file_name}_VideoScript.txt', mode='w', encoding='utf-8') as f:
            f.write(text)
    
    def func(self, file):
        result = ""
        try:
            r = sr.Recognizer()
            audio_path = '{}/{}'.format(self.chunks_dir_path, file)
            print(f"Started processing audio chunk: {file}")
            with sr.AudioFile(audio_path) as source:
                audio_file = r.record(source)
            result = r.recognize_google(audio_file, language=self.processing_language)

            #with open('recognized.txt', mode='a', encoding='utf-8') as f:
                #f.write(result + '\n')
            print(f"Finished processing audio chunk: {file}")
        except sr.UnknownValueError:
            self.cnt = self.cnt + 1
            print(f"Google Speech Recognition could not understand the following chunk: {file}")
        except sr.RequestError:
            print(f"Could not request results from Google Speech Recognition service: {file}")

        if self.cnt > 0:
            print(f"Could not extract text from {self.cnt} audio chunks")
        print(f"Finished converting speech to text")
        return result
