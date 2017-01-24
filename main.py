import kivy
kivy.require('1.9.1')

from kivy.app import App
from kivy.uix.image import Image
from kivy.graphics import Color, Rectangle
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.storage.jsonstore import JsonStore

from os.path import join
import webbrowser # to open urls
    
import urllib2
import zipfile, os

import threading
import subprocess

storage = JsonStore('storage.json')

# window properties
from kivy.core.window import Window
Window.size = [784, 532]
Window.borderless = True

class HoverBehavior(object):
    def __init__(self, **kwargs):
        self.hovered = False
        self.register_event_type('on_enter')
        self.register_event_type('on_leave')
        Window.bind(mouse_pos=self.on_mouse_pos)
        super(HoverBehavior, self).__init__(**kwargs)

    def on_mouse_pos(self, *args):
        if not self.get_root_window():
            return # do proceed if not displayed
        pos = args[1]
        inside = self.collide_point(*self.to_widget(*pos))
        if self.hovered == inside:
            return
        self.hovered = inside
        if inside:
            self.dispatch('on_enter')
        else:
            self.dispatch('on_leave')

    def on_enter(self):
        if hasattr(self, 'link'): #if icon
            self.size = (50,50)
            self.pos = (self.pos[0]+5, self.pos[1]+5)
        self.background_normal = self.background_normal[:-4] + '_hover.png'

    def on_leave(self):
        if hasattr(self, 'link'): #if icon
            self.size = (60,60)
            self.pos = (self.pos[0]-5, self.pos[1]-5)
        self.background_normal = self.background_normal[:-10] + '.png'

from kivy.factory import Factory
Factory.register('HoverBehavior', HoverBehavior)

class LangButton(Button):
    def __init__(self, **kwargs):
        super(LangButton, self).__init__(**kwargs)
        self.size = (60,36)
        self.pos = (38,474)
        self.background_normal = join('buttons', 'eng.png' if lang == 'rus' else 'rus.png')
        self.background_down = join('buttons', 'eng.png' if lang == 'rus' else 'rus.png')
        
    def update(self, *args):
        self.background_normal = join('buttons', 'eng.png' if lang == 'rus' else 'rus.png')
        self.background_down = join('buttons', 'eng.png' if lang == 'rus' else 'rus.png')
    
    def on_press(self, *args):
        if lang == 'rus':
            global lang
            lang = 'eng'
        else:
            global lang
            lang = 'rus'
            
        self.update()
        bg.update()
        download_bttn.update()
        play_bttn.update()
        update_bttn.update()
        for bttn in contact_bttns:
            bttn.update()
            
class ExitButton(Button, HoverBehavior):
    def __init__(self, **kwargs):
        super(ExitButton, self).__init__(**kwargs)
        self.size = (55,53)
        self.background_normal = join('buttons', 'exit.png')
        self.background_down = join('buttons', 'exit_hover.png')
        self.pos = (706,460)
    
    def on_press(self, *args):
        App.get_running_app().stop()
        
class LoadingAnimation(Image):
    def __init__(self, **kwargs):
        super(LoadingAnimation, self).__init__(**kwargs)
        self.size = (376, 218)
        self.source = join('loading', lang, '1.png')
        self.pos = (210,149)
        self.step = 1 # animation step from 1 to 7
        
    def update(self, *args):
        if download_bttn.pos[1]>0 and download_bttn.stop.is_set():
            Clock.schedule_once(download_bttn.clear, .5)
            return False
        elif download_bttn.pos[1]<0 and update_bttn.stop.is_set():
            Clock.schedule_once(update_bttn.clear, .5)   
            return False
        else:
            self.step += 1
            if self.step == 8:
                self.step = 1
            self.source = join('loading', lang, str(self.step)+'.png')
        
class Background(Image):
    def __init__(self, **kwargs):
        super(Background, self).__init__(**kwargs)
        self.pos = (0,0)
        self.size = (784, 532)
        if lang == 'rus': # default to russian if system language is russian
            self.source = join('bg', 'rus.png')
        else:
            self.source = join('bg', 'eng.png')
    def update(self):
        self.source = join('bg', lang + '.png')
        
