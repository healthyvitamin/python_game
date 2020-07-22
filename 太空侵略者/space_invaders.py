import random
from collections import defaultdict #可有預設值的字典
from pyglet.image import load, ImageGrid, Animation #用於異形的圖片變換
from pyglet.window import key #用於綁定按鍵事件
import cocos.layer
import cocos.sprite
import cocos.collision_model as cm #碰撞管理器
import cocos.euclid as eu #euclid是設定圖片"碰撞區塊的大小"需要的模組，使用Vecotr2中心座標
#--------------------------------------------------------------------------------------
"""
程式運作邏輯:創建導演、場景、game圖層、hud圖層(顯示分數、生命值)>開始運行，game圖層排程了update函式
故開始每禎呼叫update，開始偵測碰撞、呼叫每個物件移動、偵測按鍵(玩家按下空白鍵發射)等等
"""
#--------------------------------------------------------------------------------------
class Actor(cocos.sprite.Sprite): #演員，異形、玩家、子彈皆繼承自此類
    def __init__(self, image, x, y):
        super(Actor, self).__init__(image) #傳入圖片
        self.position = eu.Vector2(x, y) #設定圖片中心座標
        #設定圖片的碰撞區塊，給定中心座標以及大小，碰撞區塊跟圖片是兩個獨立的存在，所以圖片有任何移動時，碰撞區塊也一定要跟著移動
        #AARectShape為矩形的碰撞區塊，他使用曼哈頓距離(見google)計算兩個矩形之間的碰撞
        self.cshape = cm.AARectShape(self.position,
                                     self.width * 0.5,
                                     self.height * 0.5)

    def move(self, offset): #根據位移量移動，當圖片移動時，碰撞區塊也跟著移動
        self.position += offset
        self.cshape.center += offset

    def update(self, elapsed):
        pass

    def collide(self, other):
        pass

class PlayerCannon(Actor): #玩家
    KEYS_PRESSED = defaultdict(int) #用於儲存按下的按鍵，defaultdict就是可以有預設值的字典

    def __init__(self, x, y):
        super(PlayerCannon, self).__init__('img/cannon.png', x, y)
        self.speed = eu.Vector2(200, 0) #速度

    def update(self, elapsed): #玩家的更新，取得按下的鍵
        pressed = PlayerCannon.KEYS_PRESSED
        #如果空白鍵有被按下則射出子彈 PlayerShoot.INSTANCE用於判斷場上還有沒有子彈，因為我們想要一次只能射一發
        space_pressed = pressed[key.SPACE] == 1
        if PlayerShoot.INSTANCE is None and space_pressed:
            self.parent.add(PlayerShoot(self.x, self.y + 50))
        #玩家往左/往右移動
        movement = pressed[key.RIGHT] - pressed[key.LEFT]
        """
        #判斷是否超出邊界，不會超出才可移動
        自身x座標只能在大於自身圖片一半的寬度以及，畫面寬度-自身圖片一半的範圍內移動
        這樣自己的圖片才不會超出視窗。
        """
        w = self.width * 0.5
        if movement != 0 and w <= self.x <= self.parent.width - w:
            self.move(self.speed * movement * elapsed)

    def collide(self, other): #玩家只要被打到(碰撞到)就會死亡
        other.kill()
        self.kill()

