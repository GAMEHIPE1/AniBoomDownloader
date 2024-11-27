import requests
from fake_useragent import FakeUserAgent
from bs4 import BeautifulSoup
import json
import statistics
import xml.etree.ElementTree as ET
ua = FakeUserAgent()
namespace = {'dash': 'urn:mpeg:dash:schema:mpd:2011'}
class AnimeGO:
    def __init__(self):
        try: import lxml;self.LXML_USE = 'lxml'
        except ImportError:self.LXML_USE = 'html.parser'
    
    def download_video(self,link,episodes = 1,res = 'middle',dowmload_only_audio = False):
        '''Скачиваетвидео'''
        self.headers = {'accept': 'application/json, text/javascript, */*; q=0.01','accept-language': 'ru,en;q=0.9','referer': link,'user-agent': ua.chrome,'x-requested-with': 'XMLHttpRequest',}
        self.params = {'_allow': 'false'}
        id = self.find_id_pass_def(link)
        response = requests.get(f'https://animego.org/anime/{id}/player', params=self.params,headers=self.headers)

        if response.status_code != 200: return f'Сайт не вернул ожидаемый код 200: {response.status_code}'

        js = response.json()
        soup = BeautifulSoup(js['content'],self.LXML_USE)
        for anime in soup.find_all(class_="tab-pane video-player-toggle scroll"):
            anime:BeautifulSoup
            url = anime.find(class_="video-player-toggle-item text-truncate mb-1 br-3")['data-player']
            if url == None or url == '': continue
            else:break
        info = self.find_id_episode_transilation(url,episodes)
        text = self.get_mpd_file_pass_def(info)
        id_video = self.get_res_pass_def(text,res)
        ints = self.global_initialization.replace('$RepresentationID$',id_video)
        r = requests.get('https://' + self.domain + self.extracted_value + ints,headers=self.headers)
        if dowmload_only_audio == True:
            init_audio = self.global_initialization.replace('$RepresentationID$',self.global_audio)
            link = 'https://' + self.domain + self.extracted_value 
            links = (self.global_media.replace('$RepresentationID$',self.global_audio))
            return self.download_audio(global_link=link,audio_init_link=init_audio,audio_chunk_link=links)
        if r.status_code != 200:
            return f'Сайт не вернул ожидаемый код 200: {r.status_code}'
        else:
            with open('video.mp4','wb') as f:
                f.write(r.content)
                for i in range(1,1000):
                    link = 'https://' + self.domain + self.extracted_value +(self.global_media.replace('$RepresentationID$',id_video)).replace('$Number%05d$',f'{i:05}')
                    respon = requests.get(link,headers=self.headers)
                    if respon.status_code != 200:
                        print('oops!')
                        if i > 5:
                            return 'good?'
                        return 'BAD'
                    f.write(respon.content)
                    print(f'chunk: {i}')
        
    def download_audio(self,global_link,audio_init_link,audio_chunk_link):
        '''Скачивает Аудио из видео'''
        r = requests.get(global_link + audio_init_link,headers=self.headers)
        with open('mp3_file.mp3','wb') as f:
            f.write(r.content)
            if r.status_code == 200:
                for i in range(1,1000):
                    respon = requests.get(global_link+audio_chunk_link.replace('$Number%05d$',f'{i:05}'),headers=self.headers)
                    if respon.status_code != 200:
                        print('oops!')
                        if i > 5:
                            return 'good?'
                        return 'BAD'
                    f.write(respon.content)
                    print(f'chunk: {i}')
            
        
    
    def get_res_pass_def(self,text,resolution): 
        res = []
        url = {}
        self.global_audio = None
        root = ET.fromstring(text)
        
        for i in root.findall('.//dash:Representation',namespaces=namespace):
            if i.get('height') != None:
                res.append(int(i.get('height')))
                url[str(i.get('height'))] = str(i.get('id'))
            else: self.global_audio = i.get('id')
            
        self.global_initialization = root.find('.//dash:SegmentTemplate',namespaces=namespace).get('initialization')
        self.global_media = root.find('.//dash:SegmentTemplate',namespaces=namespace).get('media')

        avg  = statistics.mean(res)
        if resolution == 'middle':
            return url[str(min(res, key=lambda num: abs(num - avg)))]
        elif resolution == 'min':
            return url[str(min(res))]
        elif resolution == 'max':
            return url[str(max(res))]
        else: return url[str(min(res, key=lambda num: abs(num - avg)))]        
    
    def get_mpd_file_pass_def(self,info):
        r = requests.get(f'https://aniboom.one/embed/{info['id']}',params = {'episode': f'{info['ep']}','translation': f'2'},headers=self.headers)
        soup = BeautifulSoup(r.text,self.LXML_USE)
        data = soup.find(id = 'video')
        data = json.loads(data['data-parameters'])
        data = json.loads(data['dash'])
        r = requests.get(data["src"])
        url:str = data["src"]
        parts = url.split('/')
        self.domain = parts[2]

        self.extracted_value = '/' + parts[3] + '/' + parts[4] + '/'
        if r.status_code != 200: return f'Сайт не вернул ожидаемый код 200: {r.status_code}'
        else: return r.text
    
    def find_id_episode_transilation(self,url:str,episodes):
        id_part = url.split('/')[-1].split('?')[0]
        params = url.split('?')[1].split('&')

        episode = None

        for param in params:
            key, value = param.split('=')
            if key == 'episode':
                episode = value
        if episodes == 1:
            return {
                'id':id_part,
                'ep':episode  
            }
        else:
            return {'id':id_part,'ep':episodes}
    
    def find_id_pass_def(self,link:str):
        id = ''
        for i in link[::-1]:
            try:int(i);id += i
            except ValueError: return id[::-1]

if __name__ == '__main__':
    anime = AnimeGO()
    # пример: anime.download_video('https://animego.org/anime/nepriznannyy-shkoloy-vladyka-demonov-2-2190',episodes=6,dowmload_only_audio=True)