class Icon(Button, HoverBehavior):
    def __init__(self, pos_x, pos_y, name, link, **kwargs):
        super(Icon, self).__init__(**kwargs)
        self.pos = (pos_x, pos_y)
        self.name = name
        self.background_normal = join('icons', name + '_icon.png')
        self.background_down = join('icons', name + '_icon_hover.png')
        self.size = (60,60)
        self.link = link
        
    def on_press(self, *args):
        webbrowser.open(self.link, new=2, autoraise=True) # open link url

class ContactButton(Button, HoverBehavior):
    def __init__(self, name, url, **kwargs):
        super(ContactButton, self).__init__(**kwargs)
        self.background_normal = join('buttons', name + '_rus.png' if lang == 'rus' else name + '.png')
        self.background_down = join('buttons', name + '_rus_hover.png' if lang == 'rus' else name + '_hover.png')
        self.pos_dict = {'contact': {'eng': (520,13), 'rus': (550,10)}, 'donate': {'eng': (307,13), 'rus': (214,10)}, 'site': {'eng': (90,13), 'rus': (78,10)}}
        self.size_dict = {'contact': {'eng': (170,35), 'rus': (172,42)}, 'donate': {'eng': (170,35), 'rus': (312,42)}, 'site': {'eng': (170,35), 'rus': (102,42)}}
        self.pos = self.pos_dict[name][lang]
        self.size = self.size_dict[name][lang]
        self.url = url
        self.name = name
        
    def on_press(self, *args):
        webbrowser.open(self.url, new=2, autoraise=True) # open link url
        
    def update(self, *args):
        self.background_normal = join('buttons', self.name + '_rus.png' if lang == 'rus' else self.name + '.png')
        self.background_down = join('buttons', self.name + '_rus_hover.png' if lang == 'rus' else self.name + '_hover.png')
        self.pos = self.pos_dict[self.name][lang]
        self.size = self.size_dict[self.name][lang]
        
class Shade(Widget):
    def __init__(self, **kwargs):
        super(Shade, self).__init__(**kwargs)
        self.size = (784, 532)
        with self.canvas:
            Color(0,80/255.,138/255.,.5)
            Rectangle(pos=(0,0), size=self.size)
        
class DownloadButton(Button, HoverBehavior):
    def __init__(self, **kwargs):
        super(DownloadButton, self).__init__(**kwargs)
        self.background_normal = join('buttons', 'download_rus.png' if lang == 'rus' else 'download.png')
        self.background_down = join('buttons', 'download_rus_hover.png' if lang == 'rus' else 'download_hover.png')
        self.size = (437,148)
        self.stop = threading.Event()
        if storage.get('version')['date'] == storage.get('version')['size'] == 0: # if files haven't been downloaded
            self.pos=(190,149)
        else:
            self.pos=(-190,-149) # hide button
        
    def download(self, url, filename, *args):
        page=urllib2.urlopen(url)
        headers = (page.headers['last-modified'], page.headers['content-length'])
        storage.put('version', date = headers[0], size = headers[1]) # save files version to check updates
        open(filename,'wb').write(page.read())
        
    def unzip(self, source_filename, dest_dir, *args):
        with zipfile.ZipFile(source_filename) as zf:
            zf.extractall(dest_dir)
            zf.close()
        os.remove(source_filename)
        
    def on_press(self, *args):
         # darken screen
        global shade
        shade = Shade()
        self.parent.add_widget(shade)
        # show loading animation
        global loading_animation
        loading_animation = LoadingAnimation()
        self.parent.add_widget(loading_animation)
        
        def download_and_unzip(*args):
            if lang == 'rus': # download russian version
                self.download('http://www.colorado.edu/conflict/peace/download/peace_essay.ZIP', 'data.zip')
            else: # download english version
                self.download('http://prdownloads.sourceforge.net/gretl/gretl-2016d-win32.zip', 'data.zip')
            self.unzip('data.zip', 'data')
            self.stop.set()
        
        Clock.schedule_interval(loading_animation.update, .5)
            
        threading.Thread(target=download_and_unzip).start()
        
    def clear(self, *args): # clear space after animation
        self.parent.remove_widget(loading_animation)
        self.parent.remove_widget(shade)
        storage.put('locale', lang=lang) # save installation language as default
        self.pos = (-190,-149) # hide
        play_bttn.pos = (190,190) # show play bttn
        update_bttn.pos = (190,75) # show update bttn
        
    def update(self, *args):
        self.background_normal = join('buttons', 'download_rus.png' if lang == 'rus' else 'download.png')
        self.background_down = join('buttons', 'download_rus_hover.png' if lang == 'rus' else 'download_hover.png')
        
