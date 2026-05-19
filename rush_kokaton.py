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
# class Score:
#     """
#     打ち落とした爆弾，敵機の数をスコアとして表示するクラス
#     爆弾：1点
#     敵機：10点
#     今からかえる
#     こうかとんの座標を超えた障害物を判定
#     """
#     def __init__(self):
#         self.font = pg.font.Font(None, 50)
#         self.color = (0, 0, 255)
#         self.value = 0
#         self.image = self.font.render(f"Score: {self.value}", 0, self.color)
#         self.rect = self.image.get_rect()
#         self.rect.center = 100, HEIGHT-50

#     def update(self, screen: pg.Surface):
#         self.image = self.font.render(f"Score: {self.value}", 0, self.color)
#         screen.blit(self.image, self.rect)


# class Bomb(pg.sprite.Sprite):
#     """
#     爆弾に関するクラス
#     今回はボスが出してくる攻撃などとして使用
#     """
#     colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]

#     def __init__(self, emy: "Enemy", bird: Bird):
#         """
#         爆弾円Surfaceを生成する
#         引数1 emy：爆弾を投下する敵機
#         引数2 bird：攻撃対象のこうかとん
#         """
#         super().__init__()
#         rad = random.randint(10, 50)  # 爆弾円の半径：10以上50以下の乱数
#         self.image = pg.Surface((2*rad, 2*rad))
#         color = random.choice(__class__.colors)  # 爆弾円の色：クラス変数からランダム選択
#         pg.draw.circle(self.image, color, (rad, rad), rad)
#         self.image.set_colorkey((0, 0, 0))
#         self.rect = self.image.get_rect()
#         # 爆弾を投下するemyから見た攻撃対象のbirdの方向を計算
#         self.vx, self.vy = calc_orientation(emy.rect, bird.rect)  
#         self.rect.centerx = emy.rect.centerx
#         self.rect.centery = emy.rect.centery+emy.rect.height//2
#         self.speed = 6

#     def update(self):
#         """
#         爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
#         引数 screen：画面Surface
#         """
#         self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
#         if check_bound(self.rect) != (True, True):
#             self.kill()


# class Beam(pg.sprite.Sprite):
#     """
#     ビームに関するクラス
#     ボス倒すための攻撃手段
#     障害物に当たるとビームは消滅
#     """
#     def __init__(self, bird: Bird, angle0 = 0):     #課題６でangle0を追加
#         """
#         ビーム画像Surfaceを生成する
#         引数 bird：ビームを放つこうかとん
#         """
#         super().__init__()

#         self.vx, self.vy = bird.dire
#         angle = math.degrees(math.atan2(-self.vy, self.vx)) + angle0        #ビームの回転角度に加算
#         self.image = pg.transform.rotozoom(pg.image.load(f"fig/beam.png"), angle, 1.0)
#         self.vx = math.cos(math.radians(angle))
#         self.vy = -math.sin(math.radians(angle))
#         self.rect = self.image.get_rect()
#         self.rect.centery = bird.rect.centery+bird.rect.height*self.vy
#         self.rect.centerx = bird.rect.centerx+bird.rect.width*self.vx
#         self.speed = 10

#     def update(self):
#         """
#         ビームを速度ベクトルself.vx, self.vyに基づき移動させる
#         引数 screen：画面Surface
#         """
#         self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
#         if check_bound(self.rect) != (True, True):
#             self.kill()


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


# class Enemy(pg.sprite.Sprite):
#     """
#     敵機に関するクラス
#     ボスのクラス（大きさだけいじればいいかな）
#     """
#     imgs = [pg.image.load(f"fig/alien{i}.png") for i in range(1, 4)]
    
#     def __init__(self):
#         super().__init__()
#         self.image = pg.transform.rotozoom(random.choice(__class__.imgs), 0, 0.8)
#         self.rect = self.image.get_rect()
#         self.rect.center = random.randint(0, WIDTH), 0
#         self.vx, self.vy = 0, +6
#         self.bound = random.randint(50, HEIGHT//2)  # 停止位置
#         self.state = "down"  # 降下状態or停止状態
#         self.interval = random.randint(50, 300)  # 爆弾投下インターバル

