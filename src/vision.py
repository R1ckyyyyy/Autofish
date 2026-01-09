import cv2
import numpy as np
import mss
import os
import time
import sys
from src.config import cfg

class Vision:
    def __init__(self):
        print("Initializing Vision (Lazy)...")
        # self.sct is removed to ensure thread safety by creating a new instance per capture
        self.templates = {}
        self._loaded = False
        # self.load_templates() # Moved to lazy load
        # print(f"Vision initialized. Loaded {len(self.templates)} templates.")

    def _ensure_loaded(self):
        if not self._loaded:
            self.load_templates()
            self._loaded = True
            print(f"Vision templates loaded. Count: {len(self.templates)}")

    def load_templates(self):
        print("Loading templates from disk...")
        resources_path = cfg._get_base_path() / 'resources'
            
        for filename in os.listdir(resources_path):
            if filename.endswith('.png'):
                # Load image with alpha channel, supporting Chinese characters in path
                # img = cv2.imread(os.path.join(resources_path, filename), cv2.IMREAD_UNCHANGED)
                file_path = os.path.join(resources_path, filename)
                img = cv2.imdecode(np.fromfile(file_path, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
                if img is None:
                    continue

                # Extract template name from filename
                template_name = os.path.splitext(filename)[0]

                # Resize image based on config scale
                if cfg.scale != 1.0:
                    width = int(img.shape[1] * cfg.scale)
                    height = int(img.shape[0] * cfg.scale)
                    img = cv2.resize(img, (width, height), interpolation=cv2.INTER_AREA)

                self.templates[template_name] = img

    def screenshot(self, region=None):
        with mss.mss() as sct:
            if region is None:
                # Use the primary monitor
                monitor = sct.monitors[1]
            else:
                monitor = {'left': region[0], 'top': region[1], 'width': region[2], 'height': region[3]}

            # Grab the data
            sct_img = sct.grab(monitor)

            # Convert to a numpy array
            img = np.array(sct_img)

            # Convert BGRA to BGR
            return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    def get_bait_amount(self, region=None, threshold=0.7):
        if region is None:
            region = cfg.get_rect('bait_count')
        
        # print(f"DEBUG: Screenshotting for bait amount at region {region}")
        screenshot = self.screenshot(region)
        
        # 用户逻辑：切片宽度 BAIT_CROP_WIDTH1_BASE (15)
        # 假设 region 是两个数字的宽度，我们主要想识别个位数和十位数
        # 但这里的逻辑稍显复杂：
        # 如果是两位数，我们需要分割。如果是1位数，可能只需要一部分。
        # 简单起见，我们先尝试在整个区域找数字。如果失败，或者结果离谱，
        # 我们按照用户提示的宽度进行切分处理。
        
        # 按照用户指示，鱼饵计数区域为 (2318, 1296, 30, 22)
        # 切片宽 15。这意味着可能有两部分：左边 (十位) 和 右边 (个位)
        # 或者这是一个滚动计数器？
        # 让我们实现一个特定的切分识别逻辑。
        
        h, w = screenshot.shape[:2]
        crop_width = int(cfg.BAIT_CROP_WIDTH1_BASE * cfg.scale)
        
        # 确保截图够宽
        if w < crop_width:
             # 如果不够宽，直接识别整个
             return self._detect_digits(screenshot, threshold)

        # 尝试切分为左右两部分 (假设最大两位数)
        # 右侧对齐切片 (个位)
        right_part = screenshot[:, w-crop_width:w]
        # 左侧剩余部分 (十位)
        left_part = screenshot[:, 0:w-crop_width]
        
        # 识别右侧 (个位)
        digit_ones = self._detect_single_digit(right_part, threshold)
        
        # 识别左侧 (十位) - 可能为空
        digit_tens = self._detect_single_digit(left_part, threshold)
        
        if digit_ones is not None:
            if digit_tens is not None:
                return digit_tens * 10 + digit_ones
            else:
                return digit_ones
        
        # 如果切分识别失败，回退到全图识别
        return self._detect_digits(screenshot, threshold)

    def _detect_single_digit(self, img, threshold):
        """
        Detects the single best matching digit in a small image crop.
        Returns the digit (int) or None.
        """
        self._ensure_loaded()
        gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        best_match = -1
        max_score = -1
        
        for i in range(10):
            template_name = f'{i}_grayscale'
            template = self.templates.get(template_name)
            if template is None:
                continue
                
            # Resize template if it's larger than the image crop
            t_h, t_w = template.shape[:2]
            i_h, i_w = gray_img.shape[:2]
            
            if t_h > i_h or t_w > i_w:
                 # Skip if template is bigger than crop (shouldn't happen if config is right)
                 continue

            res = cv2.matchTemplate(gray_img, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
            
            if max_val > max_score:
                max_score = max_val
                best_match = i
        
        if max_score >= threshold:
            return best_match
        
        return None

    def _detect_digits(self, img, threshold):
        """
        Helper method to detect digits in a given image (BGR).
        """
        self._ensure_loaded()
        gray_screenshot = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        found_digits = []
        for i in range(10):
            template_name = f'{i}_grayscale'
            template = self.templates.get(template_name)
            if template is None:
                continue

            res = cv2.matchTemplate(gray_screenshot, template, cv2.TM_CCOEFF_NORMED)
            loc = np.where(res >= threshold)
            for pt in zip(*loc[::-1]):
                found_digits.append({'digit': i, 'x': pt[0]})

        if not found_digits:
            return None
        
        found_digits.sort(key=lambda d: d['x'])

        # Filter out overlapping detections
        unique_digits = []
        if found_digits:
            unique_digits.append(found_digits[0])
            for i in range(1, len(found_digits)):
                # If the x-coordinate is far enough from the last one, it's a new digit
                if found_digits[i]['x'] > unique_digits[-1]['x'] + 5: # 5px horizontal threshold
                    unique_digits.append(found_digits[i])

        try:
            number_str = "".join([str(d['digit']) for d in unique_digits])
            return int(number_str)
        except (ValueError, TypeError):
            return None

    def wait_for_bait_change(self, timeout=30):
        """
        Waits for the bait count to decrease.
        """
        initial_amount = self.get_bait_amount()
        if initial_amount is None:
            print("Could not determine initial bait amount.")
            return False

        start_time = time.time()
        while time.time() - start_time < timeout:
            current_amount = self.get_bait_amount()
            if current_amount is not None and current_amount < initial_amount:
                print(f"Bait amount changed from {initial_amount} to {current_amount}.")
                return True
            time.sleep(0.5)  # Polling interval
        
        print("Timeout waiting for bait change.")
        return False

    def find_template(self, template_name, region=None, threshold=0.8):
        self._ensure_loaded()
        screenshot = self.screenshot(region)
        template = self.templates.get(template_name)

        if template is None:
            raise ValueError(f"Template '{template_name}' not found.")

        # Handle alpha channel and dimensionality
        if len(template.shape) == 3:
            if template.shape[2] == 4:
                # Separate the alpha channel as a mask
                mask = template[:,:,3]
                template = template[:,:,:3]
                # Use the mask in template matching
                result = cv2.matchTemplate(screenshot, template, cv2.TM_CCORR_NORMED, mask=mask)
            else:
                # BGR Template
                result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        else:
            # Grayscale Template - convert screenshot to grayscale for matching
            gray_screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
            result = cv2.matchTemplate(gray_screenshot, template, cv2.TM_CCOEFF_NORMED)

        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val >= threshold:
            # Get the center of the found template
            template_w = template.shape[1]
            template_h = template.shape[0]
            center_x = max_loc[0] + template_w // 2
            center_y = max_loc[1] + template_h // 2
            return (center_x, center_y)
        
        return None

    def draw_debug_rects(self, image, config):
        """
        Draw debug rectangles with Chinese labels and a legend on the image.
        """
        # --- DEBUGGING: Remove the big red square ---
        print("[DEBUG] Entering draw_debug_rects.")
        # cv2.rectangle(image, (0, 0), (100, 100), (0, 0, 255), -1) # Big Red Square REMOVED
        print(f"[DEBUG] Received config with {len(config)} items.")
        
        label_map = {
            'cast_rod': '抛竿检测',
            'cast_rod_ice': '冰钓抛竿',
            'wait_bite': '咬钩等待',
            'reel_in': '收杆检测',
            'bait_count': '鱼饵计数',
            'f3_menu': 'F3菜单',
            'repair': '修理检测',
            'shangyu': '收鱼检测',
            'reel_in_star': '收杆判定',
            'jiashi_popup': '加时弹窗',
            'ocr_area': 'OCR区域'
        }
        
        font_cjk = None
        pil_available = False
        font_load_error = ""

        try:
            from PIL import Image, ImageDraw, ImageFont
            pil_available = True
            
            # Try to load a font that supports Chinese
            try:
                font_cjk = ImageFont.truetype("msyh.ttc", 15)
            except IOError:
                try:
                    font_cjk = ImageFont.truetype("simhei.ttf", 15)
                except IOError:
                    font_load_error = "未找到中文字体(msyh.ttc, simhei.ttf)"
                    font_cjk = ImageFont.load_default()
        except ImportError:
            font_load_error = "PIL(Pillow)库未安装"
            print("PIL not found, falling back to English labels for debug overlay.")

        # If PIL is not available, draw basic boxes with OpenCV and return
        if not pil_available:
            cv2.putText(image, font_load_error, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)
            for name, rect_data in config.items():
                if name == 'scale' or not isinstance(rect_data, list): continue
                x, y, w, h = rect_data
                cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(image, name, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            return image

        # --- PIL Drawing Logic ---
        # 1. Convert OpenCV image to PIL image
        img_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil, 'RGBA') # Draw with transparency support

        # 2. Draw everything directly on the PIL image
        # --- Draw Legend Box ---
        legend_x, legend_y = 10, 10
        legend_line_height = 20
        legend_width = 350
        legend_content = ["调试图例:"]
        if font_load_error:
            legend_content.append(font_load_error)
        
        # Create a dictionary of rects that are valid and should be in the legend
        rects_for_legend = {k: config[k] for k in label_map if k in config and isinstance(config.get(k), list)}
        legend_content.extend([f"- {label_map[name]}: ({rect[0]},{rect[1]},{rect[2]},{rect[3]})" for name, rect in rects_for_legend.items()])

        legend_height = len(legend_content) * legend_line_height + 10

        # Draw legend background (semi-transparent)
        draw.rectangle(
            [legend_x, legend_y, legend_x + legend_width, legend_y + legend_height],
            fill=(0, 0, 0, 128)
        )
        # Draw legend text
        for i, text in enumerate(legend_content):
             draw.text(
                (legend_x + 5, legend_y + 5 + i * legend_line_height),
                text,
                font=font_cjk,
                fill=(255, 255, 255)
            )

        # --- Draw Rectangles and Labels ---
        for name, rect_data in config.items():
            if name == 'scale' or not isinstance(rect_data, list):
                continue
            
            # --- FINAL DEBUG STEP ---
            print(f"[DEBUG] Drawing rect: {name} with data {rect_data}")

            x, y, w, h = rect_data
            
            # Draw rectangle outline
            draw.rectangle([x, y, x + w, y + h], outline=(0, 255, 0), width=2)
            
            # Prepare label text
            label_text = label_map.get(name, name)
            
            # Use textbbox for modern Pillow, fallback to textsize
            try:
                bbox = draw.textbbox((0, 0), label_text, font=font_cjk)
                text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            except AttributeError:
                 text_w, text_h = draw.textsize(label_text, font=font_cjk)

            text_x = x
            text_y = y - text_h - 5
            if text_y < 0: text_y = y + h + 5

            # Draw semi-transparent background for the label
            draw.rectangle([text_x, text_y, text_x + text_w, text_y + text_h], fill=(0, 0, 0, 128))
            draw.text((text_x, text_y), label_text, font=font_cjk, fill=(0, 255, 0))

        # 3. Convert back to OpenCV image and update the original
        image[:] = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
        
        print("[DEBUG] Exiting draw_debug_rects.")
        return image

# Instantiate the vision class to be used by other modules
vision = Vision()
