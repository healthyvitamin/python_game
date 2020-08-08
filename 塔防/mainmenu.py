import cocos.menu
import cocos.scene
import cocos.layer
import cocos.actions as ac
from cocos.director import director
from cocos.scenes.transitions import FadeTRTransition

import pyglet.app

from gamelayer import new_game


class MainMenu(cocos.menu.Menu):
    def __init__(self):
        super(MainMenu, self).__init__('Tower Defense')

        self.font_title['font_name'] = 'Oswald' #使用towerdefense.py載入的字體 標題、選項、選中的選項都使用
        self.font_item['font_name'] = 'Oswald'
        self.font_item_selected['font_name'] = 'Oswald' #

        self.menu_anchor_y = 'center' #設定置中
        self.menu_anchor_x = 'center'

        items = list() #選項用list來儲存
        items.append(cocos.menu.MenuItem('New Game', self.on_new_game)) #一般可點擊一次的選項，開始新遊戲
        items.append(cocos.menu.ToggleMenuItem('Show FPS: ', self.show_fps, director.show_FPS)) #布林選項，傳入值至show_fps()，決定是否要顯示FPS則在show_fps()內以及第三個參數都要director.show_FPS，缺一不可
    
        items.append(cocos.menu.MenuItem('Quit', pyglet.app.exit)) #離開遊戲

        self.create_menu(items, ac.ScaleTo(1.25, duration=0.25), ac.ScaleTo(1.0, duration=0.25)) #由於cocos2d 除了精靈以外 其他東西也都是繼承是cocosNode 這意味著一般操控精靈的"動作"也可以使用於這，ScaleTo用於將目標縮放至倍數大小，第一個設定選中時將該選項放大至1.25倍在0.25秒內，第二個是放開時在0.25秒內回復到1倍

    def on_new_game(self): #轉場功能，點擊New Game在2秒內轉場至遊戲場景 FadeTRTransition是轉場特效
        director.push(FadeTRTransition(new_game(), duration=2))

    def show_fps(self, val):  #當FPS選項ON時會傳入1 OFF時會傳入0
        director.show_FPS = val

def new_menu():
    scene = cocos.scene.Scene()
    color_layer = cocos.layer.ColorLayer(205, 133, 63, 255)
    scene.add(MainMenu(), z=1) #選單
    scene.add(color_layer, z=0) #顏色塗層
    return scene