class PlayButton(Button, HoverBehavior):
    def __init__(self, **kwargs):
        super(PlayButton, self).__init__(**kwargs)     
        self.background_normal = join('buttons', 'play_rus.png' if lang == 'rus' else 'play.png')
        self.background_down = join('buttons', 'play_rus_hover.png' if lang == 'rus' else 'play_hover.png')
        self.size = (408,107)
        self.path = '' # path to executable file, to be written
        if storage.get('version')['date'] == storage.get('version')['size'] == 0: # if files haven't been downloaded
            self.pos=(-190,-149)
        else:
            self.pos=(190,190) # show button
        
    def update(self, *args):
        self.background_normal = join('buttons', 'play_rus.png' if lang == 'rus' else 'play.png')
        self.background_down = join('buttons', 'play_rus_hover.png' if lang == 'rus' else 'play_hover.png')
        
    def on_press(self, *args):
        try:
            subprocess.check_call(join('data', 'gretl', 'gretl.exe'))
        except subprocess.CalledProcessError:
            pass
        
class UpdateButton(Button, HoverBehavior):
    def __init__(self, **kwargs):
        super(UpdateButton, self).__init__(**kwargs)
        self.background_normal = join('buttons', 'update_rus.png' if lang == 'rus' else 'update.png')
        self.background_down = join('buttons', 'update_rus_hover.png' if lang == 'rus' else 'update_hover.png')
        self.ability = True
        self.size = (408,107) if lang == 'rus' else (384,112)
        self.stop = threading.Event()
        if storage.get('version')['date'] == storage.get('version')['size'] == 0: # if files haven't been downloaded
            self.pos = (-190,-149)
        else:
            self.pos = (190,75) # show button
            
    def check_for_updates(self, *args):
        language = storage.get('locale')['lang'] # get language from storage file to match installed version
        url = 'http://www.colorado.edu/conflict/peace/download/peace_essay.ZIP' if language == 'rus' else 'http://prdownloads.sourceforge.net/gretl/gretl-2016d-win32.zip'
        page = urllib2.urlopen(url)
        headers = (page.headers['last-modified'], page.headers['content-length'])
        if headers[0] == storage.get('version')['date'] and headers[1] == storage.get('version')['size']: # up-to-date
            self.ability = False
            if self.background_normal[-9:] == 'hover.png':
                self.background_normal = join('buttons', 'up_to_date_rus_hover.png' if lang == 'rus' else 'up_to_date_hover.png')
            else:
                self.background_down = join('buttons', 'up_to_date_rus.png' if lang == 'rus' else 'up_to_date.png')
      
    def update(self, *args):
        if self.ability:
            self.background_normal = join('buttons', 'update_rus.png' if lang == 'rus' else 'update.png')
            self.background_down = join('buttons', 'update_rus_hover.png' if lang == 'rus' else 'update_hover.png')
        else:
            self.background_normal = join('buttons', 'up_to_date_rus.png' if lang == 'rus' else 'up_to_date.png')
            self.background_down = join('buttons', 'up_to_date_rus_hover.png' if lang == 'rus' else 'up_to_date_hover.png')
        self.size = (408,107) if lang == 'rus' else (384,112)
        
    def download(self, url, filename, *args):
        page = urllib2.urlopen(url)
        headers = (page.headers['last-modified'], page.headers['content-length'])
        storage.put('version', date = headers[0], size = headers[1]) # save files version to check updates
        open(filename,'wb').write(page.read())
        
    def unzip(self, source_filename, dest_dir, *args):
        with zipfile.ZipFile(source_filename) as zf:
            zf.extractall(dest_dir)
            zf.close()
        os.remove(source_filename)
        
    def on_press(self, *args):
        self.check_for_updates()
        if self.ability:
            # darken screen
            global shade
            shade = Shade()
            self.parent.add_widget(shade)
            # show loading animation
            global loading_animation
            loading_animation = LoadingAnimation()
            self.parent.add_widget(loading_animation)
            
            def download_and_unzip(*args):
                language = storage.get('locale')['lang'] # get language from storage file to match installed version
                if language == 'rus': # download russian version
                    self.download('http://www.colorado.edu/conflict/peace/download/peace_essay.ZIP', 'data.zip')
                else: # download english version
                    self.download('http://prdownloads.sourceforge.net/gretl/gretl-2016d-win32.zip', 'data.zip')
                self.unzip('data.zip', 'data')
                self.stop.set()
            
            Clock.schedule_interval(loading_animation.update, .5)
            threading.Thread(target=download_and_unzip).start()
            
        else:
            pass
        
    def clear(self, *args): # clear space after animation
        self.parent.remove_widget(loading_animation)
        self.parent.remove_widget(shade)
        if self.background_normal[-9:] == 'hover.png':
            self.background_normal = join('buttons', 'up_to_date_rus_hover.png' if lang == 'rus' else 'up_to_date_hover.png')
        else:
            self.background_normal = join('buttons', 'up_to_date_rus.png' if lang == 'rus' else 'up_to_date.png')
        self.background_down = join('buttons', 'up_to_date_rus_hover.png' if lang == 'rus' else 'up_to_date_hover.png')
        self.ability = False
        