#     def update(self):
#         """
#         敵機を速度ベクトルself.vyに基づき移動（降下）させる
#         ランダムに決めた停止位置_boundまで降下したら，_stateを停止状態に変更する
#         引数 screen：画面Surface
#         """
#         if self.rect.centery > self.bound:
#             self.vy = 0
#             self.state = "stop"
#         self.rect.move_ip(self.vx, self.vy)


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


# class Gravity(pg.sprite.Sprite):
#     """
#     今回は、小さい敵と障害物と爆弾を消せる必殺技クラス
#     """
#     def __init__(self, life):
#         super().__init__()      #Groupのために継承

#         self.life = life
#         self.image = pg.Surface((WIDTH, HEIGHT))
#         self.image.set_alpha(128)
#         self.rect = self.image.get_rect()

#     def update(self):
#         self.life -= 1
#         if self.life <= 0:
#             self.kill()


# class EMP():
#     def __init__(self, emys, bombs, screen):
#         for emy in emys:
#             emy.interval = float("inf")
#             emy.image = pg.transform.laplacian(emy.image)

#         for bom in bombs:
#             bom.speed /= 2
#             bom.state = "inactive"

#         image = pg.Surface((WIDTH, HEIGHT))
#         image.fill((255, 255, 0))
#         image.set_alpha(200)

#         screen.blit(image, [0, 0])
#         pg.display.update()
#         time.sleep(0.05)


# class Shield(pg.sprite.Sprite):
#     def __init__(self, life, bird:Bird):
#         super().__init__()
#         self.life = life

#         self.image = pg.Surface((20, bird.rect.height * 2))
#         pg.draw.rect(self.image, (0, 0, 255), (0, 0, 10, bird.rect.height * 2))
#         self.rect = self.image.get_rect()

#         vx, vy = bird.dire  #向いてる方向のベクトルをvx, vyに代入
#         self.rect.centerx = bird.rect.centerx + vx * bird.rect.width
#         self.rect.centery = bird.rect.centery + vy * bird.rect.height
#         kakudo = math.degrees(math.atan2(-vy, vx))
#         self.image = pg.transform.rotozoom(self.image, kakudo, 1)
#         self.image.set_colorkey((0, 0, 0))      #ここに入れないと黒くなる

#     def update(self):
#         self.life -= 1
#         if self.life <= 0:
#             self.kill()


