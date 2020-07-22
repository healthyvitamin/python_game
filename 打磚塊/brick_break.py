import tkinter as tk

#main>初始化game>按空白鍵觸發開始遊戲的start_game()>進入遊戲循環game_loop()

class GameObject(object):
    def __init__(self, canvas, item):
        self.canvas = canvas
        self.item = item

    def get_position(self):
        return self.canvas.coords(self.item)

    def move(self, x, y):
        self.canvas.move(self.item, x, y)

    def delete(self):
        self.canvas.delete(self.item)


class Ball(GameObject): #球
    def __init__(self, canvas, x, y):
        self.radius = 10
        self.direction = [1, -1] #球的飛行方向，一開始要往上飛所以y軸要負的
        self.speed = 10
        #raidus=半徑，創建球
        item = canvas.create_oval(x-self.radius, y-self.radius,
                                  x+self.radius, y+self.radius,
                                  fill='white')
        super(Ball, self).__init__(canvas, item)

    def update(self): #檢查球是否碰撞到畫布邊界
        coords = self.get_position()
        width = self.canvas.winfo_width() #取得畫布寬度
        #判斷是否碰撞到畫布左右邊，是的話x飛行方向要反向
        if coords[0] <= 0 or coords[2] >= width:
            self.direction[0] *= -1
        #碰撞到畫布上側，y飛行方向反向
        if coords[1] <= 0:
            self.direction[1] *= -1
        #根據速度移動一次
        x = self.direction[0] * self.speed
        y = self.direction[1] * self.speed
        self.move(x, y)

    def collide(self, game_objects): #碰撞到物體時 這邊只會傳入磚塊及滑桿
        #畫布邊界並不會,因為邊界的碰撞我們已經在上面update做了，原因跟滑桿同理，只要在每次移動前判斷移動後是否會超出邊界即可，不需要額外根據是否碰撞到邊界做反應
        coords = self.get_position()
        x = (coords[0] + coords[2]) * 0.5 #球中心座標
        if len(game_objects) > 1: #碰撞到不只一個，只讓y飛反方向
            self.direction[1] *= -1
        elif len(game_objects) == 1: #碰撞到一個則判斷是碰撞到磚塊/滑桿的左右還是上下
            game_object = game_objects[0]
            coords = game_object.get_position()
            if x > coords[2]: #碰撞到右邊則x飛右邊
                self.direction[0] = 1
            elif x < coords[0]: #碰撞到左邊則x飛左邊
                self.direction[0] = -1
            else: #碰撞到上下則y飛反方向
                self.direction[1] *= -1

        for game_object in game_objects: #取出被碰撞到的物體
            if isinstance(game_object, Brick): #isinstance確認game_object是磚塊類型，是才做hit動作(減少磚塊生命值、換顏色)
                game_object.hit()


class Paddle(GameObject): #滑桿
    def __init__(self, canvas, x, y):
        self.width = 80
        self.height = 10
        self.ball = None
        item = canvas.create_rectangle(x - self.width / 2,
                                       y - self.height / 2,
                                       x + self.width / 2,
                                       y + self.height / 2,
                                       fill='blue')
        super(Paddle, self).__init__(canvas, item)

    def set_ball(self, ball):
        self.ball = ball

    def move(self, offset):
        coords = self.get_position()
        width = self.canvas.winfo_width()
        #只可移動在畫布之中，所以只有在他的左/右邊座標+位移量不超出畫布時才會做移動
        if coords[0] + offset >= 0 and coords[2] + offset <= width:
            super(Paddle, self).move(offset, 0)
            if self.ball is not None: #這發生在還沒按空白鍵開始遊戲時，因為此時也可以移動滑桿，如果我們想要讓球也跟著滑桿移動，所以這裡讓滑桿移動多少，球也跟著移動。  在按下空白鍵觸發的start_game()時會把self.ball設成None
                self.ball.move(offset, 0)


class Brick(GameObject): #磚塊
    #磚塊顏色
    COLORS = {1: '#999999', 2: '#555555', 3: '#222222'}

    def __init__(self, canvas, x, y, hits):
        self.width = 75
        self.height = 20
        self.hits = hits
        color = Brick.COLORS[hits]
        item = canvas.create_rectangle(x - self.width / 2, #磚塊的大小、顏色
                                       y - self.height / 2,
                                       x + self.width / 2,
                                       y + self.height / 2,
                                       fill=color, tags='brick') #tags用於檢查還有多少個磚塊
        super(Brick, self).__init__(canvas, item)

    def hit(self): #當被擊中時，磚塊生命值-1，如果=0則delete
        self.hits -= 1
        if self.hits == 0:
            self.delete()
        else:
            self.canvas.itemconfig(self.item, #呼叫內建的itemconfig方法更換磚塊顏色
                                   fill=Brick.COLORS[self.hits])


