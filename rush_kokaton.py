import math
import os
import random
import sys
import time
import pygame as pg

WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
GROUND = 300  # 地面の高さ
os.chdir(os.path.dirname(os.path.abspath(__file__)))
pg.mixer.init()


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


def calc_orientation(org: pg.Rect, dst: pg.Rect) -> tuple[float, float]:
    """
    orgから見て，dstがどこにあるかを計算し，方向ベクトルをタプルで返す
    引数1 org：爆弾SurfaceのRect
    引数2 dst：こうかとんSurfaceのRect
    戻り値：orgから見たdstの方向ベクトルを表すタプル
    """
    x_diff, y_diff = dst.centerx-org.centerx, dst.centery-org.centery
    norm = math.sqrt(x_diff**2+y_diff**2)
    return x_diff/norm, y_diff/norm


class Bird():
    """
    ゲームキャラクター（こうかとん）に関するクラス
    動くかは未定。ボス戦の時に動けた方がいいか考えよう
    """
    # delta = {  # 押下キーと移動量の辞書
    #     pg.K_UP: (0, -1),
    #     pg.K_DOWN: (0, +1),
    #     pg.K_LEFT: (-1, 0),
    #     pg.K_RIGHT: (+1, 0),
    # }

    def __init__(self):
        # super().__init__()      #Spriteクラス継承してるからつけてる
        #こうかとんの画像読み込み
        self.k_img = pg.image.load("fig/9.png")
        self.rk_img = pg.transform.flip(self.k_img, True, False)
        self.rect = self.rk_img.get_rect()

        self.rect.x = 50
        self.rect.y = GROUND + 140


        #重力、ジャンプのこと↓
        self.vy = 0     #縦方向速度
        self.gravity = 1
        self.jumping = False    #ジャンプ中か？の判定のため。初期はジャンプしていない
        self.jump_count = 0      # 現在のジャンプ回数
        self.max_jump = 2        # 最大2段ジャンプ

        #こうかとんの無敵技用

        self.state = "normal"
        self.hyper_life = 500

    def update(self, screen, platforms):
        key_lst = pg.key.get_pressed()

        if key_lst[pg.K_LEFT]:
            self.rect.x -= 5

        if key_lst[pg.K_RIGHT]:
            self.rect.x += 5

       # 移動できる範囲を制限
        if self.rect.left < 50:
            self.rect.left = 50
        if self.rect.right > 350:
            self.rect.right = 350

        self.vy += self.gravity
        self.rect.y += self.vy

    

        if self.rect.y >= GROUND + 140:
            self.rect.y = GROUND + 140
            self.vy = 0
            self.jumping = False
            self.jump_count = 0   # ジャンプ回数リセット
            

    # 足場判定
        for platform in platforms:
         # 上から落ちてきたときのみ乗れる
            if self.rect.colliderect(platform.rect):
                if self.vy >= 0 and self.rect.bottom <= platform.rect.bottom:
                    self.rect.bottom = platform.rect.top
                    self.vy = 0
                    self.jumping = False
                    self.jump_count = 0   # 足場に乗ったらリセット
        screen.blit(self.rk_img, self.rect)



class Map():
    def __init__(self):
        self.bg1_img = pg.image.load("fig/pg2_bg.png")
        self.bg1_img_flip = pg.transform.flip(self.bg1_img,True,False)
        self.bg2_img = pg.image.load("fig/pg4_bg.png")
        self.bg2_img_flip = pg.transform.flip(self.bg2_img,True,False)
        self.bg3_img = pg.image.load("fig/pg3_bg.png")
        self.bg3_img_flip = pg.transform.flip(self.bg3_img,True,False)

        self.x1 = 0     #一枚目の背景
        self.x2 = 1672 #二枚目の背景 画像の大きさが1672だった

        self.speed = 2

    def update(self, screen, time):
        """
        時間経過によってマップを切り替える
        """

        if self.speed < 10:     #背景画像の移動速度
            self.speed += 0.01

        self.x1 -= self.speed
        self.x2 -= self.speed

        #背景画像
        if time <= 2000:
            bg = self.bg1_img
            bg_flip = self.bg1_img_flip
        elif time <= 4000:
            bg = self.bg2_img
            bg_flip = self.bg2_img_flip
        else:
            bg = self.bg3_img
            bg_flip = self.bg3_img_flip

        screen.blit(bg, (self.x1, 0))
        screen.blit(bg_flip, (self.x2, 0))

        #画面外判定
        if self.x1 <= -1672:
            self.x1 = self.x2 + 1672
        if self.x2 <= -1672:
            self.x2 = self.x1 + 1672


