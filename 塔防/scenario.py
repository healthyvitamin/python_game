import cocos.tiles
import cocos.actions as ac


RIGHT = ac.RotateBy(90, 1)
LEFT = ac.RotateBy(-90, 1)


def move(x, y):
    dur = abs(x+y) / 100.0
    return ac.MoveBy((x, y), duration=dur)


class Scenario(object):
    def __init__(self, tmx_map, turrets, bunker, enemy_start):
        self.tmx_map = tmx_map
        self.turret_slots = turrets
        self.bunker_position = bunker
        self.enemy_start = enemy_start
        self._actions = None

    @property
    def actions(self):
        return self._actions

    @actions.setter
    def actions(self, actions):
        self._actions = ac.RotateBy(90, 0.5)
        for step in actions:
            self._actions += step

    def get_background(self): #載入磚塊地圖(tmx檔案)做為一個layer圖層
        tmx_map = cocos.tiles.load('assets/tower_defense.tmx')
        bg = tmx_map[self.tmx_map] #self.tmx_map是'map0' 取得這個tmx檔內的map0圖層
        bg.set_view(0, 0, bg.px_width, bg.px_height) #設定覆蓋區域
        return bg


def get_scenario(): #定義砲塔、碉堡、敵人開始位子，給定在tiled map editor內製作磚塊地圖時給的圖層名稱(但還未載入磚塊地圖，載入在get_background)、敵人整場的動作
    turret_slots = [(192, 352), (320, 352), (448, 352),
                    (192, 192), (320, 192), (448, 192),
                    (96, 32), (224, 32), (352, 32), (480, 32)]
    bunker_position = (528, 430)
    enemy_start = (-80, 110)
    sc = Scenario('map0', turret_slots,
                  bunker_position, enemy_start)
    sc.actions = [move(610, 0), LEFT, move(0, 160),
                  LEFT, move(-415, 0), RIGHT,
                  move(0, 160), RIGHT, move(420, 0)]
    return sc