class GameLayer(cocos.layer.Layer):
    is_event_handler = True #這個要宣告為true，圖層才會處理輸入事件

    #按下按鍵時觸發，在這裡為一個Pyglet按鍵常數，例如方向"上"鍵 其k值為65362
    #可以from pyglet.window import key 列印key.symbol_string(k)即可看k值原本是什麼鍵
    def on_key_press(self, k, _): #將按下的按鍵在字典中儲存，用k值當作key，value=1
        PlayerCannon.KEYS_PRESSED[k] = 1

    def on_key_release(self, k, _):
        PlayerCannon.KEYS_PRESSED[k] = 0

    def __init__(self, hud):
        super(GameLayer, self).__init__()
        #初始化各項數值
        w, h = cocos.director.director.get_window_size()
        self.hud = hud
        self.width = w
        self.height = h
        self.lives = 3
        self.score = 0
        self.update_score()
        self.create_player()
        self.create_alien_group(100, 300)
        #碰撞管理器的一種，將整個空間分成指定寬度與高度的矩形方格，計算物件之間的關係時只考慮物件與已知實體重疊的相同方格，例如某兩物件分別有2格長度，當他們的第一格互相碰撞，就只會計算第一格，效能較好。
        cell = 1.25 * 50
        self.collman = cm.CollisionManagerGrid(0, w, 0, h,
                                               cell, cell)
        self.schedule(self.update) #呼叫身為layer內建的schedule方法，排程每禎呼叫它

    def create_player(self): #創造玩家，重生或是一開始都會呼叫
        self.player = PlayerCannon(self.width * 0.5, 50)
        self.add(self.player) #加入player於圖層中
        self.hud.update_lives(self.lives) #更新生命值，例如是死掉重生，則

    def update_score(self, score=0): #更新分數，hud也要更新
        self.score += score
        self.hud.update_score(self.score)

    def create_alien_group(self, x, y): #創建異形集團
        self.alien_group = AlienGroup(x, y)
        for alien in self.alien_group:
            self.add(alien)

    def update(self, dt): #dt代表禎與禎之間的時間(即上次呼叫update到現在這次呼叫經過的時間)，會傳
        self.collman.clear() #清除碰撞管理器裡面的已知物件集合
        for _, node in self.children: #取得目前圖層有的所有物件並加入碰撞管理器
            self.collman.add(node)
            if not self.collman.knows(node): #如果有不存在碰撞區塊的物件就刪除，例如子彈離開螢幕時，不會與任何碰撞管理器的碰撞區塊重疊，所以便不在碰撞管理器內了，此時用這方法可以刪除
                self.remove(node)
        self.collide(PlayerShoot.INSTANCE) #呼叫collide方法處理玩家子彈是否有碰撞到異形
        if self.collide(self.player): #偵測玩家是否被碰撞到(被異形/異形的子彈打到，代表死亡)，重生玩家
            self.respawn_player()

        for column in self.alien_group.columns: #columns儲存了每一行異形(直行橫列)
            shoot = column.shoot() #呼叫AlienColumn的shoot()方法射擊
            if shoot is not None: #由於我們是隨機進行射擊(所以不一定射擊)，所以如果有射擊，要將該物件加入至圖層中
                self.add(shoot)

        for _, node in self.children: #取出目前所有的物件呼叫他們各自的方法，進行移動等等動作，傳入dt因玩家、異形、子彈等等移動都需要用到，以讓他們動起來"順暢"
            node.update(dt)
        self.alien_group.update(dt) #異形也要下降
        if random.random() < 0.001: #以隨機方式在上方出現MysteryShip
            self.add(MysteryShip(50, self.height - 50))


    def collide(self, node): #處理任何碰撞事件
        if node is not None:
            for other in self.collman.iter_colliding(node): #iter_colliding方法查看node是否有碰撞到任何在碰撞管理內的物件，會回傳一個包含所有碰撞到的物件的"迭代"，故要用for取出
                node.collide(other) #呼叫該物件的碰撞方法
                return True
        return False

    def respawn_player(self): #重生玩家，減少生命值，當生命值<0則結束
        self.lives -= 1
        if self.lives < 0:
            self.unschedule(self.update) #將update排程移除
            self.hud.show_game_over() #HUD顯示game_over
        else:
            self.create_player() #重生玩家

