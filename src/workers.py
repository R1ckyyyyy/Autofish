import cv2
import re
import time
import os
from pathlib import Path
import mss
from PySide6.QtCore import QThread, Signal, Slot
from rapidocr_onnxruntime import RapidOCR
from src.vision import vision
from src.inputs import InputController
from src.config import cfg

class FishingWorker(QThread):
    """
    自动化钓鱼逻辑的核心线程
    """
    log_updated = Signal(str)
    status_updated = Signal(str)
    record_added = Signal(dict)

    def __init__(self):
        super().__init__()
        self.ocr = RapidOCR()
        self.running = False
        self.paused = True  # Start in a paused state
        self.inputs = InputController()
        self.vision = vision
        self.state = "finding_prompt"  # 初始状态
        # 确保截图目录存在
        screenshots_dir = cfg._get_base_path() / 'screenshots'
        if not screenshots_dir.exists():
            screenshots_dir.mkdir(parents=True)


    def run(self):
        """
        QThread 的入口点, 包含主循环
        """
        self.running = True
        
        # 启动预检
        self.log_updated.emit("正在执行启动环境预检...")
        env_checked = False
        
        # 1. 检查抛竿提示
        for key in ['F1_grayscale', 'F2_grayscale']:
            if self.vision.find_template(key, threshold=0.8):
                env_checked = True
                break
        
        # 3. 检查鱼饵数量
        if not env_checked:
            if self.vision.get_bait_amount() is not None:
                env_checked = True

        if env_checked:
             self.log_updated.emit("环境检查通过，开始运行。")
        else:
            self.log_updated.emit("⚠️ 未检测到游戏界面，请确保游戏在前台。")
            self.status_updated.emit("环境检查失败")
            # 自动暂停，等待用户调整
            self.pause()
            
        
        self.log_updated.emit("开始自动化钓鱼...")

        while self.running:
            while self.paused:
                if not self.running:
                    break
                self.msleep(100)  # 暂停时避免CPU空转

            if not self.running:
                break

            try:
                if self.state == "finding_prompt":
                    if self._cast_rod():
                        self.state = "waiting_for_bite"
                
                elif self.state == "waiting_for_bite":
                    if not self._wait_for_bite():
                        # 如果等待超时或失败，重置状态
                        self.state = "finding_prompt"
                    else:
                        self.state = "reeling_in"

                elif self.state == "reeling_in":
                    reel_in_finished = self._reel_in()
                    if reel_in_finished:
                        self._record_catch()
                        self.log_updated.emit("收起渔获, 准备下一轮。")
                        self.smart_sleep(0.5)
                        self.inputs.left_click()
                        self.smart_sleep(1.0)
                    # 无论成功与否，都重置到初始状态
                    self.state = "finding_prompt"

            except Exception as e:
                self.log_updated.emit(f"发生错误: {e}")
                self.pause()
                self.status_updated.emit(f"错误: {e}, 已暂停")

            # 循环间隔，等待指定时间后再进行下一轮
            self.smart_sleep(cfg.cycle_interval) 

        self.log_updated.emit("自动化钓鱼已停止。")

    def _cast_rod(self):
        """
        抛竿阶段
        """
        if not self.running: return False
        self.status_updated.emit("抛竿阶段")
        self.log_updated.emit("正在寻找抛竿提示...")

        start_time = time.time()
        timeout = 10
        cast_rod_region = cfg.get_rect("cast_rod")

        while time.time() - start_time < timeout:
             if not self.running: return False
             while self.paused: self.msleep(100)

             for key in ['F1_grayscale', 'F2_grayscale']:
                 # 在限定的“抛竿检测”区域内寻找图标
                 if self.vision.find_template(key, region=cast_rod_region, threshold=0.8):
                     self.log_updated.emit(f"检测到抛竿提示, 准备抛竿。")
                     self.inputs.hold_mouse(cfg.cast_time)
                     
                     # -- 状态转换验证 --
                     self.smart_sleep(1.0) # 等待UI响应
                     
                     verification_start_time = time.time()
                     verification_timeout = 5 # 5秒验证超时
                     wait_bite_region = cfg.get_rect("wait_bite")
                     
                     while time.time() - verification_start_time < verification_timeout:
                         # 成功条件: 抛竿区图标消失 AND 等待区图标出现
                         cast_icon_gone = not self.vision.find_template(key, region=cast_rod_region, threshold=0.8)
                         wait_icon_appeared = self.vision.find_template(key, region=wait_bite_region, threshold=0.8)

                         if cast_icon_gone and wait_icon_appeared:
                             self.log_updated.emit("已抛竿, 进入等待咬钩状态。")
                             return True # 抛竿成功
                         
                         self.msleep(200)

                     # 如果超时，说明抛竿失败
                     bait_amount = self.vision.get_bait_amount()
                     if bait_amount == 0:
                         self.log_updated.emit("错误：抛竿后状态未改变，且鱼饵数量为0。")
                         self.pause(reason="没有鱼饵了")
                     else:
                         self.log_updated.emit("错误：抛竿后状态未改变，可能鱼桶已满。")
                         self.pause(reason="鱼桶可能已满")
                     return False
                     # -- 验证结束 --

             self.msleep(200)

        self.log_updated.emit("抛竿超时, 未找到抛竿提示。")
        return False


    def _wait_for_bite(self):
        """
        等待鱼儿咬钩, 通过检测鱼饵数量变化来判断
        """
        if not self.running: return False
        self.status_updated.emit("等待咬钩")
        self.log_updated.emit("等待鱼饵数量减少...")
        
        # 增加初始检查: 如果根本获取不到鱼饵数量，说明可能没抛竿或界面不对
        initial_check_retries = 3
        initial_bait = None

        # 在等待循环前，先获取一次初始鱼饵数量
        for _ in range(initial_check_retries):
            if not self.running: return False
            while self.paused: self.msleep(100)
            
            initial_bait = self.vision.get_bait_amount()
            if initial_bait is not None:
                break
            self.smart_sleep(0.5)
            
        if initial_bait is None:
            self.log_updated.emit("警告: 无法获取初始鱼饵数量，可能未抛竿或已收杆。重置循环。")
            return False # 返回False将导致主循环continue，从而重新尝试抛竿

        # 进入等待咬钩的主循环
        timeout = 120  # 等待咬钩的超时时间
        start_time = time.time()
        while time.time() - start_time < timeout:
            if not self.running or self.paused:
                return False

            current_bait = self.vision.get_bait_amount()
            if current_bait is not None and current_bait < initial_bait:
                self.log_updated.emit(f"检测到鱼饵数量变化 ({initial_bait} -> {current_bait}), 判定为咬钩。")
                return True
            
            self.msleep(200) # 循环检测间隔

        self.log_updated.emit("等待咬钩超时。")
        return False



    def _reel_in(self):
        """
        收杆阶段, 实现收放循环。
        仅通过寻找星星图标来判断何时停止收线。
        """
        if not self.running: return False
        self.status_updated.emit("上鱼了! 开始收杆!")
        self.log_updated.emit("进入收放线循环...")
        
        star_region = cfg.get_rect("reel_in_star")

        for i in range(cfg.max_pulls):
            if not self.running or self.paused:
                return False

            self.log_updated.emit(f"第 {i+1}/{cfg.max_pulls} 次尝试: 收线...")
            
            # --- START: 改进的收线逻辑，可处理中断 ---
            self.inputs.press_mouse_button()
            pull_start_time = time.time()
            pull_duration = cfg.reel_in_time

            try:
                while time.time() - pull_start_time < pull_duration:
                    if not self.running or self.paused:
                        # 如果在收线时暂停或停止，必须释放鼠标
                        return False # 直接退出_reel_in

                    time.sleep(0.05) # 短暂轮询间隔，降低CPU占用
            finally:
                # 确保无论循环如何退出（正常结束、break或异常），鼠标都会被释放
                self.inputs.release_mouse_button()
            # --- END: 改进的收线逻辑 ---

            self.log_updated.emit("放线...")
            # Use smart_sleep but consider jitter. smart_sleep handles intervals > 0.1s better. 
            # If jittered time is very short, simple sleep is fine, but for consistency we can use smart_sleep
            # provided input jitter doesn't make it negative.
            sleep_duration = self.inputs.add_jitter(cfg.release_time)
            self.smart_sleep(sleep_duration)

            # --- START: “鱼跑了”检测 ---
            # 在放线间隙，检查是否意外回到了抛竿状态
            cast_rod_region = cfg.get_rect("cast_rod")
            for key in ['F1_grayscale', 'F2_grayscale']:
                if self.vision.find_template(key, region=cast_rod_region, threshold=0.8):
                    self.log_updated.emit("在收线过程中检测到抛竿提示，判定为鱼跑了！")
                    self.status_updated.emit("鱼跑了!")
                    self._record_event("鱼跑了") # 记录事件
                    return False # 返回False，主循环会继续下一次尝试
            # --- END: “鱼跑了”检测 ---

            # 检测是否成功钓到鱼
            if self.vision.find_template('star_grayscale', region=star_region, threshold=0.7):
                self.log_updated.emit("检测到星星，成功！")
                return True

        self.log_updated.emit("达到最大拉杆次数，仍未检测到星星。")
        return False


    def _record_catch(self):
        """
        截图识别渔获信息, 并发送信号
        """
        if not self.running: return False
        self.status_updated.emit("记录渔获")
        self.log_updated.emit("正在识别渔获信息...")

        self.smart_sleep(1.0) # 等待UI稳定

        # 尝试检测并点击"收起"按钮 (shangyu)
        shangyu_region = cfg.get_rect("shangyu")
        if self.vision.find_template('shangyu_grayscale', region=shangyu_region, threshold=0.8):
             self.log_updated.emit("检测到'收起'按钮，确认上鱼成功。")
             # shangyu仅作为状态指示，不作为点击位置，稍后统一左键点击关闭
             # 注意：这里我们稍后点击，先截图OCR，防止点击后弹窗消失
        
        rect = cfg.get_rect("ocr_area")
        if not rect:
            self.log_updated.emit("错误: 未在配置中找到 'ocr_area' 区域。")
            return False

        image = self.vision.screenshot(rect)
        if image is None:
            self.log_updated.emit("截图失败。")
            return False

        result, _ = self.ocr(image)

        if not result:
            self.log_updated.emit("OCR未能识别到有效的渔获信息。")
            try:
                # Debug: save the failed image
                debug_dir = cfg._get_base_path() / 'debug_screenshots'
                if not debug_dir.exists():
                    debug_dir.mkdir(parents=True)
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                debug_filename = debug_dir / f"ocr_failed_{timestamp}.png"
                cv2.imwrite(str(debug_filename), image)
                self.log_updated.emit(f"OCR失败，已保存调试截图: {debug_filename}")
            except Exception as e:
                self.log_updated.emit(f"保存调试截图失败: {e}")
            return False
        
        full_text = "".join([res[1] for res in result])
        self.log_updated.emit(f"识别到原始文本: {full_text}")
        
        # 检测是否为新纪录
        is_new_record = "新纪录" in full_text or "新记录" in full_text
        if is_new_record:
            self.log_updated.emit("检测到新纪录！")
            # 移除关键词以免干扰后续解析
            full_text = full_text.replace("新纪录", "").replace("新记录", "")
        
        # 增强容错：只要文本中包含关键字即可，不需要精确匹配
        if "你钓到了" not in full_text:
            # 尝试模糊匹配或查找后续特征，如"千克"
            if "千克" in full_text:
                self.log_updated.emit("未检测到'你钓到了'前缀，但发现重量单位，尝试继续解析。")
                # 假设所有文本都是有效信息
            else:
                self.log_updated.emit("OCR结果不包含关键字，判定为钓鱼失败。")
                return False

        cleaned_text = full_text.replace(" ", "").replace("(", "").replace(")", "")

        # 检测并清理新纪录关键词
        # 已经在前一步做了初步检测，这里进行清理以防止干扰后续解析
        new_record_keywords = ["新纪录", "新记录", "首次捕获", "首次"]
        for kw in new_record_keywords:
            if kw in cleaned_text:
                is_new_record = True # 再次确认
                cleaned_text = cleaned_text.replace(kw, "")

        try:
            # 移除固定的前缀 "你钓到了" (如果存在)
            if "你钓到了" in cleaned_text:
                text_after_prefix = cleaned_text.split("你钓到了", 1)[-1]
            else:
                text_after_prefix = cleaned_text

            # 定义所有可能的品质
            # 包含繁体字和同义词
            qualities = ['标准', '非凡', '稀有', '史诗', '传说', '传奇', '標準', '傳說', '傳奇']
            
            # 提取重量
            weight = 0.0
            weight_match = re.search(r"(\d+\.?\d*)千克", text_after_prefix)
            if weight_match:
                weight = float(weight_match.group(1))
                # 从字符串中移除重量信息以便于解析鱼名和品质
                text_after_prefix = text_after_prefix.replace(weight_match.group(0), "").strip()

            # 提取品质
            quality = "普通" # 默认值
            for q in qualities:
                if q in text_after_prefix:
                    quality = q
                    # 从字符串中移除品质信息
                    text_after_prefix = text_after_prefix.replace(q, "").strip()
                    break
            
            # 品质名称归一化
            if quality in ['传奇', '傳奇', '傳說']:
                quality = '传说'
            elif quality == '標準':
                quality = '标准'
            
            # 剩下的就是鱼名，移除任何特殊字符
            fish_name = re.sub(r'[★☆]', '', text_after_prefix).strip()
            # 后处理：移除鱼名末尾的数字
            fish_name = re.sub(r'\d+$', '', fish_name)
            
            if not fish_name:
                self.log_updated.emit(f"无法从 '{full_text}' 中解析出鱼名。")
                return False

            self.log_updated.emit(f"解析结果 -> 鱼名: '{fish_name}', 品质: '{quality}', 重量: {weight}")

        except Exception as e:
            self.log_updated.emit(f"数据解析过程中发生错误: {e}")
            return False

        self.log_updated.emit(f"钓到鱼: {fish_name}, 重量: {weight}kg, 品质: {quality}")

        catch_data = {'name': fish_name, 'weight': weight, 'quality': quality, 'is_new_record': is_new_record}
        self.record_added.emit(catch_data)

        # Persistence: Write to CSV
        try:
            base_path = cfg._get_base_path()
            data_dir = base_path / 'data'
            if not data_dir.exists():
                data_dir.mkdir(parents=True)
            
            csv_file = data_dir / 'records.csv'
            file_exists = csv_file.is_file()
            
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            
            with open(csv_file, 'a', encoding='utf-8') as f:
                if not file_exists:
                    f.write('Timestamp,Name,Quality,Weight,IsNewRecord\n')
                
                # Check if existing CSV has the new column, if not, we can't easily append it without rewriting.
                # However, Python's csv module is flexible.
                # To be backward compatible and non-destructive:
                # We will just append the new field. Old parsers (if any) might ignore it or fail.
                # But since we control the reader in records_interface, we can handle it there.
                
                # 兼容性处理：如果文件已存在但没有新列，我们附加数据。读取时会处理缺失列。
                is_new_record_str = 'Yes' if is_new_record else 'No'
                f.write(f'{timestamp},{fish_name},{quality},{weight},{is_new_record_str}\n')
                
        except Exception as e:
            self.log_updated.emit(f"写入记录文件失败: {e}")

        if quality == "传说":
            self.log_updated.emit("哇! 钓到了传说品质的鱼, 正在截图保存...")
            try:
                with mss.mss() as sct:
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    filename = cfg._get_base_path() / 'screenshots' / f"legendary_{fish_name.replace(':', '_')}_{timestamp}.png"
                    sct.shot(output=str(filename))
                    self.log_updated.emit(f"截图已保存至 {filename}")
            except Exception as e:
                self.log_updated.emit(f"截图失败: {e}")
        
        # 无论结果如何，尝试点击"收起"按钮以关闭弹窗，进入下一轮
        # 优化：交由主循环统一处理点击，避免此处重复点击导致异常
        return True


    def _record_event(self, event_type: str):
        """
        记录一个通用事件到CSV文件, 例如 "鱼跑了"
        """
        try:
            base_path = cfg._get_base_path()
            data_dir = base_path / 'data'
            if not data_dir.exists():
                data_dir.mkdir(parents=True)
            
            csv_file = data_dir / 'records.csv'
            file_exists = csv_file.is_file()
            
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            
            with open(csv_file, 'a', encoding='utf-8') as f:
                if not file_exists:
                    f.write('Timestamp,Name,Quality,Weight\n')
                # 对于事件，我们只记录名称，其他字段留空
                f.write(f'{timestamp},{event_type},,\n')
                
        except Exception as e:
            self.log_updated.emit(f"写入事件记录失败: {e}")

    def pause(self, reason: str = None):
        """
        暂停线程并重置状态
        :param reason: 暂停的具体原因，如果不为None，将显示此状态，否则显示默认的"已暂停"
        """
        self.paused = True
        self.state = "finding_prompt"  # 重置状态到初始阶段
        self.inputs.ensure_mouse_up()
        
        status_text = reason if reason else "已暂停"
        self.status_updated.emit(status_text)
        self.log_updated.emit(f"脚本暂停，原因: {status_text}，状态已重置，已强制松开鼠标。")


    def resume(self):
        """
        恢复线程
        """
        self.paused = False
        self.status_updated.emit("运行中")
        self.log_updated.emit("自动化已恢复。")


    def stop(self, reason: str = None):
        """
        安全地停止线程
        :param reason: 停止的具体原因，将作为最终状态显示在GUI上
        """
        self.running = False
        # Remove self.wait() to prevent GUI freezing. 
        # The main thread should wait for us, not us blocking inside our own stop method called from main thread.
        # But actually, stop() is called from main thread. If we wait() here, we block main thread until run() finishes.
        # This IS the correct way usually, but if run() is blocked, we freeze.
        # We already improved run() loop responsiveness. 
        # However, if 'wait' causes issues, we can remove it and let closeEvent handle the wait with timeout.
        final_status = reason if reason else "已停止"
        self.status_updated.emit(f"{final_status}")
        self.log_updated.emit(f"收到停止信号, 原因: {final_status}")

    def smart_sleep(self, duration):
        """
        可中断的睡眠函数，能够及时响应停止信号
        """
        end_time = time.time() + duration
        while self.running and time.time() < end_time:
            sleep_time = min(0.1, end_time - time.time())
            if sleep_time > 0:
                time.sleep(sleep_time)

    @Slot(str)
    def update_preset(self, preset_name):
        """
        线程安全的槽函数，用于更新配置预设
        """
        try:
            self.log_updated.emit(f"接收到预设更改请求: {preset_name}")
            # 在工作线程中安全地加载新配置
            cfg.load_preset(preset_name)
            self.log_updated.emit(f"配置预设 '{preset_name}' 已成功加载。")
        except Exception as e:
            self.log_updated.emit(f"错误：加载预设 '{preset_name}' 失败: {e}")


