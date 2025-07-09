"""
网页截图捕获模块
Website Screenshot Capture Module
"""
import os
import time
import signal
import psutil
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
        self.chrome_process_id = None  # 跟踪Chrome进程ID
        
    def _get_optimized_chrome_options(self) -> ChromeOptions:
        """获取优化的Chrome选项以减少内存和CPU使用"""
        options = ChromeOptions()
        
        if self.headless:
            options.add_argument('--headless=new')  # 使用新的headless模式
        
        # 基础优化选项
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        options.add_argument('--disable-images')  # 禁用图片加载以节省内存
        
        # 内存优化选项
        options.add_argument('--memory-pressure-off')
        options.add_argument('--max_old_space_size=2048')  # 限制V8内存使用
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-renderer-backgrounding')
        
        # 性能优化选项
        options.add_argument('--disable-features=VizDisplayCompositor')
        options.add_argument('--disable-logging')
        options.add_argument('--silent')
        options.add_argument('--disable-default-apps')
        options.add_argument('--disable-sync')
        
        # 网络和安全优化
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-features=TranslateUI')
        options.add_argument('--disable-ipc-flooding-protection')
        
        # 设置浏览器语言偏好
        if self.language:
            options.add_argument(f'--lang={self.language}')
            options.add_experimental_option('prefs', {
                'intl.accept_languages': self.language,
                'profile.default_content_setting_values': {
                    'notifications': 2,  # 禁用通知
                    'geolocation': 2,    # 禁用地理位置
                }
            })
        
        return options
        
    def _setup_driver(self, device_size: Tuple[int, int] = None, device_type: str = 'desktop'):
        """设置浏览器驱动"""
        try:
            # 清理之前的进程
            self._cleanup_processes()
            
            if self.browser.lower() == 'chrome':
                options = self._get_optimized_chrome_options()
                
                # 为移动设备设置设备仿真
                if device_type == 'mobile':
                    mobile_emulation = {
                        "deviceMetrics": {
                            "width": 375,
                            "height": 667,
                            "pixelRatio": 2.0
                        },
                        "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1"
                    }
                    options.add_experimental_option("mobileEmulation", mobile_emulation)
                    logger.info("设置移动设备仿真: iPhone 6")
                elif device_size:
                    options.add_argument(f'--window-size={device_size[0]},{device_size[1]}')
                
                self.driver = webdriver.Chrome(options=options)
                
                # 记录Chrome进程ID用于后续清理
                if hasattr(self.driver, 'service') and hasattr(self.driver.service, 'process'):
                    self.chrome_process_id = self.driver.service.process.pid
                    logger.info(f"Chrome进程ID: {self.chrome_process_id}")
                
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
            
            # 为非移动设备设置窗口尺寸
            if device_type != 'mobile' and device_size:
                self.driver.set_window_size(device_size[0], device_size[1])
                
                # 设置页面加载超时
                self.driver.set_page_load_timeout(30)  # 30秒超时
                self.driver.implicitly_wait(10)  # 隐式等待10秒
                
            logger.info(f"浏览器驱动设置成功: {self.browser}, 设备类型: {device_type}, 语言: {self.language}")
            
        except Exception as e:
            logger.error(f"浏览器驱动设置失败: {e}")
            self._cleanup_processes()  # 确保清理
            raise
    
    def _cleanup_processes(self):
        """强制清理浏览器进程"""
        try:
            # 清理webdriver
            if self.driver:
                try:
                    self.driver.quit()
                except Exception as e:
                    logger.warning(f"关闭webdriver时出错: {e}")
                finally:
                    self.driver = None
            
            # 强制终止Chrome进程
            if self.chrome_process_id:
                try:
                    if psutil.pid_exists(self.chrome_process_id):
                        process = psutil.Process(self.chrome_process_id)
                        # 首先尝试优雅关闭
                        process.terminate()
                        process.wait(timeout=5)
                        
                        # 如果还存在，强制杀死
                        if process.is_running():
                            process.kill()
                        
                        logger.info(f"已清理Chrome进程: {self.chrome_process_id}")
                except (psutil.NoSuchProcess, psutil.TimeoutExpired) as e:
                    logger.info(f"Chrome进程已结束或清理超时: {e}")
                except Exception as e:
                    logger.warning(f"清理Chrome进程时出错: {e}")
                finally:
                    self.chrome_process_id = None
            
            # 清理所有遗留的Chrome进程（额外保险措施）
            self._kill_orphaned_chrome_processes()
            
        except Exception as e:
            logger.error(f"清理进程时出错: {e}")
    
    def _kill_orphaned_chrome_processes(self):
        """清理孤立的Chrome进程"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] and 'chrome' in proc.info['name'].lower():
                        # 检查是否是headless Chrome进程
                        cmdline = proc.info.get('cmdline', [])
                        if cmdline and any('--headless' in arg for arg in cmdline):
                            logger.info(f"发现孤立Chrome进程: {proc.info['pid']}")
                            proc.terminate()
                            proc.wait(timeout=3)
                            if proc.is_running():
                                proc.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            logger.warning(f"清理孤立Chrome进程时出错: {e}")

    def _wait_for_page_fully_loaded(self, max_wait_time: int = 30):
        """等待页面完全加载，包括CSS和JavaScript，增加超时控制"""
        try:
            start_time = time.time()
            
            # 基础页面加载检查（带超时）
            WebDriverWait(self.driver, min(max_wait_time, 15)).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # 检查剩余时间
            elapsed = time.time() - start_time
            remaining_time = max_wait_time - elapsed
            
            if remaining_time <= 0:
                logger.warning("页面加载检查超时，继续执行")
                return
            
            # 等待图片加载（带超时）
            try:
                self.driver.execute_async_script("""
                    var callback = arguments[arguments.length - 1];
                    var timeout = arguments[0] * 1000;
                    var startTime = Date.now();
                    
                    function checkImages() {
                        if (Date.now() - startTime > timeout) {
                            callback('timeout');
                            return;
                        }
                        
                        const images = document.querySelectorAll('img');
                        let loadedCount = 0;
                        const totalImages = images.length;
                        
                        if (totalImages === 0) {
                            callback('success');
                            return;
                        }
                        
                        images.forEach(img => {
                            if (img.complete) {
                                loadedCount++;
                            }
                        });
                        
                        if (loadedCount === totalImages) {
                            callback('success');
                        } else {
                            setTimeout(checkImages, 500);
                        }
                    }
                    
                    checkImages();
                """, min(remaining_time, 10))
            except Exception as e:
                logger.warning(f"等待图片加载失败: {e}")
            
            # 最后等待一小段时间确保渲染完成
            time.sleep(min(2, remaining_time))
            
            logger.debug("页面完全加载完成")
            
        except Exception as e:
            logger.warning(f"等待页面完全加载失败: {e}")
            # 如果检测失败，等待一个较短的固定时间
            time.sleep(3)

    def _set_language(self):
        """设置浏览器语言偏好"""
        try:
            if self.language == 'zh-CN':
                # 设置中文语言
                self.driver.execute_script("""
                    Object.defineProperty(navigator, 'language', {
                        get: function() { return 'zh-CN'; }
                    });
                    Object.defineProperty(navigator, 'languages', {
                        get: function() { return ['zh-CN', 'zh', 'en']; }
                    });
                """)
                
                # 设置Accept-Language头
                self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                    "userAgent": self.driver.execute_script("return navigator.userAgent"),
                    "acceptLanguage": "zh-CN,zh;q=0.9,en;q=0.8"
                })
            elif self.language == 'en-US':
                # 设置英文语言
                self.driver.execute_script("""
                    Object.defineProperty(navigator, 'language', {
                        get: function() { return 'en-US'; }
                    });
                    Object.defineProperty(navigator, 'languages', {
                        get: function() { return ['en-US', 'en']; }
                    });
                """)
                
                # 设置Accept-Language头
                self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                    "userAgent": self.driver.execute_script("return navigator.userAgent"),
                    "acceptLanguage": "en-US,en;q=0.9"
                })
                
        except Exception as e:
            logger.warning(f"设置语言失败: {e}")

    def _parse_url_with_xpath(self, url_input: str) -> tuple[str, str]:
        """
        解析URL输入，检查是否包含XPath
        
        Args:
            url_input: 可能包含XPath的URL输入
            
        Returns:
            tuple: (基础URL, XPath选择器) 如果没有XPath则返回 (url_input, None)
        """
        if ':' in url_input:
            # 查找协议后的第一个冒号
            protocol_end = url_input.find('://')
            if protocol_end != -1:
                # 从协议后开始查找冒号
                search_start = protocol_end + 3
                xpath_separator = url_input.find(':', search_start)
                
                if xpath_separator != -1:
                    # 找到XPath分隔符
                    base_url = url_input[:xpath_separator]
                    xpath = url_input[xpath_separator + 1:]
                    return base_url, xpath
        
        return url_input, None

    def capture_url_with_auto_detection(self, url_input: str, output_path: str, 
                                       device: str = 'desktop', wait_time: int = 3,
                                       full_page: bool = True) -> str:
        """
        智能截图方法，自动检测URL中是否包含XPath
        
        Args:
            url_input: 可能包含XPath的URL输入
            output_path: 输出文件路径
            device: 设备类型
            wait_time: 等待时间
            full_page: 是否截取完整页面（仅当没有XPath时有效）
            
        Returns:
            保存的文件路径
        """
        base_url, xpath = self._parse_url_with_xpath(url_input)
        
        if xpath:
            # 如果检测到XPath，截取特定元素
            logger.info("检测到XPath，将截取特定元素")
            return self.capture_element_by_xpath(base_url, xpath, output_path, device, wait_time)
        else:
            # 如果没有XPath，正常截取页面
            logger.info("未检测到XPath，将截取整个页面")
            return self.capture_url(base_url, output_path, device, wait_time, full_page)
    
    def capture_url(self, url: str, output_path: str, 
                   device: str = 'desktop', wait_time: int = 3,
                   full_page: bool = True) -> str:
        """
        截取网页（支持URL:XPath格式自动检测）
        
        Args:
            url: 网页URL，支持格式：
                - 普通URL: https://example.com
                - URL+XPath: https://example.com:/html/body/div[1]/span
            output_path: 输出文件路径
            device: 设备类型
            wait_time: 页面加载等待时间（秒）
            full_page: 是否截取完整页面（仅当没有XPath时有效）
            
        Returns:
            保存的文件路径
        """
        # 先检查是否包含XPath
        base_url, xpath = self._parse_url_with_xpath(url)
        
        if xpath:
            # 如果检测到XPath，使用元素截图方法
            logger.info("检测到XPath格式，将截取特定元素")
            return self.capture_element_by_xpath(base_url, xpath, output_path, device, wait_time)
        
        # 没有XPath，执行正常的页面截图
        try:
            device_size = self.DEVICE_SIZES.get(device, self.DEVICE_SIZES['desktop'])
            self._setup_driver(device_size, device_type=device)
            
            # 访问页面
            logger.info(f"正在访问页面: {base_url}")
            self.driver.get(base_url)
            
            # 设置语言
            self._set_language()
            
            # 等待页面加载
            time.sleep(min(wait_time, 5))  # 限制最大等待时间
            
            # 等待页面完全加载（带超时控制）
            self._wait_for_page_fully_loaded(max_wait_time=20)
            
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
            # 确保清理资源
            self._cleanup_processes()
    
    def _capture_full_page(self, output_path: str, total_height: int, viewport_height: int):
        """捕获完整页面截图，优化内存使用"""
        try:
            # 滚动到顶部
            self.driver.execute_script("window.scrollTo(0, 0)")
            time.sleep(1)
            
            screenshots = []
            current_position = 0
            max_screenshots = 10  # 限制最大截图数量以防止内存溢出
            
            screenshot_count = 0
            while current_position < total_height and screenshot_count < max_screenshots:
                # 截取当前视口
                screenshot = self.driver.get_screenshot_as_png()
                screenshots.append(Image.open(io.BytesIO(screenshot)))
                
                # 滚动到下一个视口
                current_position += viewport_height
                self.driver.execute_script(f"window.scrollTo(0, {current_position})")
                time.sleep(0.5)
                screenshot_count += 1
            
            # 拼接所有截图
            if len(screenshots) > 1:
                total_width = screenshots[0].width
                combined_height = sum(img.height for img in screenshots)
                combined_image = Image.new('RGB', (total_width, combined_height))
                
                y_offset = 0
                for img in screenshots:
                    combined_image.paste(img, (0, y_offset))
                    y_offset += img.height
                    # 及时释放内存
                    img.close()
                
                combined_image.save(output_path)
                combined_image.close()
            else:
                screenshots[0].save(output_path)
                screenshots[0].close()
                
        except Exception as e:
            logger.error(f"完整页面截图失败: {e}")
            raise
        finally:
            # 清理screenshots列表中的所有图像
            for img in screenshots:
                try:
                    img.close()
                except:
                    pass
    
    def capture_element(self, url: str, selector: str, output_path: str,
                       device: str = 'desktop', wait_time: int = 3) -> str:
        """
        截取页面特定元素（支持URL:XPath格式自动检测）
        
        Args:
            url: 网页URL，支持格式：
                - 普通URL: https://example.com
                - URL+XPath: https://example.com:/html/body/div[1]/span (此时忽略selector参数)
            selector: CSS选择器
            output_path: 输出文件路径
            device: 设备类型
            wait_time: 等待时间
            
        Returns:
            保存的文件路径
        """
        # 先检查是否包含XPath
        base_url, xpath = self._parse_url_with_xpath(url)
        
        if xpath:
            # 如果检测到XPath，忽略selector参数，使用XPath方法
            logger.info("检测到XPath格式，将使用XPath而不是CSS选择器")
            return self.capture_element_by_xpath(base_url, xpath, output_path, device, wait_time)
        
        # 没有XPath，执行正常的CSS选择器截图
        try:
            device_size = self.DEVICE_SIZES.get(device, self.DEVICE_SIZES['desktop'])
            self._setup_driver(device_size, device_type=device)
            
            # 访问页面
            self.driver.get(base_url)
            
            # 设置语言
            self._set_language()
            
            time.sleep(min(wait_time, 5))  # 限制最大等待时间
            
            # 等待页面完全加载（带超时控制）
            self._wait_for_page_fully_loaded(max_wait_time=15)
            
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
            # 确保清理资源
            self._cleanup_processes()

    def capture_element_by_xpath(self, url: str, xpath: str, output_path: str,
                                device: str = 'desktop', wait_time: int = 3) -> str:
        """
        通过XPath截取页面特定元素
        
        Args:
            url: 网页URL
            xpath: XPath选择器
            output_path: 输出文件路径
            device: 设备类型
            wait_time: 等待时间
            
        Returns:
            保存的文件路径
        """
        try:
            device_size = self.DEVICE_SIZES.get(device, self.DEVICE_SIZES['desktop'])
            self._setup_driver(device_size, device_type=device)
            
            # 访问页面
            logger.info(f"正在访问页面: {url}")
            self.driver.get(url)
            
            # 设置语言
            self._set_language()
            
            # 为移动端设置localStorage
            if device == 'mobile':
                logger.info("设置移动端localStorage...")
                # 设置 h5_kalodata_first_open
                self.driver.execute_script("localStorage.setItem('h5_kalodata_first_open', 'true');")
                # 设置 h5_kalodata_last_visit 为当前时间戳
                self.driver.execute_script("localStorage.setItem('h5_kalodata_last_visit', Date.now().toString());")
                # 设置 h5_language 为 en-US
                self.driver.execute_script("localStorage.setItem('h5_language', 'en-US');")
                # 设置弹窗控制相关项目
                self.driver.execute_script("localStorage.setItem('h5_kalodata_modal_state', 'hidden');")
                self.driver.execute_script("localStorage.setItem('h5_app_guide_shown', 'true');")
                self.driver.execute_script("localStorage.setItem('h5_download_guide_dismissed', 'true');")
                logger.info("移动端localStorage设置完成")
                
                # 等待1秒后刷新页面
                logger.info("等待1秒后刷新页面以应用localStorage设置...")
                time.sleep(1)
                self.driver.refresh()
                self._set_language()
            
            time.sleep(wait_time)
            
            # 等待页面完全加载
            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # 等待CSS和JavaScript完全加载
            self._wait_for_page_fully_loaded()
            
            logger.info(f"正在查找XPath元素: {xpath}")
            
            # 等待元素出现
            element = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            
            # 滚动到元素位置
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
            time.sleep(2)  # 等待滚动完成
            
            # 额外等待确保元素样式完全应用
            time.sleep(2)
            
            # 注意：移除了调试高亮代码，避免影响截图真实性
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 截取元素
            element.screenshot(output_path)
            
            logger.info(f"XPath元素截图保存成功: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"XPath元素截图失败: {e}")
            logger.error(f"XPath: {xpath}")
            logger.error(f"URL: {url}")
            raise
        finally:
            # 确保清理资源
            self._cleanup_processes()

    def capture_by_xpath(self, url: str, xpath: str = None, output_dir: str = '',
                        device: str = 'desktop', wait_time: int = 3) -> str:
        """
        通过XPath截取元素的便捷方法（支持URL:XPath格式）
        
        Args:
            url: 网页URL，支持格式：
                - 普通URL: https://example.com (需要提供xpath参数)
                - URL+XPath: https://example.com:/html/body/div[1]/span (xpath参数可选)
            xpath: XPath选择器（当URL中不包含XPath时必需）
            output_dir: 输出目录
            device: 设备类型
            wait_time: 等待时间
            
        Returns:
            保存的文件路径
        """
        # 解析URL，检查是否包含XPath
        base_url, url_xpath = self._parse_url_with_xpath(url)
        
        # 确定要使用的XPath
        final_xpath = url_xpath if url_xpath else xpath
        
        if not final_xpath:
            raise ValueError("必须提供XPath选择器，可以通过xpath参数或URL中的:xpath格式提供")
        
        # 构建文件名
        filename = self.build_filename_from_xpath(final_xpath, device, base_url)
        output_path = os.path.join(output_dir, filename)
        
        return self.capture_element_by_xpath(base_url, final_xpath, output_path, device, wait_time)
    
    def build_filename_from_xpath(self, xpath: str, device: str, url: str) -> str:
        """
        从XPath构建文件名
        
        Args:
            xpath: XPath选择器
            device: 设备类型
            url: 网页URL
            
        Returns:
            文件名
        """
        # 从URL提取域名
        from urllib.parse import urlparse
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.replace('www.', '').replace('.', '_')
        
        # 简化XPath，提取关键部分
        xpath_simple = xpath.replace('/', '_').replace('[', '_').replace(']', '_').replace('(', '_').replace(')', '_')
        # 限制长度
        if len(xpath_simple) > 50:
            xpath_simple = xpath_simple[:50]
        
        # 构建文件名
        filename = f"xpath_{domain}_{xpath_simple}_{device}.png"
        
        # 清理文件名中的特殊字符
        import re
        filename = re.sub(r'[^\w\-_\.]', '_', filename)
        filename = re.sub(r'_+', '_', filename)  # 合并多个下划线
        
        return filename
    
    def capture_multiple_devices(self, url: str, output_dir: str,
                                devices: List[str] = None, wait_time: int = 3) -> Dict[str, str]:
        """
        在多个设备尺寸下截图（支持URL:XPath格式）
        
        Args:
            url: 网页URL，支持格式：
                - 普通URL: https://example.com
                - URL+XPath: https://example.com:/html/body/div[1]/span
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
            self._setup_driver(device_type='desktop')
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
            self._setup_driver(device_size, device_type=device)
            
            # 访问页面
            self.driver.get(url)
            
            # 设置语言
            self._set_language()
            
            time.sleep(wait_time)
            
            # 等待页面完全加载
            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # 等待CSS和JavaScript完全加载
            self._wait_for_page_fully_loaded()
            
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
            self._setup_driver(device_size, device_type=device)
            
            # 访问页面
            self.driver.get(url)
            
            # 设置语言
            self._set_language()
            
            time.sleep(wait_time)
            
            # 等待页面完全加载
            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # 等待CSS和JavaScript完全加载
            self._wait_for_page_fully_loaded()
            
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