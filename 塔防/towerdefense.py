from cocos.director import director

import pyglet.font
import pyglet.resource

from mainmenu import new_menu


if __name__ == '__main__':
    #加入path資源路徑
    pyglet.resource.path.append('assets')
    #將path放入一個list來指定"資源路徑"，這樣例如在actor.py載入角色圖片的時候就可以直接指定檔案，不用路徑。
    pyglet.resource.reindex()
    #加入一種字體 讓HUD、選單的選項都可以使用這個字體來顯示字
    pyglet.font.add_file('assets/Oswald-Regular.ttf')
    #初始化
    director.init(caption='Tower Defense')
    #開始運行選單場景，new_menu()會返回選單場景
    director.run(new_menu())


"""
流程:towerdefense.py > mainmenu.py 選單場景 > gamelayer的new_game() > scenario.py取得腳本 > 遊戲場景 > 每幀運行gamelayer的update、actors的turrents的_shoots > 結束 > gamelayer的game_over()場景 > 回到選單
"""