"""
网页截图捕获模块
Website Screenshot Capture Module
"""
import os
import time
from typing import Dict, List, Optional, Tuple
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
import io
import re

from ..utils.logger import get_logger

logger = get_logger(__name__)

class ScreenshotCapture:
    """网页截图捕获器"""
    
    # 常用设备尺寸
    DEVICE_SIZES = {
        'desktop': (1920, 1080),
        'laptop': (1366, 768),
        'tablet': (768, 1024),
        'mobile': (375, 667),
        'iphone': (414, 896),
        'android': (360, 640)
    }
    
    def __init__(self, browser: str = 'chrome', headless: bool = True, language: str = 'en-US'):
        """
        初始化截图捕获器
        
        Args:
            browser: 浏览器类型 ('chrome', 'firefox')
            headless: 是否无头模式
            language: 设置localStorage中的语言 (默认: 'en-US')
        """
        self.browser = browser
        self.headless = headless
        self.language = language
        self.driver = None
        
    def _setup_driver(self, device_size: Tuple[int, int] = None):
        """设置浏览器驱动"""
        try:
            if self.browser.lower() == 'chrome':
                options = ChromeOptions()
                if self.headless:
                    options.add_argument('--headless')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-gpu')
                options.add_argument('--disable-extensions')
                
                # 设置浏览器语言偏好
                if self.language:
                    options.add_argument(f'--lang={self.language}')
                    options.add_experimental_option('prefs', {
                        'intl.accept_languages': self.language
                    })
                
                if device_size:
                    options.add_argument(f'--window-size={device_size[0]},{device_size[1]}')
                
                self.driver = webdriver.Chrome(options=options)
                
            elif self.browser.lower() == 'firefox':
                options = FirefoxOptions()
                if self.headless:
                    options.add_argument('--headless')
                
                # 设置Firefox语言偏好
                if self.language:
                    options.set_preference('intl.accept_languages', self.language)
                
                self.driver = webdriver.Firefox(options=options)
                
            else:
                raise ValueError(f"不支持的浏览器类型: {self.browser}")
            
            if device_size:
                self.driver.set_window_size(device_size[0], device_size[1])
                
            logger.info(f"浏览器驱动设置成功: {self.browser}, 语言: {self.language}")
            
        except Exception as e:
            logger.error(f"浏览器驱动设置失败: {e}")
            raise
    
    def _set_language(self):
        """设置浏览器localStorage中的语言并刷新页面"""
        try:
            if self.language:
                current_url = self.driver.current_url
                
                # 设置localStorage中的语言相关项
                language_settings = [
                    ('language', self.language),
                    ('locale', self.language),
                    ('lang', self.language),
                    ('i18nextLng', self.language.split('-')[0]),  # for i18next
                    ('preferred_language', self.language),
                    ('ui_language', self.language)
                ]
                
                for key, value in language_settings:
                    self.driver.execute_script(f"localStorage.setItem('{key}', '{value}');")
                
                # 刷新页面使语言设置生效
                self.driver.refresh()
                
                # 等待页面重新加载
                WebDriverWait(self.driver, 10).until(
                    lambda driver: driver.execute_script("return document.readyState") == "complete"
                )
                
                logger.info(f"设置浏览器语言为: {self.language} 并刷新页面")
        except Exception as e:
            logger.warning(f"设置语言失败: {e}")
    
    def capture_url(self, url: str, output_path: str, 
                   device: str = 'desktop', wait_time: int = 3,
                   full_page: bool = True) -> str:
        """
        截取网页
        
        Args:
            url: 网页URL
            output_path: 输出文件路径
            device: 设备类型
            wait_time: 页面加载等待时间（秒）
            full_page: 是否截取完整页面
            
        Returns:
            保存的文件路径
        """
        try:
            device_size = self.DEVICE_SIZES.get(device, self.DEVICE_SIZES['desktop'])
            self._setup_driver(device_size)
            
            # 访问页面
            logger.info(f"正在访问页面: {url}")
            self.driver.get(url)
            
            # 设置语言
            self._set_language()
            
            # 等待页面加载
            time.sleep(wait_time)
            
            # 等待页面完全加载
            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            if full_page:
                # 获取页面完整高度
                total_height = self.driver.execute_script("return document.body.scrollHeight")
                viewport_height = self.driver.execute_script("return window.innerHeight")
                
                # 如果页面高度超过视口，进行滚动截图
                if total_height > viewport_height:
                    self._capture_full_page(output_path, total_height, viewport_height)
                else:
                    self.driver.save_screenshot(output_path)
            else:
                # 只截取当前视口
                self.driver.save_screenshot(output_path)
            
            logger.info(f"截图保存成功: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"截图失败: {e}")
            raise
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None
    
    def _capture_full_page(self, output_path: str, total_height: int, viewport_height: int):
        """捕获完整页面截图"""
        try:
            # 滚动到顶部
            self.driver.execute_script("window.scrollTo(0, 0)")
            time.sleep(1)
            
            screenshots = []
            current_position = 0
            
            while current_position < total_height:
                # 截取当前视口
                screenshot = self.driver.get_screenshot_as_png()
                screenshots.append(Image.open(io.BytesIO(screenshot)))
                
                # 滚动到下一个视口
                current_position += viewport_height
                self.driver.execute_script(f"window.scrollTo(0, {current_position})")
                time.sleep(0.5)
            
            # 拼接所有截图
            if len(screenshots) > 1:
                total_width = screenshots[0].width
                combined_image = Image.new('RGB', (total_width, total_height))
                
                y_offset = 0
                for img in screenshots:
                    combined_image.paste(img, (0, y_offset))
                    y_offset += img.height
                
                combined_image.save(output_path)
            else:
                screenshots[0].save(output_path)
                
        except Exception as e:
            logger.error(f"完整页面截图失败: {e}")
            raise
    
    def capture_element(self, url: str, selector: str, output_path: str,
                       device: str = 'desktop', wait_time: int = 3) -> str:
        """
        截取页面特定元素
        
        Args:
            url: 网页URL
            selector: CSS选择器
            output_path: 输出文件路径
            device: 设备类型
            wait_time: 等待时间
            
        Returns:
            保存的文件路径
        """
        try:
            device_size = self.DEVICE_SIZES.get(device, self.DEVICE_SIZES['desktop'])
            self._setup_driver(device_size)
            
            # 访问页面
            self.driver.get(url)
            
            # 设置语言
            self._set_language()
            
            time.sleep(wait_time)
            
            # 等待元素出现
            element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            
            # 滚动到元素位置
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(1)
            
            # 截取元素
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            element.screenshot(output_path)
            
            logger.info(f"元素截图保存成功: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"元素截图失败: {e}")
            raise
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None
    
    def capture_multiple_devices(self, url: str, output_dir: str,
                                devices: List[str] = None, wait_time: int = 3) -> Dict[str, str]:
        """
        在多个设备尺寸下截图
        
        Args:
            url: 网页URL
            output_dir: 输出目录
            devices: 设备列表
            wait_time: 等待时间
            
        Returns:
            设备名到文件路径的映射
        """
        if devices is None:
            devices = ['desktop', 'tablet', 'mobile']
        
        results = {}
        
        for device in devices:
            try:
                filename = f"{device}_screenshot.png"
                output_path = os.path.join(output_dir, filename)
                
                captured_path = self.capture_url(
                    url=url,
                    output_path=output_path,
                    device=device,
                    wait_time=wait_time
                )
                
                results[device] = captured_path
                logger.info(f"{device}设备截图完成")
                
            except Exception as e:
                logger.error(f"{device}设备截图失败: {e}")
                results[device] = None
        
        return results
    
    def get_page_info(self, url: str) -> Dict[str, any]:
        """
        获取页面基本信息
        
        Args:
            url: 网页URL
            
        Returns:
            页面信息字典
        """
        try:
            self._setup_driver()
            self.driver.get(url)
            
            # 设置语言
            self._set_language()
            
            time.sleep(2)
            
            page_info = {
                'title': self.driver.title,
                'url': self.driver.current_url,
                'viewport_size': self.driver.get_window_size(),
                'page_height': self.driver.execute_script("return document.body.scrollHeight"),
                'page_width': self.driver.execute_script("return document.body.scrollWidth"),
                'load_time': self.driver.execute_script("return performance.timing.loadEventEnd - performance.timing.navigationStart")
            }
            
            logger.info(f"页面信息获取成功: {page_info['title']}")
            return page_info
            
        except Exception as e:
            logger.error(f"获取页面信息失败: {e}")
            raise
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None 
    
    @staticmethod
    def build_class_selector(classes: str) -> str:
        """
        构建CSS类选择器，支持Tailwind CSS类组合
        
        Args:
            classes: 空格分隔的类名字符串，如 "flex flex-row gap-[16px]"
            
        Returns:
            CSS选择器字符串
        """
        if not classes:
            return ""
        
        # 分割类名
        class_list = classes.strip().split()
        
        # 为每个类名添加点号，并转义特殊字符
        escaped_classes = []
        for cls in class_list:
            # 转义CSS特殊字符（修复正则表达式警告）
            escaped_cls = re.sub(r'([\[\](){}*+?.^$|\\])', r'\\\1', cls)
            escaped_classes.append(f".{escaped_cls}")
        
        # 组合成选择器（连续的类选择器表示AND关系）
        selector = "".join(escaped_classes)
        
        logger.info(f"构建的CSS选择器: {selector}")
        return selector
    
    def find_elements_by_classes(self, url: str, classes: str, 
                                device: str = 'desktop', wait_time: int = 3) -> List[Dict]:
        """
        查找包含指定类组合的所有元素
        
        Args:
            url: 网页URL
            classes: 空格分隔的类名字符串
            device: 设备类型
            wait_time: 等待时间
            
        Returns:
            元素信息列表
        """
        try:
            device_size = self.DEVICE_SIZES.get(device, self.DEVICE_SIZES['desktop'])
            self._setup_driver(device_size)
            
            # 访问页面
            self.driver.get(url)
            
            # 设置语言
            self._set_language()
            
            time.sleep(wait_time)
            
            # 构建选择器
            selector = self.build_class_selector(classes)
            
            # 查找所有匹配的元素
            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            
            elements_info = []
            for i, element in enumerate(elements):
                try:
                    # 获取元素信息
                    location = element.location
                    size = element.size
                    tag_name = element.tag_name
                    text = element.text[:100] if element.text else ""  # 限制文本长度
                    
                    # 获取计算样式
                    try:
                        display_style = self.driver.execute_script(
                            "return window.getComputedStyle(arguments[0]).display;", element
                        )
                        position_style = self.driver.execute_script(
                            "return window.getComputedStyle(arguments[0]).position;", element
                        )
                    except Exception:
                        display_style = ''
                        position_style = ''
                    
                    element_info = {
                        'index': i,
                        'tag_name': tag_name,
                        'location': location,
                        'size': size,
                        'text': text,
                        'classes': element.get_attribute('class'),
                        'id': element.get_attribute('id'),
                        'visible': element.is_displayed(),
                        'display': display_style,
                        'position': position_style,
                    }
                    
                    elements_info.append(element_info)
                    
                except Exception as e:
                    logger.warning(f"获取元素{i}信息失败: {e}")
                    continue
            
            logger.info(f"找到 {len(elements_info)} 个匹配的元素")
            return elements_info
            
        except Exception as e:
            logger.error(f"查找元素失败: {e}")
            raise
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None
    
    def capture_by_classes(self, url: str, classes: str, output_dir: str,
                          element_index: int = 0, device: str = 'desktop', 
                          wait_time: int = 3) -> str:
        """
        通过类组合截取指定元素
        
        Args:
            url: 网页URL
            classes: 空格分隔的类名字符串
            output_dir: 输出目录
            element_index: 元素索引（当有多个匹配元素时）
            device: 设备类型
            wait_time: 等待时间
            
        Returns:
            保存的文件路径
        """
        try:
            device_size = self.DEVICE_SIZES.get(device, self.DEVICE_SIZES['desktop'])
            self._setup_driver(device_size)
            
            # 访问页面
            self.driver.get(url)
            
            # 设置语言
            self._set_language()
            
            time.sleep(wait_time)
            
            # 构建选择器
            selector = self.build_class_selector(classes)
            
            # 查找元素
            elements = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
            )
            
            if not elements:
                raise Exception(f"未找到匹配类 '{classes}' 的元素")
            
            if element_index >= len(elements):
                raise Exception(f"元素索引 {element_index} 超出范围，共找到 {len(elements)} 个元素")
            
            element = elements[element_index]
            
            # 滚动到元素位置
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(1)
            
            # 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)
            
            # 生成文件名
            safe_classes = re.sub(r'[^\w\-]', '_', classes.replace(' ', '-'))
            filename = f"element_{safe_classes}_{element_index}_{device}.png"
            output_path = os.path.join(output_dir, filename)
            
            # 截取元素
            element.screenshot(output_path)
            
            # 获取元素信息
            element_info = {
                'classes': classes,
                'selector': selector,
                'element_index': element_index,
                'total_found': len(elements),
                'tag_name': element.tag_name,
                'location': element.location,
                'size': element.size,
                'text': element.text[:100] if element.text else "",
                'device': device,
                'file_path': output_path
            }
            
            logger.info(f"类组合元素截图保存成功: {output_path}")
            logger.info(f"元素信息: {element_info}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"类组合元素截图失败: {e}")
            raise
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None 

    def capture_full_page(self, url: str, output_path: str, 
                         device: str = 'desktop', wait_time: int = 3) -> str:
        """
        截取完整页面
        Capture full page screenshot
        
        Args:
            url: 网页URL website URL
            output_path: 输出文件路径 output file path
            device: 设备类型 device type
            wait_time: 等待时间 wait time
            
        Returns:
            保存的文件路径 saved file path
        """
        return self.capture_url(url, output_path, device, wait_time, full_page=True)
    
    def build_filename_from_classes(self, classes: str, element_index: int, 
                                   device: str, url: str) -> str:
        """
        根据CSS类构建文件名
        Build filename from CSS classes
        
        Args:
            classes: CSS类名字符串 CSS classes string
            element_index: 元素索引 element index
            device: 设备类型 device type
            url: 网页URL website URL
            
        Returns:
            文件名 filename
        """
        try:
            # 清理类名，移除特殊字符
            safe_classes = re.sub(r'[^\w\-]', '_', classes.replace(' ', '-'))
            
            # 从URL提取域名
            domain = url.split('//')[1].split('/')[0] if '//' in url else 'unknown'
            safe_domain = re.sub(r'[^\w\-]', '_', domain)
            
            # 构建文件名
            filename = f"element_{safe_classes}_{element_index}_{device}.png"
            
            return filename
            
        except Exception as e:
            logger.warning(f"构建文件名失败: {e}")
            # 返回默认文件名
            return f"element_{element_index}_{device}.png" 