class PopupWorker(QThread):
    """
    一个专门用于在后台检测和处理游戏弹窗的独立工作线程.
    """
    log_updated = Signal(str)

    def __init__(self):
        super().__init__()
        self.running = False
        self.vision = vision
        self.inputs = InputController()

    def run(self):
        """
        QThread 的入口点, 包含主循环, 持续检测弹窗.
        """
        self.running = True
        self.log_updated.emit("弹窗处理服务已启动。")

        while self.running:
            try:
                # --- 加时弹窗检测 ---
                jiashi_region = cfg.get_rect("jiashi_popup")
                if self.vision.find_template('chang_grayscale', region=jiashi_region, threshold=0.8):
                    self.log_updated.emit("检测到加时弹窗，正在处理...")
                    if cfg.enable_jiashi:
                        target_x, target_y = cfg.get_center_anchored_pos(cfg.BTN_JIASHI_YES)
                        self.inputs.click(target_x, target_y)
                        self.log_updated.emit("已自动点击'是'。")
                    else:
                        target_x, target_y = cfg.get_center_anchored_pos(cfg.BTN_JIASHI_NO)
                        self.inputs.click(target_x, target_y)
                        self.log_updated.emit("已自动点击'否'。")
                    
                    self.msleep(1000) # 点击后等待一下，防止重复检测

            except Exception as e:
                self.log_updated.emit(f"[弹窗处理服务] 发生错误: {e}")
            
            # 控制循环频率
            self.msleep(500) # 每0.5秒检测一次

        self.log_updated.emit("弹窗处理服务已停止。")

    def stop(self):
        """
        安全地停止线程.
        """
        self.running = False
        # Remove wait() here too
        self.log_updated.emit("收到停止弹窗处理服务的信号。")