class Obstacle(pg.sprite.Sprite):
    """
    障害物クラス
    """
    def __init__(self):
        super().__init__()

        rad = random.randint(20, 30)  # 大小さまざまな岩が転がってくるイメージ
        self.image = pg.Surface((2*rad, 2*rad))
        pg.draw.circle(self.image, (211, 211, 211), (rad, rad), rad)
        self.rect = self.image.get_rect()

        self.rect.x = WIDTH
        self.rect.bottom = GROUND + 200
        self.vx = -random.randint(10, 20)    #障害物の移動速度

    def update(self):
        self.rect.x += self.vx
        if self.rect.right < 0:     #画面外出たら消す
            self.kill()

class Icicle(pg.sprite.Sprite):
    """
    上から落ちてくるつらら
    """

    def __init__(self):
        super().__init__()

        self.image = pg.Surface((20, 60))
        self.image.fill((150, 255, 255))

        self.rect = self.image.get_rect()

        self.rect.x = random.randint(50, 330)
        self.rect.y = 0

        self.vy = random.randint(8, 15)

    def update(self):
        self.rect.y += self.vy

        if self.rect.top > HEIGHT:
            self.kill()

class Platform(pg.sprite.Sprite):
    """
    こうかとんが乗れる足場
    """
    def __init__(self, x, y, w=180, h=20):
        super().__init__()

        self.image = pg.Surface((w, h))
        self.image.fill((139, 69, 19))  # 茶色

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        self.vx = -6   # 背景に合わせて左へ移動

    def update(self):
        self.rect.x += self.vx

        # 画面外に出たら消す
        if self.rect.right < 0:
            self.kill()