def main():
    pg.display.set_caption("走れ！こうかとん")
    screen = pg.display.set_mode((1100, 650))
    clock  = pg.time.Clock()
    move = 0
    tmr = 0
    maps = Map()    #マップを切り替えるため
    x = 0 #練習5


    # score = Score()
    bird = Bird()

    # bombs = pg.sprite.Group()
    # beams = pg.sprite.Group()
    exps = pg.sprite.Group()
    # emys = pg.sprite.Group()
    obstacle = pg.sprite.Group()
    platforms = pg.sprite.Group()
    icicles = pg.sprite.Group()

    life = Life(5)      
    # gravity = pg.sprite.Group()     #課題2 Groupにインスタンスを追加
    # shield = pg.sprite.Group()
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

            title_shade = pg.Surface((430, 150))
            title_shade.fill((0, 0, 0))
            title_shade.set_alpha(180)
            screen.blit(title_shade, (350, 250))
            font = pg.font.Font(None, 80)
            txt = font.render("Morning stage", True, (0, 255, 255))
            screen.blit(txt, (400, 300))
            pg.display.update()
            time.sleep(3)

        if tmr == 2000:
            #初期設定に戻す
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

        if tmr == 4000:
        #初期設定に戻す
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
            

        key_lst = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT: return

            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                # 2回までジャンプ可能
                if bird.jump_count < bird.max_jump:
                    bird.vy = -15
                    bird.jumping = True
                    bird.jump_count += 1
                    

        
        # for bomb in pg.sprite.spritecollide(bird, bombs, True):  # こうかとんと衝突した爆弾リスト
        #     if bird.state == "hyper":       #課題４の無敵時間判定のために条件分岐
        #         exps.add(Explosion(bomb, 50))
        #         score.value += 1
        #     else:
        #         bird.change_img(8, screen)  # こうかとん悲しみエフェクト
        #         score.update(screen)
        #         life.num -= 1       #課題１
        #         pg.display.update()
        #         if life.num <= 0:
        #             time.sleep(2)
        #             return  

        #     if event.type == pg.KEYDOWN and event.key == pg.K_RETURN:       #課題2の重力場判定
        #         if score.value >= 10:      #scoreクラスの中にvalueという名前で書かれていたため
        #             gravity.add(Gravity(400))
        #             score.value -= 10       #見せるために一時的に10にしているだけだからあとで200に変えて

        #     if event.type == pg.KEYDOWN and event.key == pg.K_e:        #課題３
        #         if score.value >= 20:
        #             EMP(emys, bombs, screen)
        #             score.value -= 20

        #     if event.type == pg.KEYDOWN and event.key == pg.K_RSHIFT:   #課題４
        #         if score.value >= 10:         #これも課題のため10にしておくけど、100に戻しておいて
        #             bird.state = "hyper"
        #             bird.hyper_life = 500
        #             score.value -= 10

        #     if event.type == pg.KEYDOWN and event.key == pg.K_s:    #課題５
        #         if score.value >= 0 and len(shield) == 0:
        #             shield.add(Shield(400, bird))
        #             score.value -= 0

        # if tmr%200 == 0:  # 200フレームに1回，敵機を出現させる
        #     emys.add(Enemy())

        # for emy in emys:
        #     if emy.state == "stop" and tmr%emy.interval == 0:
        #         # 敵機が停止状態に入ったら，intervalに応じて爆弾投下
        #         bombs.add(Bomb(emy, bird))

        # for emy in pg.sprite.groupcollide(emys, beams, True, True).keys():  # ビームと衝突した敵機リスト
        #     exps.add(Explosion(emy, 100))  # 爆発エフェクト
        #     score.value += 10  # 10点アップ
        #     bird.change_img(6, screen)  # こうかとん喜びエフェクト

        # for bomb in pg.sprite.groupcollide(bombs, beams, True, True).keys():  # ビームと衝突した爆弾リスト
        #     exps.add(Explosion(bomb, 50))  # 爆発エフェクト
        #     score.value += 1  # 1点アップ

        # for bomb in pg.sprite.spritecollide(bird, bombs, True):  # こうかとんと衝突した爆弾リスト
        #     if bird.state == "hyper":       #課題４の無敵時間判定のために条件分岐
        #         exps.add(Explosion(bomb, 50))
        #         score.value += 1
        #     else:
        #         bird.change_img(8, screen)  # こうかとん悲しみエフェクト
        #         score.update(screen)
        #         life.num -= 1       #課題１
        #         pg.display.update()
        #         if life.num <= 0:
        #             time.sleep(2)
        #             return     

        # for emy in pg.sprite.groupcollide(emys, gravity, True, False).keys():  # 重力場と敵機の衝突判定
        #     exps.add(Explosion(emy, 100))  # 爆発エフェクト

        # for bomb in pg.sprite.groupcollide(bombs, gravity, True, False):
        #     exps.add(Explosion(bomb, 50))

        # for bomb in pg.sprite.groupcollide(shield, bombs, True, True):      #課題５　防御壁
        #     exps.add(Explosion(bomb, 50))

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

        # beams.update()
        # beams.draw(screen)
        # emys.update()
        # emys.draw(screen)
        # bombs.update()
        # bombs.draw(screen)
        exps.update()
        exps.draw(screen)
        # score.update(screen)  
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