class MainFrame(Widget):
    def __init__(self, **kwargs):
        super(MainFrame, self).__init__(**kwargs)
        global bg
        bg = Background()
        global download_bttn
        download_bttn = DownloadButton()
        global play_bttn
        play_bttn = PlayButton()
        global update_bttn
        update_bttn = UpdateButton()
        self.add_widget(bg)
        self.add_widget(LangButton())
        self.add_widget(ExitButton())
        self.add_widget(Icon(38, 138, 'twitter', 'http://www.twitter.com'))
        self.add_widget(Icon(38, 215, 'fb', 'http://www.facebook.com'))
        self.add_widget(Icon(38, 292, 'vk', 'http://www.vk.com'))
        self.add_widget(Icon(38, 369, 'youtube', 'http://www.youtube.com'))
        self.add_widget(download_bttn)
        self.add_widget(play_bttn)
        self.add_widget(update_bttn)
        global contact_bttns
        contact_bttns = []
        for x in [('contact', 'http://contacts.com'), ('donate', 'http://donate.com'), ('site', 'http://site.com')]:
            bttn = ContactButton(x[0], x[1])
            contact_bttns.append(bttn)
            self.add_widget(bttn)

class Launcher(App):
    def build(self):
        self.title = 'Mirt Launcher'
        self.icon = 'icon.png'
        # check if game files were downloaded
        try:
            storage.get('version')
        except KeyError:
            storage.put('version', date = 0, size = 0)
        # set default language
        try: 
            global lang
            lang = storage.get('locale')['lang']
        except KeyError:
            import locale
            if locale.getdefaultlocale()[0] == 'ru_RU': # get system language
                lang = 'rus'
            else:
                lang = 'eng'
            storage.put('locale', lang=lang)
        return MainFrame()
    def on_stop(self):
        exit()

if __name__ == '__main__':
    Launcher().run()