class Timer:
    """
    時間表示
    """
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (255, 255, 0)
        self.value = 0
        self.image = self.font.render(f"Timer: {self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 100, HEIGHT-50

    def update(self, screen: pg.Surface, tmr):
        if (tmr%50 == 0 and tmr > 0):
            self.value += 1
        self.image = self.font.render(f"Timer: {self.value}", 0, self.color)
        screen.blit(self.image, self.rect)


class Explosion(pg.sprite.Sprite):
    """
    爆発に関するクラス
    今回はボスの放つ攻撃のための爆発
    障害物も
    """
    def __init__(self, obj: "Obstacle", life: int):
        """
        爆弾が爆発するエフェクトを生成する
        引数1 obj：爆発するBombまたは敵機インスタンス　Bomb|Enemy|が入ってた
        引数2 life：爆発時間
        """
        super().__init__()
        img = pg.image.load(f"fig/explosion.gif")
        self.imgs = [img, pg.transform.flip(img, 1, 1)]
        self.image = self.imgs[0]
        self.rect = self.image.get_rect(center=obj.rect.center)
        self.life = life

    def update(self):
        """
        爆発時間を1減算した爆発経過時間_lifeに応じて爆発画像を切り替えることで
        爆発エフェクトを表現する
        """
        self.life -= 1
        self.image = self.imgs[self.life//10%2]
        if self.life < 0:
            self.kill()


class Life():
    """
    体力
    障害物または敵の攻撃などに当たると減る
    """
    def __init__(self, num):
        self.num = num
        self.img = pg.Surface((40, 40))
        points = [(16*math.sin(t/100)**3 +20,
                    -(13*math.cos(t/100)-5*math.cos(2*t/100)-2*math.cos(3*t/100)-math.cos(4*t/100)) +20
                    ) for t in range(0, 628) ]
        pg.draw.polygon(self.img, (255, 0, 0), points)
        self.img.set_colorkey((0, 0, 0))

    def update(self, screen):
        for i in range(self.num):
            x = WIDTH - 50 - i * 45
            y = HEIGHT - 600
            screen.blit(self.img, (x, y))



def main():
    pg.display.set_caption("走れ！こうかとん")
    screen = pg.display.set_mode((1100, 650))
    clock  = pg.time.Clock()
    move = 0
    tmr = 4000
    maps = Map()    #マップを切り替えるため
    x = 0 #練習5


    timer = Timer()
    bird = Bird()

    exps = pg.sprite.Group()
    obstacle = pg.sprite.Group()
    platforms = pg.sprite.Group()
    icicles = pg.sprite.Group()
    life = Life(5)      

    while True:


        #障害物
        if tmr % 60 == 0:
            obstacle.add(Obstacle())
        # 夕方ステージだけつらら生成
        if 2000 <= tmr < 4000 and tmr % 80 == 0:
            icicles.add(Icicle())
            if tmr % 80 == 0:
                icicles.add(Icicle())
        # 足場生成
        if tmr % 180 == 0:
            y = random.randint(250, 450)
            platforms.add(Platform(WIDTH, y))

        #ステージ名表示のため一時停止
        if tmr == 0:
            bg1_img = pg.image.load("fig/pg2_bg.png")
            screen.blit(bg1_img, (0, 0))
            pg.mixer.music.load("sounds/stage1~2.mp3") # 音源の読み込み

            title_shade = pg.Surface((430, 150))
            title_shade.fill((0, 0, 0))
            title_shade.set_alpha(180)
            screen.blit(title_shade, (350, 250))
            font = pg.font.Font(None, 80)
            txt = font.render("Morning stage", True, (0, 255, 255))
            screen.blit(txt, (400, 300))
            pg.display.update()
            time.sleep(3)
            pg.mixer.music.play(-1) # bgmの再生

        if tmr == 2000:
            #初期設定に戻す
            pg.mixer.music.stop() # bgmの停止
            bird.rect.x = 50
            bird.rect.y = GROUND + 140
            bird.vy = 0
            bird.jumping = False

            #障害物も消す
            obstacle.empty()
            #背景がステージコールの時に反映されないからここで
            screen.blit(maps.bg2_img, (0, 0))

            title_shade = pg.Surface((430, 150))
            title_shade.fill((0, 0, 0))
            title_shade.set_alpha(180)
            screen.blit(title_shade, (350, 250))
            font = pg.font.Font(None, 80)
            txt = font.render("Noon stage", True, (0, 255, 255))
            screen.blit(txt, (400, 300))
            pg.display.update()
            time.sleep(3)
            pg.mixer.music.load("sounds/stage1~2.mp3")
            pg.mixer.music.play(-1) # bgmの再生

        if tmr == 4000:
        #初期設定に戻す
            pg.mixer.music.stop() # bgmの停止
            bird.rect.x = 50
            bird.rect.y = GROUND + 140
            bird.vy = 0
            bird.jumping = False

            #障害物も消す
            obstacle.empty()
            #背景がステージコールの時に反映されないからここで
            screen.blit(maps.bg3_img, (0, 0))

            title_shade = pg.Surface((430, 150))
            title_shade.fill((0, 0, 0))
            title_shade.set_alpha(180)
            screen.blit(title_shade, (350, 250))
            font = pg.font.Font(None, 80)
            txt = font.render("Night stage", True, (0, 255, 255))
            screen.blit(txt, (400, 300))
            pg.display.update()
            time.sleep(3)
            pg.mixer.music.load("sounds/stage3.mp3") # 音源の読み込み
            pg.mixer.music.play(-1)
            

        key_lst = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT: return

            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                # 2回までジャンプ可能
                if bird.jump_count < bird.max_jump:
                    bird.vy = -15
                    bird.jumping = True
                    bird.jump_count += 1

        for obstacles in pg.sprite.spritecollide(bird, obstacle, True):
            exps.add(Explosion(obstacles, 50))
            #こうかとん悲しみエフェクト
            # bird.change_img(8, screen)    
            # score.update(screen)
            life.num -= 1       #ここでlifeを減らす
            pg.display.update()
            if life.num <= 0:
                time.sleep(2)
                return  
            
            # つららとの当たり判定
        for icicle in pg.sprite.spritecollide(bird, icicles, True):
            exps.add(Explosion(icicle, 50))
            life.num -= 1
            pg.display.update()
                
            if life.num <= 0:
                time.sleep(2)
                return
        maps.update(screen, tmr)

        bird.update(screen, platforms)

        exps.update()
        exps.draw(screen)
        timer.update(screen, tmr)  # timerの更新
        life.update(screen)

        platforms.update()
        platforms.draw(screen)
        
        obstacle.update()
        obstacle.draw(screen)
        icicles.update()
        icicles.draw(screen)

        pg.display.update()
        tmr += 1        
        clock.tick(50) #FPSはこれ フレーム数。50フレームで1秒を表すということ


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()