class Game(tk.Frame):
    def __init__(self, master):
        super(Game, self).__init__(master)
        self.lives = 3
        self.width = 610
        self.height = 400
        self.canvas = tk.Canvas(self, bg='#aaaaff',
                                width=self.width,
                                height=self.height,)
        self.canvas.pack()
        self.pack()

        self.items = {} #用於儲存所有"可碰撞的物件"(滑桿、磚塊)
        self.ball = None
        self.paddle = Paddle(self.canvas, self.width/2, 326) #創建滑桿
        #將滑桿加入items中
        #使用滑桿物件本身來當作"key"方便我們在check_collisions方法中直接取得該物件
        self.items[self.paddle.item] = self.paddle
        for x in range(5, self.width - 5, 75):
            self.add_brick(x + 37.5, 50, 2)
            self.add_brick(x + 37.5, 70, 1)
            self.add_brick(x + 37.5, 90, 1)

        self.hud = None #用於儲存顯示生命值的畫布物件 見update_lives_text函式
        self.setup_game() #準備球、顯示生命值等等
        self.canvas.focus_set() #將焦點設定於畫布上(也就是按下空白鍵等等時會是觸發在這上面)

        #綁定左右建以移動滑桿 10是speed值
        self.canvas.bind('<Left>',
                         lambda _: self.paddle.move(-10))
        self.canvas.bind('<Right>',
                         lambda _: self.paddle.move(10))

    def setup_game(self): #此函式會在球掉到下面要重新開始或一開始時呼叫
           self.add_ball() #創建新的球的方法
           self.update_lives_text() #更新生命值的方法
           self.text = self.draw_text(300, 200,
                                      'Press Space to start')
           #將空白建綁定start_game函式
           self.canvas.bind('<space>', lambda _: self.start_game())

    def add_ball(self):
        if self.ball is not None: #刪除原本的球，如果有的話
            self.ball.delete()
        paddle_coords = self.paddle.get_position()
        x = (paddle_coords[0] + paddle_coords[2]) * 0.5 #在滑桿的X中心點的上面一點處創建新的球
        self.ball = Ball(self.canvas, x, 310)
        self.paddle.set_ball(self.ball) #將球給滑桿，用於一開始設定方向用

    def add_brick(self, x, y, hits): #新增磚塊並加入至items中
        brick = Brick(self.canvas, x, y, hits)
        self.items[brick.item] = brick

    def draw_text(self, x, y, text, size='40'): #繪字於畫布上
        font = ('Helvetica', size) #設定字體、大小
        return self.canvas.create_text(x, y, text=text,
                                       font=font)

    def update_lives_text(self): #更新生命值的text
        text = 'Lives: %s' % self.lives
        if self.hud is None:
            self.hud = self.draw_text(50, 20, text, 15)
        else:
            self.canvas.itemconfig(self.hud, text=text)

    def start_game(self):  #開始遊戲，解除綁定空白鍵、刪除螢幕上的"Press Space to start"
        self.canvas.unbind('<space>')
        self.canvas.delete(self.text)
        self.paddle.ball = None #讓球離開滑桿，詳見paddle.move()
        self.game_loop()

    def game_loop(self):
        self.check_collisions()  #確認碰撞
        num_bricks = len(self.canvas.find_withtag('brick')) #使用find_withtag方法根據brick標籤取得目前磚塊數量(創建磚塊時有給標籤brick)
        if num_bricks == 0: #磚塊歸零，贏了
            self.ball.speed = None
            self.draw_text(300, 200, 'You win!')
        elif self.ball.get_position()[3] >= self.height: #如果球掉到畫布最下面則代表失敗，生命值-1並用after 1000毫秒後呼叫setup_game() 重新開始 (最下面為何是height高度? 因笛卡爾座標，且畫布左上角才是(0,0)，往下y增加，往右x增加，故height最高=最底部)
            self.ball.speed = None
            self.lives -= 1
            if self.lives < 0: #如果失敗到生命值<0則game over
                self.draw_text(300, 200, 'Game Over')
            else:
                self.after(1000, self.setup_game)
        else: #磚塊沒歸0、球沒掉到最下面時都呼叫球的update方法讓球飛，並且每50毫秒循環一次這個函式
            self.ball.update()
            self.after(50, self.game_loop)

    def check_collisions(self):
        ball_coords = self.ball.get_position()  #取得球座標
        items = self.canvas.find_overlapping(*ball_coords)  #取得所有跟該"座標"重疊(或者說碰撞)的畫布物件
        #由於我們本身的"遊戲介面"也是一個畫布，但明顯不可碰撞，所以要檢查
        #self.items儲存了目前所有"可碰撞"的物件(滑桿、磚塊)，所以只有跟球碰撞到的是在裡面的才會取出
        #用碰撞到的物件當作key來取出值(這就是為什麼一開始創建滑桿、磚塊時用他們各自的物件當作key來儲存進self.items)
        #最後全取出成一個list，這是"串列綜合運算"的寫法
        objects = [self.items[x] for x in items if x in self.items]
        self.ball.collide(objects) #呼叫球碰撞方法



if __name__ == '__main__':
    root = tk.Tk()
    root.title('Hello, Pong!')
    game = Game(root)
    game.mainloop()
