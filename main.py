# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
from email.mime import base
import subprocess
import urllib.request
from moviepy.editor import VideoFileClip
from pathlib import Path
from VideoToText import VideoToText
from WebSpider import WebSpider


def extract_news(base_url = 'https://www.zdf.de/nachrichten/politik',data_saving_Directory="Nachrichten-Politik",video_extract = False):

    news_extractor = WebSpider(url=base_url, recursive=True, data_saving_Directory=data_saving_Directory)
    news_extractor.scrape_data()
    video_link_file = news_extractor.write_video_links()
    
    video_links = []
    if video_extract:
        try:
            file = open(video_link_file, 'r')
            video_links = file.readlines()
        except Exception as e:
            print(e)
    
        for video in video_links:
            video_to_text(video.strip())
        
    


def extract_news_test():
    #base_url = 'https://www.zdf.de/nachrichten/politik'
    #base_url = 'https://www.tagesschau.de/'
    #base_url = 'https://www.zdf.de/nachrichten/politik/oel-terminal-kasachstan-ukraine-krieg-russland-100.html'
    #base_url = 'https://www.zdf.de/nachrichten/politik/atomkraftwerk-saporischschja-krim-ukraine-krieg-russland-100.html'
    #base_url = 'https://www.zdf.de/nachrichten/politik/masala-interview-ukraine-krieg-russland-100.html'
    #base_url = 'https://www.zdf.de/nachrichten/politik/grossbritannien-johnson-krise-abgrund-100.html'
    #news_extractor = WebSpider(url=base_url, recursive=True, data_saving_Directory="nachrichten-politik-atomkraftwerk")
    
    base_url = 'https://www.tagesschau.de/newsticker/liveblog-ukraine-mittwoch-149.html'
    news_extractor = WebSpider(url=base_url, recursive=True, data_saving_Directory="tagesschau-newsticker1")
    news_extractor.scrape_data()
    video_link_file = news_extractor.write_video_links()
    
    video_links = []
    try:
        file = open(video_link_file, 'r')
        video_links = file.readlines()
    except Exception as e:
        print(e)
    
    for video in video_links:
        video_to_text(video.strip())

def video_to_text(video_link):
    
    video_text = VideoToText(video_link)
    try:
        video_text.video_to_audio()
        video_text.split_audio_file_on_silence()
        video_text.read_text_parallel()
    except Exception as e:   
        print("The following Error occurred while converting speech to text:", e)
    finally:
        video_text.delete_directory()
    

def video_to_text_test():
    #video_link = 'https://nrodlzdf-a.akamaihd.net/none/zdf/22/06/220609_1900_clip_3_h19/1/220609_1900_clip_3_h19_2128k_p18v15.webm'
    video_link = 'https://nrodlzdf-a.akamaihd.net/none/zdf/22/08/220810_x06_nif_akw_sf_onl/1/220810_x06_nif_akw_sf_onl_2128k_p18v15.webm'
    
    
    video_text = VideoToText(video_link)
    try:
        video_text.video_to_audio()
        # video_text.split_audio_file()
        video_text.split_audio_file_on_silence()
        #video_text.read_text()
        video_text.read_text_parallel()
    except Exception as e:   
        print("The following Error occurred:", e)
    finally:
        video_text.delete_directory() 
       


def video_to_text_test_lib():
    url = 'https://www.ardmediathek.de/video/jagd-auf-dagobert/trailer-jagd-auf-dagobert/rbb-fernsehen/Y3JpZDovL3JiYi1vbmxpbmUuZGUvamFnZC1hdWYtZGFnb2JlcnQvMjAyMi0wNi0wNlQwMDowMDowMF8wZWQ1Y2Q5Ni02YTZjLTRkNTItOWY5ZS0zNmY2YjkyNWZlZjcvamFnZC1hdWYtZGFnb2JlcnRfMjAyMjA2MDZfdHJhaWxlcl9qYWdk'
    url ="https://media.tagesschau.de/video/2022/0616/TV-20220616-1932-5000.webs.h264.mp4"
    mp4file = urllib.request.urlopen(url)
    name = "test.mp4"
    #name = "test.m4v"
    #name = "test.mpeg4"
    with open(name, "wb") as handle:
        handle.write(mp4file.read())
    p = Path(name).resolve()
    p1 = Path('test.wav').resolve()
    #cmdline = ['avconv', '-i', p, '-vn', '-f', 'wav', p1]
    #subprocess.call(cmdline)
    #command = "ffmpeg -i test.mp4 -ab 160k -ac 2 -ar 44100 -vn audio.wav"
    #command = f"ffmpeg -i {p} -ab 160k -ac 2 -ar 44100 -vn test.wav"
    #command = f"ffmpeg -i {p} -ab 160k -ac 2 -ar 16000 -vn {p1}"
    command = f"ffmpeg -i {p} -ab 160k -ac 2 -ar 44100 -vn {p1}"
    subprocess.call(command, shell=True)



# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    #video_to_text()
    #extract_news()
    #extract_news_test()
    video_to_text_test()
