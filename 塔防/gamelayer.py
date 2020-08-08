import random

from cocos.director import director
from cocos.scenes.transitions import SplitColsTransition, FadeTransition
import cocos.layer
import cocos.scene
import cocos.text
import cocos.actions as ac
import cocos.collision_model as cm

import actors
import mainmenu
from scenario import get_scenario


class GameLayer(cocos.layer.Layer):
    is_event_handler = True #為true才可以使用按鍵輸入事件

    def __init__(self, hud, scenario):
        super(GameLayer, self).__init__()
        self.hud = hud
        self.scenario = scenario
        self.score = self._score = 0
        self.points = self._points = 60
        self.turrets = []

        w, h = director.get_window_size()
        
        #使用兩個碰撞管理器，因為slots只是要放砲塔而已所以可以獨立開來，並不需要發生碰撞，雖然全放在一起也可以，但在判斷是否是敵人或是on_mouse_press()時就要多判斷一堆，因此獨立開來可以改善效能
        cell_size = 32
        self.coll_man = cm.CollisionManagerGrid(0, w, 0, h, cell_size, cell_size)
        self.coll_man_slots = cm.CollisionManagerGrid(0, w, 0, h, cell_size, cell_size)
        for slot in scenario.turret_slots: #在腳本設定的位子全部放入砲塔槽演員，其全部加入coll_man_slots碰撞管理器
            self.coll_man_slots.add(actors.TurretSlot(slot, cell_size))

        self.bunker = actors.Bunker(*scenario.bunker_position) #碉堡
        self.add(self.bunker)
        self.schedule(self.game_loop) #註冊排程game_loop 開始每幀循環
        
    """
    property功能，用於讓一般參數可以用函式讀取、賦值，還可以在期間做其他的處理
    分為getter以及setter，getter顧名思義就是讀取參數時觸發，setter則是賦值時觸發
    只有@property則是預設的getter
    """
    @property 
    def points(self):
        return self._points #回傳points參數，在property前面要+底線_

    @points.setter
    def points(self, val):
        self._points = val
        self.hud.update_points(val) #賦值同時更新hud分數

    @property
    def score(self): #同上
        return self._score

    @score.setter
    def score(self, val): #同上
        self._score = val
        self.hud.update_score(val)

    def game_loop(self, _): #遊戲循環
        self.coll_man.clear() #跟打精靈一樣，要偵測碰撞先把管理員清除
        for obj in self.get_children(): #取得所有在圖層中的物件，如果是敵人就加入
            if isinstance(obj, actors.Enemy):
                self.coll_man.add(obj)

        for turret in self.turrets: #取得目前已經放置的砲塔
            """
            #偵測是否有物件(敵人)，砲塔槽不會 因為已經放在另一個碰撞管理器了)與砲塔相撞，iter_colliding會返回一個跟砲塔相撞的物件的串列，next讓每次呼叫時就取得一個值，使但在這裡只會呼叫一次，代表只取出第一個，這是為了讓砲塔一次只射擊一個敵人,最後一個None是如果next沒有得到任何東西，預設值傳回None
            """
            obj = next(self.coll_man.iter_colliding(turret), None)
            turret.collide(obj)
        for obj in self.coll_man.iter_colliding(self.bunker): #偵測是否有東西與碉堡碰撞，被敵人撞到要扣血
            self.bunker.collide(obj)

        if random.random() < 0.005: #隨機生敵人
            self.create_enemy()

    def create_enemy(self):
        enemy_start = self.scenario.enemy_start #敵人出生位置
        x = enemy_start[0] + random.uniform(-10, 10) #用於避免一直重生在相同座標，所以加入+/-10象素隨機位移
        y = enemy_start[1] + random.uniform(-10, 10)
        self.add(actors.Enemy(x, y, self.scenario.actions)) #敵人出生

    def on_mouse_press(self, x, y, buttons, mod): #當滑鼠點擊到的地方跟砲塔槽碰撞時檢查分數是否夠放一個砲塔
        slots = self.coll_man_slots.objs_touching_point(x, y)
        #print(slots)
        if len(slots) and self.points >= 20:
            self.points -= 20
            
            """
            上方print(slots)，會出現{<actors.TurretSlot object at 0x0000016EB93C4B48>}，可見是一個元組 所以必須取出 這裡作者取出的方法是生成iter之後用next取出
            為何使用next，課本未解釋 next功能原為每次運行時依序取出迭代器中的值
            但這裡即便我們一直選擇將砲塔放置在同一個砲塔槽，砲塔槽始終只有一個，所以原則上並不需要next
            """
            
            slot = next(iter(slots))
            #print(slot)
            
            #將砲塔設置於砲塔槽中心
            # #用"*"可以一次傳x、y座標(=一組參數)，加入砲塔
            turret = actors.Turret(*slot.cshape.center)
            self.turrets.append(turret) #加入砲塔至已有砲塔中
            self.add(turret)

    def remove(self, obj):
        if obj is self.bunker: #如果被刪除的是碉堡 代表失敗，轉場至失敗場景
            director.replace(SplitColsTransition(game_over()))
        elif isinstance(obj, actors.Enemy) and obj.destroyed: #如果是敵人且是因為射擊而被破壞而不是撞到碉堡(碉堡不用給分數)，則給玩家分數、點數
            self.score += obj.score
            self.points += 5
        super(GameLayer, self).remove(obj) #最後才用super使用原本內建的remove方法(先使用會導致先刪除)


class HUD(cocos.layer.Layer): #HUD圖層
    def __init__(self):
        super(HUD, self).__init__()
        w, h = director.get_window_size()
        self.score_text = self._create_text(60, h-40)
        self.score_points = self._create_text(w-60, h-40)

    def _create_text(self, x, y):
        text = cocos.text.Label(font_size=18, font_name='Oswald',
                                anchor_x='center', anchor_y='center')
        text.position = (x, y)
        self.add(text)
        return text

    def update_score(self, score):
        self.score_text.element.text = 'Score: %s' % score

    def update_points(self, points):
        self.score_points.element.text = 'Points: %s' % points


def new_game():
    scenario = get_scenario() #從scenario.py取得所有腳本
    background = scenario.get_background() #取得磚塊地圖圖層作為背景
    hud = HUD() #HUD圖層，顯示分數、點數
    game_layer = GameLayer(hud, scenario)
    return cocos.scene.Scene(background, game_layer, hud)


def game_over():
    w, h = director.get_window_size()
    layer = cocos.layer.Layer()
    text = cocos.text.Label('Game Over', position=(w*0.5, h*0.5),
                            font_name='Oswald', font_size=72,
                            anchor_x='center', anchor_y='center')
    layer.add(text)
    scene = cocos.scene.Scene(layer)
    new_scene = FadeTransition(mainmenu.new_menu()) #FadeTransition轉場景特效
    func = lambda: director.replace(new_scene)
    scene.do(ac.Delay(3) + ac.CallFunc(func)) #如同在main.menu.py的self.create_menu所說，場景也可以做動作，故在3秒後才切換至新場景
    return scene