#--------------------------------------------------------------------------------------------
"""
    異形設計邏輯:有三種異形分別以123代替，並且一行(直行橫列)稱為AlienColumn，所有異形稱為AlienGroup
    每行會從最下面開始建立
      4  1 1 1
      3  2 2 2
      2  2 2 2
      1  3 3 3
      0  3 3 3
"""
class Alien(Actor): #單一隻異形
    def load_animation(imgage): #載入動畫
        seq = ImageGrid(load(imgage), 2, 1) #載入一個圖片網格
        return Animation.from_image_sequence(seq, 0.5) #每0.5秒變換一次圖片
    #三種異形及其分數
    TYPES = {
        '1': (load_animation('img/alien1.png'), 40),
        '2': (load_animation('img/alien2.png'), 20),
        '3': (load_animation('img/alien3.png'), 10)
    }

    def from_type(x, y, alien_type, column): #用於AlienColumn呼叫創列一行的異形
        animation, score = Alien.TYPES[alien_type] #指定異形種類
        return Alien(animation, x, y, score, column)

    def __init__(self, img, x, y, score, column=None):
        super(Alien, self).__init__(img, x, y)
        self.score = score
        self.column = column #自身所屬的AlienColumn

    def on_exit(self): #當異形從場景中被刪除時會自動呼叫，告知所屬的行列要刪除他(因為我們想要讓異形從最下面發射子彈)
        super(Alien, self).on_exit()
        if self.column:
            self.column.remove(self)

class AlienColumn(object): #一行異形
    def __init__(self, x, y):
        #enumerate列舉，下面會變成[(0,'3'), (1, '3'), (2, '2'), (3, '2'), (4, '1')]
        alien_types = enumerate(['3', '3', '2', '2', '1'])
        self.aliens = [Alien.from_type(x, y+i*60, alien, self) #創建一行異形 self.aliens儲存
                       for i, alien in alien_types]

    def should_turn(self, d): #用於偵測異形是否抵達邊界，見side_reached()
        if len(self.aliens) == 0: #如果該行已經沒有異形
            return False
        alien = self.aliens[0] #取得最下面那個異形
        x, width = alien.x, alien.parent.width #異形的x座標以及異形所在的圖層的寬度
        #想要判斷異形是否抵達邊界，只要根據
        return x >= width - 50 and d == 1 or x <= 50 and d == -1

    def remove(self, alien): #刪除一行內的某個異形
        self.aliens.remove(alien)

    def shoot(self):  #異形射擊，採用隨機判斷，只有還有異形以及random值<0.001時才發射
        if random.random() < 0.001 and len(self.aliens) > 0:
            pos = self.aliens[0].position #取得最下面的異形的位子(因為異形被打掉會被刪除)
            return Shoot(pos[0], pos[1] - 50) #從該異形的Y軸下面50處發射
        return None


class AlienGroup(object): #代表所有異形
    def __init__(self, x, y):
        self.columns = [AlienColumn(x + i * 60, y)  #創建10行異形 self.columns儲存
                        for i in range(10)]
        self.speed = eu.Vector2(10, 0) #異形移動速度
        self.direction = 1 #見update
        self.elapsed = 0.0
        self.period = 1.0

    """
    每次更新時計算self.elapsed累積到1.0了沒，到1.0才移動整個異形集團，
    """
    def update(self, elapsed):  #elapsed=dt 即禎與禎之間的時間
        self.elapsed += elapsed
        while self.elapsed >= self.period:
            self.elapsed -= self.period
            offset = self.direction * self.speed
            if self.side_reached(): #偵測是否有任何一行的異形碰撞到了邊界，則x方向要相反 (y固定是往下)
                self.direction *= -1
                offset = eu.Vector2(0, -10)
            for alien in self: #這個self會呼叫下面的__iter__方法，讓每個異形移動=整個集團移動
                alien.move(offset)

    def side_reached(self): #使用lambda呼叫每一行異形的should_turn()方法檢查是否碰撞到邊界，並且用map一個一個餵給any，只要有任何一個為true，any就會回傳true(碰到邊界了)
        return any(map(lambda c: c.should_turn(self.direction),
                       self.columns))

    def __iter__(self): #創建自身的"迭代器"
        for column in self.columns: #取出每一行的每一個異形，yield功能是讓上面的for alien in self 每次拿取一個alien時
            #才會給一個alien(有點像同步、多執行緒的感覺)
            for alien in column.aliens:
                yield alien

