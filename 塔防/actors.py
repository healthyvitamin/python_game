import math

import cocos.sprite
import cocos.audio
import cocos.actions as ac
import cocos.euclid as eu
import cocos.collision_model as cm

import pyglet.image
from pyglet.image import Animation

raw = pyglet.image.load('assets/explosion.png') #爆炸特效
seq = pyglet.image.ImageGrid(raw, 1, 8)
explosion_img = Animation.from_image_sequence(seq, 0.07, False)


class Explosion(cocos.sprite.Sprite):
    def __init__(self, pos):
        super(Explosion, self).__init__(explosion_img, pos)
        self.do(ac.Delay(1) + ac.CallFunc(self.kill))


class Shoot(cocos.sprite.Sprite):
    def __init__(self, pos, offset, target):
        super(Shoot, self).__init__('shoot.png', position=pos)
        self.do(ac.MoveBy(offset, 0.1) +
                ac.CallFunc(self.kill) +
                ac.CallFunc(target.hit))


class Hit(ac.IntervalAction): #繼承自間隔動作
    def init(self, duration=0.5):
        self.duration = duration

    def update(self, t):
        self.target.color = (255, 255 * t, 255 * t)


class TurretSlot(object):
    def __init__(self, pos, side):
        self.cshape = cm.AARectShape(eu.Vector2(*pos), side*0.5, side*0.5)


class Actor(cocos.sprite.Sprite):
    def __init__(self, img, x, y):
        super(Actor, self).__init__(img, position=(x, y))
        self._cshape = cm.CircleShape(self.position,
                                      self.width * 0.5)

    @property
    def cshape(self): #069會在每楨update為了檢測碰撞區塊而呼叫chsape時觸發，這樣就可以跟actions做連動了，本體跟碰撞區塊都會跟著一起移動
        self._cshape.center = eu.Vector2(self.x, self.y)
        return self._cshape


class Turret(Actor):
    def __init__(self, x, y):
        super(Turret, self).__init__('turret.png', x, y)
        ##偵測與敵人碰撞的方法是使用一個圓形代表範圍，所以gamelayer的update會偵測是否有敵人跟圓形碰撞
        self.add(cocos.sprite.Sprite('range.png', opacity=50, scale=5))
        self.cshape.r = 125.0
        self.target = None
        self.period = 2.0
        self.reload = 0.0
        self.schedule(self._shoot) #排程_shoot() 讓砲塔自動計算時間進行射擊

    """
    _shoot 使用底線命名的主要功能在於命名的"風格"
    但python有另外的機制，當import * 時並不會引入這個fc，但其實還是可以使用 from actors import _shoot引入
    """
    def _shoot(self, dt): #計算reload以每隔一段時間才射一顆子彈，dt代表幀與幀之間的時間
        if self.reload < self.period:
            self.reload += dt
        elif self.target is not None:
            self.reload -= self.period
            offset = eu.Vector2(self.target.x - self.x, #同小精靈遊戲解釋，子彈的射擊
                                self.target.y - self.y)
            pos = self.cshape.center + offset.normalized() * 20
            self.parent.add(Shoot(pos, offset, self.target))

    def collide(self, other): #範圍與敵人碰撞時為了讓砲塔口跟著敵人旋轉，使用atan2方法計算與該敵人之間的角度(詳見google)
        self.target = other
        if self.target is not None:
            x, y = other.x - self.x, other.y - self.y
            angle = -math.atan2(y, x)
            self.rotation = math.degrees(angle)


class Enemy(Actor):
    def __init__(self, x, y, actions):
        super(Enemy, self).__init__('tank.png', x, y)
        self.health = 100
        self.score = 20
        self.destroyed = False #用於判斷是否是被砲塔射擊摧毀的，被砲塔擊毀要給分數、碉堡不用
        self.do(actions)

    def hit(self):
        self.health -= 25
        self.do(Hit())
        if self.health <= 0 and self.is_running: #用is_running確認他還在
            self.destroyed = True #destroyed=true 到下面呼叫kill並進入gamelayer.py的remove時即可判斷刪除
            self.explode()

    def explode(self):
        self.parent.add(Explosion(self.position))
        self.kill() #此時會觸發game.layer的remove方法


class Bunker(Actor): #碉堡
    def __init__(self, x, y):
        super(Bunker, self).__init__('bunker.png', x, y)
        self.hp = 100

    def collide(self, other):
        if isinstance(other, Enemy): #如果是敵人碰撞到，扣血並且爆炸，不會呼叫敵人的hit方法所以destroyed=flase，因為不是玩家擊毀 不用給分數
            self.hp -= 10
            other.explode()
        if self.hp <= 0:
            self.kill()
