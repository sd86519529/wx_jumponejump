from PIL import Image
import time
import os
import re
import subprocess
import random
import json

'''
思路：
	1. 配置
	2. 截图
	3. 分析棋子，棋盘坐标
	4. 计算出他们的距离
	5. 根据距离计算出压手机的时间，然后执行
	6. 等待1-3秒
	7. （2-6循环）


'''


def get_screen_size():
    '''获取手机屏幕的分辨率'''
    # 返回1920x1080这样的数据
    size_str = os.popen('adb shell wm size').read()
    if not size_str:
        print('please install adb and 驱动')
        exit()
    m = re.search('(\d+)x(\d+)', size_str)
    if m:
        print(m)
        return '%sx%s' % (m.group(2), m.group(1))


def init():
    '''配置文件'''
    # 获取分辨率
    screen_size = get_screen_size()
    config_file_path = 'config/%s/config.json' % screen_size
    if os.path.exists(config_file_path):
        with open(config_file_path, 'r') as f:
            print('Load config file from %s' % config_file_path)
            return json.loads(f.read())
    else:
        with open('config/default.json', 'r') as f:
            print('Load default config')
            return json.loads(f.read())


def screenshot_image():
    '''获取截图内容,加入截图名称为1.png adb shell screencap -p'''
    process = subprocess.Popen('adb shell screencap -p', shell=True, stdout=subprocess.PIPE)
    screenshot = process.stdout.read()
    # print(type(screenshot))
    screenshot = screenshot.replace(b'\r\r\n', b'\n')
    # print(screenshot)
    with open('1.png', 'wb') as f:
        f.write(screenshot)


def find_piece_board(image, Config):
    '''通过图片和配置文件来获取棋子和棋盘的x,y'''
    # 获取图片的宽和高
    wight, hight = image.size
    scan_y_start = 0
    piece_y_max = 0
    # 拿到图片的像素矩阵对象
    img = image.load()
    # 扫描 下面去掉1/3 上面去掉1/3 以50px步长来扫描
    for i in range(hight // 3, hight * 2 // 3):
        first_pixel = img[0, i]
        for j in range(1, wight):
            pixel = img[j, i]
            # 如果不是纯色的，跳出，扫描出y轴最大值的界限
            if first_pixel[:-1] != pixel[:-1]:
                scan_y_start = i
                break
        if scan_y_start != 0:
            break
    # 开始扫描棋子
    left = 0
    right = 0
    for i in range(scan_y_start, hight * 2 // 3):
        flag = True
        for j in range(wight // 8, wight * 7 // 8):  # 切掉左右的1/8
            pixel = img[j, i]
            # 根据棋子的颜色，找到最后一行的点的起始和末尾
            if (50 < pixel[0] < 60) and (53 < pixel[1] < 63) and (95 < pixel[2] < 110):
                if flag:
                    left = j
                    flag = False
                right = j
                piece_y_max = max(i, piece_y_max)
    piece_x = (left + right) // 2
    piece_y = piece_y_max - Config['piece_base_height_1_2']
    # 计算方块的最中间距离 首先方块和棋子不在同一侧
    board_x = 0
    board_y = 0
    if piece_x < wight / 2:
        board_x_start = piece_x
        board_x_end = wight
    else:
        board_x_start = 0
        board_x_end = piece_x

    for i in range(int(hight / 3), int(hight * 2 / 3)):
        last_pixel = img[0, i]
        if board_x or board_y:
            break
        board_x_sum = 0
        board_x_c = 0

        for j in range(int(board_x_start), int(board_x_end)):
            pixel = img[j, i]

            # 下一个棋盘紧贴着棋子

            if abs(j - piece_x) < Config['piece_body_width']:
                continue

            if abs(pixel[0] - last_pixel[0]) + abs(pixel[1] - last_pixel[1]) + abs(pixel[2] - last_pixel[2]) > 10:
                board_x_sum += j
                board_x_c += 1
        if board_x_sum:
            # 最高棋盘的平均横坐标
            board_x = board_x_sum / board_x_c
            board_y = i
    return piece_x, piece_y, board_x, board_y


def jump(distance, Config):
    '''通过两点之间的距离和配置文件中的系数来模拟用户按压屏幕'''
    param = Config['press_ratio']
    take_x = Config['swipe']['x'][0]
    take_x2 = Config['swipe']['x'][1]
    take_y = Config['swipe']['y'][0]
    take_y2 = Config['swipe']['y'][1]
    pass_time = distance * param
    pass_time = int(pass_time)
    print(pass_time, take_x, take_x2, take_y, take_y2)
    cmd = 'adb shell input swipe {x1} {y1} {x2} {y2} {duration}'.format(
        x1=take_x,
        x2=take_x2,
        y1=take_y,
        y2=take_y2,
        duration=pass_time
    )
    print(cmd)
    os.system(cmd)


def run():
    '''主函数'''
    '''读取配置文件'''
    Config = init()
    print(Config)
    while True:
        '''获取截图内容'''
        screenshot_image()
        image = Image.open('1.png')
        piece_x, piece_y, board_x, board_y = find_piece_board(image, Config)
        # 通过piece 和board的xy来计算两点之间的距离
        distance = ((piece_x - board_x) ** 2 + (piece_y - board_y) ** 2) ** 0.5
        print(distance)
        jump(distance, Config)
        # 随机按压时间
        time.sleep(1 + random.random() * 2)


if __name__ == '__main__':
    run()