#--------------------------------------------------------------------------------------------

class Shoot(Actor):
    def __init__(self, x, y, img='img/shoot.png'):
        super(Shoot, self).__init__(img, x, y)
        self.speed = eu.Vector2(0, -400) #預設是敵人的子彈，所以Y是負的，往下射，玩家射擊要改成正的

    def update(self, elapsed):
        self.move(self.speed * elapsed)

class PlayerShoot(Shoot):
    INSTANCE = None #用於判斷是否還有子彈在場上，因為我們想要一次只能射一發，在前一發還沒擊中/消失之前不可再射擊

    def __init__(self, x, y):
        super(PlayerShoot, self).__init__(x, y, 'img/laser.png')
        self.speed *= -1 #原本shoot父類別的子彈是往下射，故這邊反向，玩家射要往上
        PlayerShoot.INSTANCE = self #用於保存playershoot

    def collide(self, other):
        if isinstance(other, Alien): #當子彈擊中異形，更新分數並且異形跟子彈都消失
            self.parent.update_score(other.score) #呼叫parent(圖層)的update_score 也就是game的update_score
            other.kill() #子彈、異形都繼承自Actor繼承自Spirte，所以這裡呼叫Spirte內建的kill方法以刪除
            self.kill()

    def on_exit(self): #當該子彈從場景中刪除時會自動被呼叫，將INSTANCE設回None
        super(PlayerShoot, self).on_exit() #使用super以繼承原本的on_exit功能再改寫，因為直接改寫會蓋掉原本的
        PlayerShoot.INSTANCE = None

class HUD(cocos.layer.Layer): #顯示生命、分數的圖層
    def __init__(self):
        super(HUD, self).__init__()
        w, h = cocos.director.director.get_window_size()
        self.score_text = cocos.text.Label('', font_size=18)
        self.score_text.position = (20, h - 40)
        self.lives_text = cocos.text.Label('', font_size=18)
        self.lives_text.position = (w - 100, h - 40)
        self.add(self.score_text)
        self.add(self.lives_text)

    def update_score(self, score): #更新分數
        self.score_text.element.text = 'Score: %s' % score

    def update_lives(self, lives):  #更新生命值
        self.lives_text.element.text = 'Lives: %s' % lives

    def show_game_over(self):
        w, h = cocos.director.director.get_window_size()
        game_over = cocos.text.Label('Game Over', font_size=50,
                                     anchor_x='center',
                                     anchor_y='center')
        game_over.position = w * 0.5, h * 0.5
        self.add(game_over)

class MysteryShip(Alien): #神秘飛船，在game.layer的update會呼叫以產生飛船
    SCORES = [10, 50, 100, 200]

    def __init__(self, x, y):
        score = random.choice(MysteryShip.SCORES)
        super(MysteryShip, self).__init__('img/alien4.png', x, y,
                                          score)
        self.speed = eu.Vector2(150, 0)

    def update(self, elapsed):
        self.move(self.speed * elapsed)


if __name__ == '__main__':
    cocos.director.director.init(caption='Cocos Invaders', #director初始化主視窗
                                 width=800, height=650)
    main_scene = cocos.scene.Scene() #場景
    hud_layer = HUD() #生命值、score的圖層， 圖層排序在1
    main_scene.add(hud_layer, z=1)
    game_layer = GameLayer(hud_layer) #遊戲的主圖層，圖層排序在0，所以hud在game的後面
    main_scene.add(game_layer, z=0)
    cocos.director.director.run(main_scene) #運行場景主迴圈，開始每禎運行GameLayer的self.schedule(他排程了update)
