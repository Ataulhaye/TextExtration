import json
import os
import random
import re
import string
from this import d
import time
from urllib.parse import urljoin
import bs4
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.utils import ChromeType
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from pathlib import Path
all_visited_links = {}
links_queue = []
extracted_video_links = []

class WebSpider:
    """Provides all functionality to extract text from ZDF or RD"""
    browser: webdriver.Chrome = None
    url = ''
    browser_mode: bool
    recursive: bool
    tag_a = 'a'
    htmlTag_p = 'p'
    htmlTag_t = 'title'
    htmlTag_btn = 'button'
    htmlTag_nav = 'nav'
    htmlTag_ul = 'ul'
    htmlTag_li = 'li'
    htmlTag_span = 'span'
    htmlTag_img = 'img'
    htmlTag_h1 = 'h1'
    htmlTag_h2 = 'h2'
    htmlTag_h3 = 'h3'
    htmlTag_h4 = 'h4'
    htmlTag_h5 = 'h5'
    video_tag = 'video'
    figure_tag = 'figure'
    audio_tag = 'audio'
    filter = [htmlTag_p, tag_a, htmlTag_nav, htmlTag_ul, htmlTag_img, figure_tag]
    aFilter = [htmlTag_span, htmlTag_img]
    soup: bs4.BeautifulSoup = None
    html_content = None
    output_file_name = ''
    data_saving_Directory = ''
    crawl_portal: bool

    def __init__(self, url, browser_mode=True, recursive=False, crawl_portal=False, data_saving_Directory= 'DataOutput'):
        self.browser_mode = browser_mode
        self.recursive = recursive
        self.enable_drivers()
        self.url = url
        self.output_file_name = self.get_filename()
        self.run_browser()
        self.get_soup_content()
        self.crawl_portal = crawl_portal
        self.data_saving_Directory = data_saving_Directory

    def run_browser(self):
        self.browser.get(self.url)
        self.accept_cookies()
        time.sleep(2) 
        try:
            #click_video = self.browser.find_element(By.XPATH, "//*[@class='b-heute-video']")
            click_videos = self.browser.find_elements(By.XPATH, "//*[@class='b-heute-video']")
            for video in click_videos:
                video.click()
                time.sleep(2)                         
        except Exception as e:
            print("An Error occurred while trying to click", e)

    def accept_cookies(self):
        time.sleep(2)       
        try:
            cookie_btn = self.browser.find_element(By.XPATH, '//*[@id="onetrust-accept-btn-handler"]')
            cookie_btn.click()
            time.sleep(2)
        except Exception as e:
            print("An Error occurred while trying to click cookie button", e)
            
        
    def quit_browser(self):
        self.browser.delete_all_cookies()
        self.browser.quit()

    def enable_drivers(self):
        options = Options()
        options.headless = self.browser_mode
        self.browser = webdriver.Chrome(
            options=options,
            service=Service(ChromeDriverManager(chrome_type=ChromeType.GOOGLE).install()))

    def get_filename(self):
        return '__'.join(self.url.split('.')[1:])

    def get_soup_content(self):
        self.html_content = self.browser.page_source
        self.soup = bs4.BeautifulSoup(self.html_content, features="lxml")
        # self.writeDataToFile(soup)

    def scrape_data(self):
        try:           
            all_content = self.parse_html_content()
            self.write_data_to_json_file(all_content, self.output_file_name)
            all_visited_links.update({self.url: True})
            if self.url in links_queue:
                links_queue.remove(self.url)
            self.quit_browser()
            
            if self.recursive:
                self.get_sublinks(all_content)
                #ffor testation reduce the number of links
                #l = {}
                #cnt = 0
                #for key, link in global_links_dictionary.items():
                    #cnt = cnt + 1
                    #if cnt <= 3:   
                        #l.update({key:link})
                #links = l
                for link in links_queue:
                    spider = WebSpider(link, browser_mode=self.browser_mode, recursive=self.recursive, crawl_portal=self.crawl_portal, data_saving_Directory=self.data_saving_Directory)
                    spider.scrape_data()           
            #self.write_video_links()
                     
        except Exception as e:           
            print(f"An exception occurred while parsing and writing data: {e}")
        finally:
              self.quit_browser()
              
    def write_video_links(self):
        file_name = WebSpider.remove_backslashes(f"{self.output_file_name}_VideoLinks.text")
        for video in extracted_video_links:
            with open(file_name, mode='a', encoding='utf-8') as f:
                f.write(video + '\n')
        return file_name        
            
    
    def get_sublinks(self, content:dict):
        temp = {}
        for key, value in content.items():
            if type(value) is str:
                if key.startswith("LnkS") and len(value) > 1:
                    temp.update({value: "link"})
            else:
                for key, val in value.items():
                    if key.startswith("LnkS") and len(val) > 1:
                        temp.update({val: "link"})
                    
        for key, value in temp.items():
            if not self.crawl_portal:
                if self.url in key:
                    visited = all_visited_links.get(key)
                    if visited is None or visited is False:
                        links_queue.append(key)
            else:
                visited = all_visited_links.get(key)
                if visited is None or visited is False:
                    links_queue.append(key)
       
        
    # all parse methods must return a string that store all the data
    def parse_html_content(self):

        page_content = self.remove_duplicate_tags()

        all_content = {"Title": self.get_text(self.soup.title)}

        for s in page_content:
            match s.name:
                case self.tag_a:
                    all_content.update(self.parse_a(s))
                case self.htmlTag_p:
                    all_content.update(WebSpider.get_paragraph(s))
                case self.htmlTag_ul:
                    all_content.update(self.parse_unordered_list(s))
                case self.htmlTag_nav:
                    all_content.update(self.parse_nav(s))
                case self.htmlTag_img:
                    all_content.update(self.parse_img(s))
                case self.figure_tag:
                    all_content.update(self.parse_figure(s))

                    
        # all_content = WebSpider.remove_duplicate_values_dictionary(all_content)
        return all_content

    def remove_duplicate_tags(self):
        page_content = self.soup.find_all(self.filter)
        for dup in page_content:
            match dup.name:

                case self.htmlTag_ul:
                    a_list_ul = dup.find_all(self.tag_a)
                    for a_ul in a_list_ul:
                        if a_ul in page_content:
                            page_content.remove(a_ul)
                        else:
                            print("nested a in ul")
                    img_list = dup.find_all(self.htmlTag_img)
                    for img in img_list:
                        if img in page_content:
                            page_content.remove(img)
                        else:
                            print("nested Image in ul / li")

                case self.htmlTag_nav:
                    a_list_nav = dup.find_all(self.tag_a)
                    for a_nav in a_list_nav:
                        if a_nav in page_content:
                            page_content.remove(a_nav)
                        else:
                            print("nested a in nav")
                    ul_list = dup.find_all(self.htmlTag_ul)
                    for ul in ul_list:
                        if ul in page_content:
                            page_content.remove(ul)
                        else:
                            print("nested ul in nav")
                    # remove img tag that appears also with in tag nav, thats why duplicate
                    img_nav = dup.find_all(self.htmlTag_img)
                    for imn in img_nav:
                        if imn in page_content:
                            page_content.remove(imn)
                        else:
                            print("nested img in nav")
                # remove img tag that appears also with in tag a, thats why duplicate
                case self.tag_a:
                    img_lis = dup.find_all(self.htmlTag_img)
                    for im in img_lis:
                        if im in page_content:
                            page_content.remove(im)
                        else:
                            print("nested a in ul")
                # remove ul thoes appear in nav and also in page-content
                case self.htmlTag_ul:
                    ul_in_nav = dup.find_all(self.htmlTag_nav)
                    for ul_in in ul_in_nav:
                        if ul_in in page_content:
                            page_content.remove(ul_in)
                        else:
                            print("nested ul in in nav")

                            # parent = parent_check()
        page_content = list(dict.fromkeys(page_content))
        return page_content

    def parse_figure(self, tag: bs4.element.Tag):
        data = {}
        video = tag.find(self.video_tag)
        if video is not None:
            try:
                source = video['src']
                key = WebSpider.generate_random_key()
                v = f"VideoLnkS_{key}_VideoLnkE"
                video_data = {"video-source":source}
                text = WebSpider.get_text(tag).strip()
                video_data.update({"video-description":text})
                data.update({v: video_data})
                if source not in extracted_video_links:
                    extracted_video_links.append(source)
            except Exception as e:
                print("An Error occured while trying to read the video source", e)
        return data
    
    def parse_nav(self, nav_tag: bs4.element.Tag):
        data = {}
        uls = {}
        nav_key = '-'.join(nav_tag.text.split())
        further_tags = nav_tag.find_all(self.htmlTag_ul)
        further_tags = list(dict.fromkeys(further_tags))
        for ul in further_tags:
            if ul.name == self.htmlTag_ul:
                o_list = self.parse_nested_unordered_list(ul)
                uls.update(o_list)
        uls = WebSpider.remove_duplicate_values_dictionary(uls)
        data.update({nav_key: uls})

        return data

    def parse_unordered_list(self, tag: bs4.element.Tag):
        # for testing
        # mydivs = tag.find_all("li", {"class": "central-footer-item"})
        # if len(mydivs) > 0:
        # print(mydivs)
        data = {}
        lis = tag.find_all(self.htmlTag_li)
        lis = list(dict.fromkeys(lis))
        ord_list = {}
        for s in lis:
            if s.name == self.htmlTag_li:
                ord_list.update(self.parse_nested_ordered_list(s))
        data.update({'-'.join(tag.text.split()): ord_list})

        return data

    def parse_nested_unordered_list(self, tag: bs4.element.Tag):
        lis = tag.find_all(self.htmlTag_li)
        lis = list(dict.fromkeys(lis))
        ord_list = {}
        for s in lis:
            if s.name == self.htmlTag_li:
                ord_list.update(self.parse_nested_ordered_list(s))
        return ord_list

    def parse_nested_ordered_list(self, tag: bs4.element.Tag):
        data = {}
        further_tags = tag.find_all(self.tag_a)
        further_tags = list(dict.fromkeys(further_tags))
        for s in further_tags:
            if s.name == self.tag_a:
                data.update(self.get_href_data(s))
        return data

    def parse_a(self, atag: bs4.element.Tag):
        """
        If arg tag contains single tag: a hrefData will be returned
        If arg tag contains further tags, href- and Img- will be returned _
        """
        tag_a_data = {}
        img_in_a = {}
        title = ""

        tag_a_data.update(self.get_href_data(atag))

        further_tags = atag.find_all(self.aFilter)

        for sub_a in further_tags:
            match sub_a.name:
                case self.htmlTag_span:
                    title += WebSpider.get_text(sub_a)
                case self.htmlTag_img:
                    img_in_a = WebSpider.parse_nested_img(sub_a)
                    tag_a_data.update({title: img_in_a})

        return tag_a_data

    def get_href_data(self, href):
        """
        "Inner Text": getText(s), "Title":getTitle(s), "href":getLink(s)       
        """
        # return {"Inner Text": self.getText(s), "Title":self.getTitle(s), "href":self.getLink(s)}
        key = WebSpider.generate_random_key()
        aHref = {"{}__{}".format(f"LnkS_{key}_LnkE", WebSpider.get_text(href).strip()): self.get_link(href)}
        # aHref = {"{}-{}".format("L", NewsExtractor.get_text(href).strip()): self.get_link(href)}
        return aHref

    def get_link(self, tag):
        try:
            href = tag.get('href')
            if len(href) > 1:
                href = urljoin(self.url, href)
            return href
            # return href
        except:
            print("An exception occurred")
            
    
    def write_data_to_json_file(self, current_content, outputfile_name):
        file_name = WebSpider.remove_backslashes(f"{outputfile_name}.json")
        save_folder = self.make_directory()
        complete_file_name = os.path.join(save_folder, file_name) 
        with open(complete_file_name, mode='w', encoding='utf-8') as f:
            f.write(json.dumps(current_content, ensure_ascii=False, indent=4))
            
    def make_directory(self):
        try:
            print(f"Making Directory")
            dir_path = Path(Path().resolve(), self.data_saving_Directory)
            if dir_path.exists():
                print(f"Following directory already exists: {dir_path}")
            else:
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"Following directory has been created: {dir_path}")
            
            return dir_path
        except OSError as exc:
            print('Directory has not been created!', exc.args)
            raise RuntimeError from exc
        
    @staticmethod
    def remove_duplicate_values_dictionary(dictionary):
        temp = {}
        for key, value in dictionary.items():
            if type(value) is str:
                temp.update({value: key})
            else:
                temp.update({key: value})
        dictionary = {}
        for key, value in temp.items():
            if type(value) is str:
                dictionary.update({value: key})
            else:
                dictionary.update({key: value})
        return dictionary
    
    @staticmethod
    def generate_random_key(key_length=10):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=key_length))

    @staticmethod
    def parse_img(img):
        img_data = {}
        src = ''
        txt = ''
        dat_src = ''
        try:
            # data-src
            src = img['src']
            txt = img['alt']
            dat_src = img['data-src']
        except:
            print("An exception occurred in Img Tag")
        # return {"{}-{}".format("Alt Text", txt).strip():txt,"Src": src}
        if src:
            img_data.update({"Src": src})
        if dat_src:
            img_data.update({'data-src': dat_src})
        # return {"Alt Text": txt, "Src": src, 'data-src': dat_src}
        img_key = WebSpider.generate_random_key()
        imDat = {"{}__{}".format(f"ImgS_{img_key}_ImgE", txt): img_data}
        return imDat

    @staticmethod
    def parse_nested_img(img):
        img_data = {}
        src = ''
        txt = ''
        dat_src = ''
        try:
            # data-src
            src = img['src']
            txt = img['alt']
            dat_src = img['data-src']
        except:
            print("")
            #print("An exception occurred in Img Tag")
        # return {"{}-{}".format("Alt Text", txt).strip():txt,"Src": src}
        if src:
            img_data.update({"Src": src})
        if txt:
            img_data.update({"Alternating Text": txt})
        if dat_src:
            img_data.update({'data-src': dat_src})
        # return {"Alt Text": txt, "Src": src, 'data-src': dat_src}
        return img_data

    @staticmethod
    def get_paragraph(para: bs4.element.Tag):
        content = {}
        text = para.getText().strip()
        if text is not None:
            key = WebSpider.generate_random_key()
            p = f"PS_{key}_PE"
            content.update({p:{"paragraph-content": text}})
        return content

    @staticmethod
    def get_text(tag: bs4.element.Tag):
        """
        Gets the text from, span, h1, h2, h3, ..
        """
        try:
            text = tag.text
            return text.strip()
        except:
            print("An exception occurred")
        
    @staticmethod
    def remove_backslashes(string):
        rep = {"/": "", "\\": ""}  # define desired replacements here
        rep = dict((re.escape(k), v) for k, v in rep.items())
        pattern = re.compile("|".join(rep.keys()))
        filtered_string = pattern.sub(lambda m: rep[re.escape(m.group(0))], string)
        return filtered_string

    def parse_subpages(links:list):
        for link in links:
            ne = WebSpider(link)
            content = ne.scrape_data()
            return content

