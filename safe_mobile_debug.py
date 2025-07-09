#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
安全的移动端调试工具
Safe mobile debugging tool
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.screenshot.capture import ScreenshotCapture
from selenium.webdriver.support.ui import WebDriverWait
import time

def safe_xpath_check():
    """安全地检查移动端XPath是否存在"""
    print("🔍 安全移动端XPath检查")
    print("=" * 60)
    
    url = "https://www.kalodata.com/settings"
    target_xpath = "/html/body/div/div/div/div[2]/div/div/div[2]/div[2]"
    
    print(f"URL: {url}")
    print(f"目标XPath: {target_xpath}")
    print("-" * 60)
    
    try:
        # 创建移动端截图器
        capturer = ScreenshotCapture(browser='chrome', headless=True, language='en-US')
        device_size = capturer.DEVICE_SIZES.get('mobile', capturer.DEVICE_SIZES['desktop'])
        capturer._setup_driver(device_size, device_type='mobile')
        
        print("✅ 移动端浏览器设置成功")
        
        # 访问页面
        print("🌐 访问页面...")
        capturer.driver.get(url)
        capturer._set_language()
        
        # 设置localStorage
        print("📝 设置localStorage...")
        capturer.driver.execute_script("localStorage.setItem('h5_kalodata_first_open', 'true');")
        print("✅ localStorage设置完成")
        
        # 刷新页面
        print("🔄 刷新页面...")
        capturer.driver.refresh()
        capturer._set_language()
        
        # 等待页面加载
        WebDriverWait(capturer.driver, 15).until(
            lambda driver: driver.execute_script("return document.readyState") == "complete"
        )
        capturer._wait_for_page_fully_loaded()
        print("✅ 页面加载完成")
        
        # 使用JavaScript安全地检查XPath
        print("🔍 使用JavaScript检查XPath...")
        
        js_check_script = f"""
        function getElementByXPath(xpath) {{
            return document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
        }}
        
        var element = getElementByXPath('{target_xpath}');
        if (element) {{
            return {{
                exists: true,
                tagName: element.tagName,
                className: element.className,
                id: element.id,
                text: element.textContent.substring(0, 100),
                visible: element.offsetParent !== null,
                rect: {{
                    x: element.getBoundingClientRect().x,
                    y: element.getBoundingClientRect().y,
                    width: element.getBoundingClientRect().width,
                    height: element.getBoundingClientRect().height
                }}
            }};
        }} else {{
            return {{
                exists: false,
                message: '元素不存在'
            }};
        }}
        """
        
        result = capturer.driver.execute_script(js_check_script)
        
        if result['exists']:
            print("✅ XPath元素存在！")
            print(f"   标签: {result['tagName']}")
            print(f"   类名: {result['className']}")
            print(f"   ID: {result['id']}")
            print(f"   文本: {result['text'][:50]}...")
            print(f"   可见: {result['visible']}")
            print(f"   位置: ({result['rect']['x']}, {result['rect']['y']})")
            print(f"   尺寸: {result['rect']['width']} x {result['rect']['height']}")
            
            # 尝试使用JavaScript滚动到元素并截图
            print("\n📸 尝试JavaScript截图...")
            try:
                # 滚动到元素
                scroll_script = f"""
                var element = document.evaluate('{target_xpath}', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                if (element) {{
                    element.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                    return true;
                }}
                return false;
                """
                
                scrolled = capturer.driver.execute_script(scroll_script)
                if scrolled:
                    print("✅ 已滚动到元素位置")
                    time.sleep(3)  # 等待滚动完成
                    
                    # 截取整个页面
                    screenshot_path = "screenshots/mobile_with_localStorage.png"
                    capturer.driver.save_screenshot(screenshot_path)
                    print(f"✅ 页面截图保存: {screenshot_path}")
                    
                    # 尝试高亮元素然后截图
                    highlight_script = f"""
                    var element = document.evaluate('{target_xpath}', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                    if (element) {{
                        element.style.border = '3px solid red';
                        element.style.backgroundColor = 'yellow';
                        return true;
                    }}
                    return false;
                    """
                    
                    highlighted = capturer.driver.execute_script(highlight_script)
                    if highlighted:
                        print("✅ 元素已高亮")
                        time.sleep(1)
                        
                        highlighted_path = "screenshots/mobile_highlighted_element.png"
                        capturer.driver.save_screenshot(highlighted_path)
                        print(f"✅ 高亮截图保存: {highlighted_path}")
            except Exception as screenshot_e:
                print(f"❌ 截图过程出错: {str(screenshot_e)}")
                        
        else:
            print("❌ XPath元素不存在")
            print(f"   原因: {result['message']}")
            
            # 分析页面结构
            print("\n🔍 分析页面结构...")
            structure_script = """
            function analyzeStructure() {
                var body = document.body;
                var result = {
                    bodyChildren: body.children.length,
                    firstLevelDivs: [],
                    pathAnalysis: []
                };
                
                // 分析第一层div
                for (var i = 0; i < body.children.length; i++) {
                    var child = body.children[i];
                    if (child.tagName === 'DIV') {
                        result.firstLevelDivs.push({
                            index: i,
                            className: child.className,
                            id: child.id,
                            childrenCount: child.children.length
                        });
                    }
                }
                
                // 逐步分析路径
                var paths = [
                    '/html/body/div',
                    '/html/body/div/div',
                    '/html/body/div/div/div',
                    '/html/body/div/div/div/div[2]'
                ];
                
                paths.forEach(function(path) {
                    var elements = document.evaluate(path, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                    result.pathAnalysis.push({
                        path: path,
                        count: elements.snapshotLength
                    });
                });
                
                return result;
            }
            
            return analyzeStructure();
            """
            
            structure = capturer.driver.execute_script(structure_script)
            print(f"   Body子元素数量: {structure['bodyChildren']}")
            print(f"   第一层div数量: {len(structure['firstLevelDivs'])}")
            
            for div_info in structure['firstLevelDivs']:
                print(f"     - Div {div_info['index']}: class='{div_info['className']}', children={div_info['childrenCount']}")
            
            print("\n   路径分析:")
            for path_info in structure['pathAnalysis']:
                print(f"     - {path_info['path']}: {path_info['count']} 个元素")
        
        # 保存页面HTML用于分析
        html_content = capturer.driver.page_source
        with open('screenshots/mobile_page_source.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"\n📄 页面HTML已保存: screenshots/mobile_page_source.html")
        
        capturer.driver.quit()
        
    except Exception as e:
        print(f"❌ 调试过程出错: {str(e)}")
        if 'capturer' in locals() and capturer.driver:
            capturer.driver.quit()

if __name__ == "__main__":
    safe_xpath_check() 