#!/usr/bin/env python3
"""
自动化测试助手主程序
Main program for Automated Testing Assistant
"""
import sys
import os
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import time

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.config import Config
from src.utils.logger import get_logger
from src.feishu.client import FeishuClient
from src.ai_analysis.gemini_case_generator import GeminiCaseGenerator
from src.screenshot.capture import ScreenshotCapture
from src.figma.client import FigmaClient
from src.visual_comparison.comparator import VisualComparator
from src.workflow.executor import WorkflowExecutor

def cleanup_old_reports(reports_dir: str):
    """
    清理旧的报告目录，只保留最新的一个
    Clean up old report directories, keep only the latest one
    """
    try:
        if not os.path.exists(reports_dir):
            return
            
        # 获取所有comparison_开头的目录
        comparison_dirs = []
        for item in os.listdir(reports_dir):
            item_path = os.path.join(reports_dir, item)
            if os.path.isdir(item_path) and item.startswith('comparison_'):
                try:
                    # 提取时间戳
                    timestamp_str = item.replace('comparison_', '')
                    timestamp = int(timestamp_str)
                    comparison_dirs.append((timestamp, item_path))
                except ValueError:
                    # 如果无法解析时间戳，跳过
                    console.print(f"⚠️  无法解析目录时间戳: {item}", style="yellow")
                    continue
        
        # 如果没有旧目录，直接返回
        if len(comparison_dirs) <= 1:
            return
        
        # 按时间戳排序，保留最新的，删除其他的
        comparison_dirs.sort(key=lambda x: x[0], reverse=True)  # 降序排列，最新的在前
        
        # 删除除最新的之外的所有目录
        dirs_to_delete = comparison_dirs[1:]  # 跳过第一个（最新的）
        
        import shutil
        for timestamp, dir_path in dirs_to_delete:
            try:
                console.print(f"🗑️  删除旧报告目录: {os.path.basename(dir_path)}", style="yellow")
                shutil.rmtree(dir_path)
            except Exception as e:
                console.print(f"⚠️  删除目录失败 {dir_path}: {e}", style="yellow")
        
        if dirs_to_delete:
            console.print(f"✅ 已清理 {len(dirs_to_delete)} 个旧报告目录，保留最新的报告", style="green")
        
    except Exception as e:
        console.print(f"⚠️  清理旧报告时出错: {e}", style="yellow")
        # 清理失败不应该影响主流程

console = Console()
logger = get_logger(__name__)

@click.group()
def cli():
    """自动化测试助手 - 通过对比飞书PRD和网站功能进行测试"""
    pass

@cli.command()
def check_config():
    """检查配置 Check configuration"""
    console.print(Panel.fit("🔧 配置检查 / Configuration Check", style="blue"))
    
    if Config.validate_config():
        console.print("✅ 配置验证通过 / Configuration validation passed", style="green")
        
        # 显示配置信息
        table = Table(title="配置信息 / Configuration Info")
        table.add_column("配置项 / Config Item", style="cyan")
        table.add_column("状态 / Status", style="green")
        
        configs = [
            ("飞书App ID / Feishu App ID", "✅" if Config.FEISHU_APP_ID else "❌"),
            ("飞书App Secret / Feishu App Secret", "✅" if Config.FEISHU_APP_SECRET else "❌"),
            ("Gemini API Key", "✅" if Config.GEMINI_API_KEY else "❌"),
            ("Figma Access Token", "✅" if Config.FIGMA_ACCESS_TOKEN else "❌"),
        ]
        
        for item, status in configs:
            table.add_row(item, status)
        
        console.print(table)
    else:
        console.print("❌ 配置验证失败 / Configuration validation failed", style="red")
        console.print("请检查 .env 文件中的配置项", style="yellow")

@cli.command()
@click.option('--document-token', '-d', help='飞书文档token / Feishu document token')
def test_feishu(document_token):
    """测试飞书PRD解析 / Test Feishu PRD parsing"""
    console.print(Panel.fit("📄 飞书PRD解析测试 / Feishu PRD Parsing Test", style="blue"))
    
    try:
        client = FeishuClient()
        console.print("✅ 飞书客户端创建成功 / Feishu client created successfully", style="green")
        
        if document_token:
            console.print(f"📋 开始解析文档: {document_token}")
            result = client.parse_prd_document(document_token)
            
            # 显示解析结果
            table = Table(title="文档解析结果 / Document Parsing Result")
            table.add_column("项目 / Item", style="cyan")
            table.add_column("值 / Value", style="green")
            
            table.add_row("文档标题 / Title", result['title'])
            table.add_row("文本长度 / Text Length", str(len(result['text_content'])))
            table.add_row("块数量 / Blocks Count", str(result['blocks_count']))
            table.add_row("标题数量 / Headings Count", str(len(result['structure']['headings'])))
            table.add_row("表格数量 / Tables Count", str(len(result['structure']['tables'])))
            table.add_row("列表数量 / Lists Count", str(len(result['structure']['lists'])))
            
            console.print(table)
            
            # 显示完整的markdown格式文档内容
            if result['text_content']:
                console.print(Panel(result['text_content'], title="📄 文档内容 (Markdown格式) / Document Content (Markdown Format)", style="yellow"))
            else:
                console.print(Panel("未能提取到文档内容", title="⚠️  文档内容 / Document Content", style="red"))
            
        else:
            console.print("⚠️  未提供文档token，仅测试客户端连接", style="yellow")
            access_token = client.get_access_token()
            console.print(f"✅ 访问令牌获取成功: {access_token[:20]}...", style="green")
            
    except Exception as e:
        console.print(f"❌ 测试失败: {e}", style="red")
        logger.error(f"飞书测试失败: {e}")

@cli.command()
def setup():
    """项目设置 / Project setup"""
    console.print(Panel.fit("🚀 项目设置 / Project Setup", style="blue"))
    
    # 创建必要的目录
    directories = ['logs', 'reports', 'screenshots', 'config']
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            console.print(f"📁 创建目录: {directory}", style="green")
        else:
            console.print(f"📁 目录已存在: {directory}", style="yellow")
    
    # 检查环境变量文件
    if not os.path.exists('.env'):
        if os.path.exists('env.example'):
            import shutil
            shutil.copy('env.example', '.env')
            console.print("📝 已创建 .env 文件，请编辑配置", style="green")
        else:
            console.print("⚠️  未找到 env.example 文件", style="yellow")
    else:
        console.print("📝 .env 文件已存在", style="yellow")
    
    console.print("\n📋 下一步 / Next Steps:")
    console.print("1. 编辑 .env 文件，填入API密钥")
    console.print("2. 运行: python main.py check-config")
    console.print("3. 运行: python main.py test-feishu --document-token <your_token>")

@cli.command()
def status():
    """显示项目状态 / Show project status"""
    console.print(Panel.fit("📊 项目状态 / Project Status", style="blue"))
    
    # 检查模块状态
    modules = [
        ("飞书PRD解析 / Feishu PRD Parser", "src/feishu/client.py"),
        ("配置管理 / Config Management", "src/utils/config.py"),
        ("日志管理 / Logging", "src/utils/logger.py"),
    ]
    
    table = Table(title="模块状态 / Module Status")
    table.add_column("模块 / Module", style="cyan")
    table.add_column("状态 / Status", style="green")
    table.add_column("文件 / File", style="yellow")
    
    for module_name, file_path in modules:
        if os.path.exists(file_path):
            table.add_row(module_name, "✅ 已实现", file_path)
        else:
            table.add_row(module_name, "❌ 未实现", file_path)
    
    console.print(table)
    
    # 显示待实现模块
    console.print("\n🔄 待实现模块 / Pending Modules:")
    pending_modules = [
        "网站页面抓取 / Website Page Scraping",
        "Figma设计稿解析 / Figma Design Parsing", 
        "AI对比分析 / AI Comparison Analysis",
        "报告生成 / Report Generation"
    ]
    
    for module in pending_modules:
        console.print(f"⏳ {module}")

@cli.command()
@click.option('--document-token', '-d', help='飞书文档token / Feishu document token')
@click.option('--case-count', '-n', default=5, help='生成测试用例数量 / Number of test cases to generate')
@click.option('--output', '-o', help='输出文件路径 / Output file path (可选)')
def generate_cases(document_token, case_count, output):
    """通过Gemini自动生成测试用例 / Generate test cases with Gemini AI"""
    console.print(Panel.fit("🤖 Gemini测试用例生成 / Gemini Test Case Generation", style="blue"))
    if not document_token:
        console.print("❌ 请提供文档token (使用 --document-token)", style="red")
        return
    try:
        # 1. 解析PRD文档
        client = FeishuClient()
        prd_result = client.parse_prd_document(document_token)
        prd_text = prd_result.get('text_content', '')
        if not prd_text.strip():
            console.print("⚠️  文档内容为空，无法生成测试用例", style="yellow")
            return
        # 2. 调用Gemini生成测试用例
        generator = GeminiCaseGenerator()
        console.print(f"📄 正在分析文档并生成{case_count}条测试用例...", style="cyan")
        cases = generator.generate_test_cases(prd_text, case_count=case_count)
        
        # 3. 显示结果
        console.print(Panel(cases, title="Gemini生成的测试用例", style="green"))
        
        # 4. 如果指定了输出文件，保存纯净的测试用例内容
        if output:
            # 构建完整的测试用例文档
            document_title = prd_result.get('title', '未命名文档')
            test_doc_content = f"""# 测试用例文档

## 文档信息
- **原始文档**: {document_title or '今汐日历App PRD'}
- **文档ID**: `{document_token}`
- **生成时间**: {prd_result.get('parsed_at', '未知')}
- **用例数量**: {case_count}

---

{cases}

---

## 原始PRD内容
{prd_text}
"""
            with open(output, 'w', encoding='utf-8') as f:
                f.write(test_doc_content)
            console.print(f"✅ 测试用例已保存到: {output}", style="green")
        
    except Exception as e:
        console.print(f"❌ 生成测试用例失败: {e}", style="red")
        logger.error(f"Gemini生成测试用例失败: {e}")

@cli.command()
@click.option('--document-token', '-d', required=True, help='飞书文档token / Feishu document token')
@click.option('--output-file', '-o', help='输出文件路径 / Output file path (可选)')
def extract_document(document_token, output_file):
    """提取飞书文档内容并以markdown格式展示 / Extract Feishu document content in markdown format"""
    console.print(Panel.fit("📄 飞书文档内容提取 / Feishu Document Content Extraction", style="blue"))
    
    try:
        client = FeishuClient()
        console.print(f"📋 正在解析文档: {document_token}")
        
        result = client.parse_prd_document(document_token)
        
        # 构建完整的markdown文档
        markdown_content = []
        
        # 添加文档标题
        title = result.get('title', '未命名文档')
        if title:
            markdown_content.append(f"# {title}")
            markdown_content.append("")  # 空行
        
        # 添加文档基本信息
        markdown_content.append("## 📊 文档信息")
        markdown_content.append("")
        markdown_content.append(f"- **文档ID**: `{document_token}`")
        markdown_content.append(f"- **文本长度**: {len(result['text_content'])} 字符")
        markdown_content.append(f"- **块数量**: {result['blocks_count']}")
        markdown_content.append(f"- **解析时间**: {result.get('parsed_at', '未知')}")
        markdown_content.append("")
        
        # 添加文档结构信息
        structure = result.get('structure', {})
        if structure.get('headings'):
            markdown_content.append("## 📋 文档结构")
            markdown_content.append("")
            for i, heading in enumerate(structure['headings'], 1):
                markdown_content.append(f"{i}. {heading}")
            markdown_content.append("")
        
        # 添加分割线
        markdown_content.append("---")
        markdown_content.append("")
        
        # 添加文档内容
        markdown_content.append("## 📄 文档内容")
        markdown_content.append("")
        
        # 处理文档内容，确保markdown格式正确
        content = result.get('text_content', '').strip()
        if content:
            # 按段落分割并重新格式化
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
            for paragraph in paragraphs:
                # 如果段落以数字开头，可能是列表项
                if paragraph and paragraph[0].isdigit() and '、' in paragraph:
                    markdown_content.append(f"- {paragraph}")
                else:
                    markdown_content.append(paragraph)
                markdown_content.append("")  # 段落间空行
        else:
            markdown_content.append("*文档内容为空*")
            markdown_content.append("")
        
        # 合并所有内容
        full_markdown = '\n'.join(markdown_content)
        
        # 显示内容
        console.print(Panel(full_markdown, title="📄 Markdown格式文档内容", style="cyan", expand=True))
        
        # 如果指定了输出文件，保存到文件
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(full_markdown)
            console.print(f"✅ 文档已保存到: {output_file}", style="green")
        
        # 显示统计信息
        stats_table = Table(title="📈 内容统计")
        stats_table.add_column("项目", style="cyan")
        stats_table.add_column("数量", style="green")
        
        lines = full_markdown.split('\n')
        words = len(full_markdown.split())
        chars = len(full_markdown)
        
        stats_table.add_row("总行数", str(len(lines)))
        stats_table.add_row("总词数", str(words))
        stats_table.add_row("总字符数", str(chars))
        stats_table.add_row("段落数", str(len(paragraphs) if 'paragraphs' in locals() else 0))
        
        console.print(stats_table)
        
    except Exception as e:
        console.print(f"❌ 提取失败: {e}", style="red")
        logger.error(f"文档提取失败: {e}")

@cli.command()
@click.option('--figma-url', '-f', required=True, help='Figma设计稿URL / Figma design URL')
def test_figma_url(figma_url):
    """测试Figma URL解析 / Test Figma URL parsing"""
    console.print(Panel.fit("🎨 Figma URL解析测试 / Figma URL Parsing Test", style="blue"))
    
    try:
        figma_client = FigmaClient()
        
        # 解析URL
        console.print(f"🔍 解析URL: {figma_url}")
        figma_info = figma_client.parse_figma_url(figma_url)
        
        # 显示解析结果
        table = Table(title="URL解析结果 / URL Parsing Result")
        table.add_column("项目 / Item", style="cyan")
        table.add_column("值 / Value", style="green")
        
        table.add_row("文件ID / File ID", figma_info['file_id'])
        table.add_row("节点ID / Node ID", figma_info.get('node_id', '未指定 / Not specified'))
        
        console.print(table)
        
        # 尝试获取文件信息
        console.print("📄 获取文件信息...")
        file_info = figma_client.get_file_info(figma_info['file_id'])
        
        file_table = Table(title="文件信息 / File Information")
        file_table.add_column("属性 / Property", style="cyan")
        file_table.add_column("值 / Value", style="green")
        
        file_table.add_row("文件名 / Name", file_info.get('name', 'N/A'))
        file_table.add_row("最后修改 / Last Modified", file_info.get('lastModified', 'N/A'))
        file_table.add_row("版本 / Version", file_info.get('version', 'N/A'))
        
        # 显示页面信息
        pages = file_info.get('document', {}).get('children', [])
        if pages:
            file_table.add_row("页面数量 / Pages Count", str(len(pages)))
            for i, page in enumerate(pages):
                file_table.add_row(f"页面{i+1} / Page {i+1}", f"{page.get('name', 'N/A')} (ID: {page.get('id', 'N/A')})")
        
        console.print(file_table)
        
        console.print("✅ Figma URL解析和访问测试成功！", style="green")
        
    except Exception as e:
        console.print(f"❌ 测试失败: {e}", style="red")
        logger.error(f"Figma URL测试失败: {e}")

@cli.command()
@click.option('--website-url', '-w', required=True, help='网站URL / Website URL')
@click.option('--figma-url', '-f', required=True, help='Figma设计稿URL / Figma design URL')
@click.option('--selector', '-s', help='CSS选择器(可选，用于截取特定元素) / CSS selector (optional, for specific element)')
@click.option('--classes', '-c', help='CSS类组合(可选，用于截取特定元素) / CSS classes combination (optional, for specific element)')
@click.option('--device', '-d', default='desktop', help='设备类型 / Device type (desktop, mobile, tablet)')
@click.option('--output-dir', '-o', default='reports', help='输出目录 / Output directory')
@click.option('--wait-time', '-t', default=3, help='页面加载等待时间(秒) / Page load wait time (seconds)')
@click.option('--language', '-l', default='en-US', help='浏览器语言设置 / Browser language setting')
def compare_web_figma(website_url, figma_url, selector, classes, device, output_dir, wait_time, language):
    """比对网页与Figma设计稿 / Compare website with Figma design"""
    console.print(Panel.fit("🔍 网页与Figma设计稿比对 / Website vs Figma Design Comparison", style="blue"))
    
    try:
        # 验证参数
        if selector and classes:
            console.print("❌ 不能同时指定 --selector 和 --classes 参数", style="red")
            return
        
        # 验证配置
        if not Config.validate_config():
            console.print("❌ 配置验证失败，请检查.env文件", style="red")
            return
        
        # 清理旧报告目录（只保留最新的一个）
        cleanup_old_reports(output_dir)
        
        # 创建输出目录
        timestamp = int(time.time())
        current_output_dir = os.path.join(output_dir, f"comparison_{timestamp}")
        os.makedirs(current_output_dir, exist_ok=True)
        
        # 1. 网页截图
        if selector:
            console.print(f"📸 正在截取网页元素 (选择器): {selector}")
        elif classes:
            console.print(f"📸 正在截取网页元素 (类组合): {classes}")
        else:
            console.print("📸 正在截取网页...")
        
        screenshot_capture = ScreenshotCapture(language=language)
        website_screenshot_path = os.path.join(current_output_dir, f"website_{device}.png")
        
        try:
            if selector:
                # 使用CSS选择器截取特定元素
                screenshot_capture.capture_element(
                    url=website_url,
                    selector=selector,
                    output_path=website_screenshot_path,
                    device=device,
                    wait_time=wait_time
                )
                console.print(f"✅ 网页元素截图完成: {website_screenshot_path}", style="green")
            elif classes:
                # 使用类组合截取特定元素
                actual_screenshot_path = screenshot_capture.capture_by_classes(
                    url=website_url,
                    classes=classes,
                    output_dir=os.path.dirname(website_screenshot_path),
                    element_index=0,
                    device=device,
                    wait_time=wait_time
                )
                
                # 检查截图是否成功生成
                if not actual_screenshot_path or not os.path.exists(actual_screenshot_path):
                    raise ValueError(f"类组合截图失败，未生成文件: {classes}")
                
                # 重命名文件到期望的路径
                try:
                    import shutil
                    shutil.move(actual_screenshot_path, website_screenshot_path)
                    console.print(f"✅ 网页元素截图完成: {website_screenshot_path}", style="green")
                except Exception as rename_error:
                    # 如果重命名失败，使用原文件
                    website_screenshot_path = actual_screenshot_path
                    console.print(f"✅ 网页元素截图完成: {website_screenshot_path}", style="green")
                    console.print(f"⚠️  文件重命名失败，使用原文件名: {rename_error}", style="yellow")
            else:
                # 截取整个页面
                screenshot_capture.capture_url(
                    url=website_url,
                    output_path=website_screenshot_path,
                    device=device,
                    wait_time=wait_time,
                    full_page=True
                )
                console.print(f"✅ 网页截图完成: {website_screenshot_path}", style="green")
        except Exception as e:
            console.print(f"❌ 网页截图失败: {e}", style="red")
            return
        
        # 2. 获取Figma设计稿
        console.print("🎨 正在获取Figma设计稿...")
        figma_client = FigmaClient()
        
        try:
            # 解析Figma URL
            figma_info = figma_client.parse_figma_url(figma_url)
            file_id = figma_info['file_id']
            node_id = figma_info.get('node_id')
            
            if not node_id:
                # 如果没有指定节点，获取文件信息并选择第一个页面
                file_info = figma_client.get_file_info(file_id)
                pages = file_info.get('document', {}).get('children', [])
                if pages:
                    node_id = pages[0]['id']
                    console.print(f"🔄 未指定节点，使用第一个页面: {node_id}")
                else:
                    raise ValueError("无法找到可用的节点")
            
            # 导出图片
            image_urls = figma_client.export_images(
                file_id=file_id,
                node_ids=[node_id],
                format="png",
                scale=2.0
            )
            
            # 调试信息
            console.print(f"🔍 导出结果: {len(image_urls) if image_urls else 0} 个URL")
            if image_urls:
                for key, url in image_urls.items():
                    console.print(f"   节点 {key}: {url[:50] if url else 'None'}...")
            
            if not image_urls:
                raise ValueError("Figma API没有返回任何图片URL")
            
            # 查找可用的图片URL
            figma_image_url = None
            actual_node_id = None
            
            # 首先尝试原始节点ID
            if node_id in image_urls and image_urls[node_id]:
                figma_image_url = image_urls[node_id]
                actual_node_id = node_id
            else:
                # 如果原始节点ID不行，尝试第一个可用的URL
                for key, url in image_urls.items():
                    if url:  # 确保URL不为空
                        figma_image_url = url
                        actual_node_id = key
                        break
            
            if not figma_image_url:
                raise ValueError(f"无法找到有效的图片URL。节点ID: {node_id}, 可用节点: {list(image_urls.keys())}")
            
            console.print(f"✅ 使用节点 {actual_node_id} 的图片")
            
            # 下载图片
            figma_image_path = os.path.join(current_output_dir, f"figma_design.png")
            figma_client.download_image(figma_image_url, figma_image_path)
            
            console.print(f"✅ Figma设计稿获取完成: {figma_image_path}", style="green")
            
        except Exception as e:
            console.print(f"❌ Figma设计稿获取失败: {e}", style="red")
            return
        
        # 3. 进行视觉比对
        console.print("🔍 正在进行视觉比对...")
        comparator = VisualComparator()
        
        try:
            comparison_result = comparator.compare_images(
                image1_path=website_screenshot_path,
                image2_path=figma_image_path,
                output_dir=current_output_dir
            )
            
            # 显示比对结果
            table = Table(title="比对结果 / Comparison Results")
            table.add_column("指标 / Metric", style="cyan")
            table.add_column("值 / Value", style="green")
            table.add_column("说明 / Description", style="yellow")
            
            table.add_row(
                "相似度分数 / Similarity Score", 
                f"{comparison_result.similarity_score:.3f}",
                comparator._get_overall_rating(comparison_result.similarity_score)
            )
            table.add_row(
                "结构相似性 / SSIM", 
                f"{comparison_result.ssim_score:.3f}",
                "1.0为完全相似"
            )
            table.add_row(
                "均方误差 / MSE", 
                f"{comparison_result.mse_score:.2f}",
                "数值越小越相似"
            )
            table.add_row(
                "哈希距离 / Hash Distance", 
                str(comparison_result.hash_distance),
                "距离越小越相似"
            )
            table.add_row(
                "差异区域数 / Differences Count", 
                str(comparison_result.differences_count),
                "检测到的差异区域数量"
            )
            
            console.print(table)
            
            # 显示分析结果
            if comparison_result.analysis:
                analysis = comparison_result.analysis
                console.print(f"\n📊 详细分析:")
                console.print(f"• 图像尺寸: {analysis.get('image_dimensions', {}).get('width', 'N/A')} x {analysis.get('image_dimensions', {}).get('height', 'N/A')}")
                console.print(f"• 差异面积占比: {analysis.get('diff_percentage', 0):.2f}%")
                
                if 'color_analysis' in analysis:
                    color_diff = analysis['color_analysis'].get('max_color_diff', 0)
                    console.print(f"• 最大颜色差异: {color_diff:.2f}")
            
            # 显示差异图像路径
            console.print(f"\n🖼️  差异对比图像: {comparison_result.diff_image_path}")
            
            # 生成详细报告
            report_path = os.path.join(current_output_dir, "comparison_report.json")
            comparator.generate_report(comparison_result, report_path)
            
            # 显示建议
            console.print(f"\n💡 改进建议:")
            recommendations = comparator._generate_recommendations(comparison_result)
            for i, recommendation in enumerate(recommendations, 1):
                console.print(f"{i}. {recommendation}")
            
            console.print(f"\n📄 详细报告: {report_path}", style="cyan")
            console.print(f"📁 所有文件保存在: {current_output_dir}", style="cyan")
            
        except Exception as e:
            console.print(f"❌ 视觉比对失败: {e}", style="red")
            return
            
    except Exception as e:
        console.print(f"❌ 比对过程失败: {e}", style="red")
        logger.error(f"比对失败: {e}")

@cli.command()
@click.option('--website-url', '-w', required=True, help='网站URL / Website URL')
@click.option('--classes', '-c', required=True, help='CSS类组合(空格分隔) / CSS classes combination (space separated)')
@click.option('--device', '-d', default='desktop', help='设备类型 / Device type')
@click.option('--wait-time', '-t', default=3, help='等待时间(秒) / Wait time (seconds)')
@click.option('--language', '-l', default='en-US', help='浏览器语言设置 / Browser language setting')
def find_by_classes(website_url, classes, device, wait_time, language):
    """查找包含指定类组合的元素 / Find elements with specific class combination"""
    console.print(Panel.fit("🔍 CSS类组合元素查找 / CSS Classes Element Search", style="blue"))
    
    try:
        # 创建截图捕获器
        screenshot_capture = ScreenshotCapture(language=language)
        
        console.print(f"🌐 访问网站: {website_url}")
        console.print(f"🎯 目标类组合: {classes}")
        console.print(f"📱 设备类型: {device}")
        
        # 构建CSS选择器并显示
        selector = screenshot_capture.build_class_selector(classes)
        console.print(f"🔧 构建的CSS选择器: {selector}")
        
        # 查找元素
        elements_info = screenshot_capture.find_elements_by_classes(
            url=website_url,
            classes=classes,
            device=device,
            wait_time=wait_time
        )
        
        if not elements_info:
            console.print("❌ 未找到匹配的元素", style="red")
            return
        
        console.print(f"✅ 找到 {len(elements_info)} 个匹配元素", style="green")
        
        # 显示元素信息表格
        table = Table(title=f"匹配元素信息 / Found Elements ({len(elements_info)} 个)")
        table.add_column("索引 / Index", style="cyan")
        table.add_column("标签 / Tag", style="yellow")
        table.add_column("位置 / Location", style="blue")
        table.add_column("尺寸 / Size", style="green")
        table.add_column("显示 / Display", style="magenta")
        table.add_column("文本预览 / Text Preview", style="white")
        
        for element in elements_info:
            location = f"({element['location']['x']}, {element['location']['y']})"
            size = f"{element['size']['width']}×{element['size']['height']}"
            display_info = f"{element['display']} / {element['position']}"
            text_preview = element['text'][:30] + "..." if len(element['text']) > 30 else element['text']
            visible_mark = "✅" if element['visible'] else "❌"
            
            table.add_row(
                str(element['index']),
                f"{element['tag_name']}{visible_mark}",
                location,
                size,
                display_info,
                text_preview
            )
        
        console.print(table)
        
        # 显示完整类名信息
        if len(elements_info) > 0:
            console.print("\n📋 完整类名信息:")
            for i, element in enumerate(elements_info):
                console.print(f"元素 {i}: {element['classes']}")
                if element['id']:
                    console.print(f"    ID: {element['id']}")
        
    except Exception as e:
        console.print(f"❌ 查找失败: {e}", style="red")
        logger.error(f"类组合元素查找失败: {e}")

@cli.command()
@click.option('--website-url', '-w', required=True, help='网站URL / Website URL')
@click.option('--classes', '-c', required=True, help='CSS类组合(空格分隔) / CSS classes combination (space separated)')
@click.option('--element-index', '-i', default=0, help='元素索引(当有多个匹配时) / Element index (when multiple matches)')
@click.option('--output-dir', '-o', default='screenshots', help='输出目录 / Output directory')
@click.option('--device', '-d', default='desktop', help='设备类型 / Device type')
@click.option('--wait-time', '-t', default=3, help='等待时间(秒) / Wait time (seconds)')
@click.option('--language', '-l', default='en-US', help='浏览器语言设置 / Browser language setting')
def capture_by_classes(website_url, classes, element_index, output_dir, device, wait_time, language):
    """通过CSS类组合截取元素 / Capture element by CSS classes combination"""
    console.print(Panel.fit("📸 CSS类组合元素截图 / CSS Classes Element Capture", style="blue"))
    
    try:
        # 创建截图捕获器
        screenshot_capture = ScreenshotCapture(language=language)
        
        console.print(f"🌐 访问网站: {website_url}")
        console.print(f"🎯 目标类组合: {classes}")
        console.print(f"📍 元素索引: {element_index}")
        console.print(f"📱 设备类型: {device}")
        
        # 构建CSS选择器并显示
        selector = screenshot_capture.build_class_selector(classes)
        console.print(f"🔧 构建的CSS选择器: {selector}")
        
        # 截取元素
        result_path = screenshot_capture.capture_by_classes(
            url=website_url,
            classes=classes,
            output_dir=output_dir,
            element_index=element_index,
            device=device,
            wait_time=wait_time
        )
        
        console.print(f"✅ 元素截图完成: {result_path}", style="green")
        
        # 显示文件信息
        if os.path.exists(result_path):
            file_size = os.path.getsize(result_path)
            console.print(f"📄 文件大小: {file_size / 1024:.1f} KB")
            
            # 使用PIL获取图片尺寸
            try:
                from PIL import Image
                with Image.open(result_path) as img:
                    console.print(f"🖼️  图片尺寸: {img.width} x {img.height}")
            except Exception:
                pass
        
        console.print(f"📁 保存位置: {os.path.abspath(result_path)}", style="cyan")
        
        # 提示用户如何继续
        console.print(f"\n💡 使用提示:")
        console.print(f"• 可以通过 find-by-classes 命令先查看所有匹配元素")
        console.print(f"• 使用 --element-index 参数选择不同的元素")
        console.print(f"• 可以将此截图与Figma设计稿进行比对")
        
    except Exception as e:
        console.print(f"❌ 截图失败: {e}", style="red")
        logger.error(f"类组合元素截图失败: {e}")

@cli.command()
@click.option('--website-url', '-w', required=True, help='网站URL / Website URL')
@click.option('--selector', '-s', required=True, help='CSS选择器 / CSS selector')
@click.option('--output-path', '-o', default='screenshots', help='输出路径 / Output path')
@click.option('--device', '-d', default='desktop', help='设备类型 / Device type')
@click.option('--wait-time', '-t', default=3, help='等待时间(秒) / Wait time (seconds)')
@click.option('--language', '-l', default='en-US', help='浏览器语言设置 / Browser language setting')
def capture_element(website_url, selector, output_path, device, wait_time, language):
    """截取网页特定元素 / Capture specific website element"""
    console.print(Panel.fit("📸 网页元素截图 / Website Element Screenshot", style="blue"))
    
    try:
        # 创建截图捕获器
        screenshot_capture = ScreenshotCapture(language=language)
        
        # 生成文件名
        timestamp = int(time.time())
        safe_selector = selector.replace('.', '').replace('#', '').replace(' ', '_').replace('>', '_')
        filename = f"element_{safe_selector}_{timestamp}.png"
        
        if os.path.isdir(output_path):
            full_output_path = os.path.join(output_path, filename)
        else:
            full_output_path = output_path
        
        console.print(f"🌐 访问网站: {website_url}")
        console.print(f"🎯 目标选择器: {selector}")
        console.print(f"📱 设备类型: {device}")
        
        # 截取元素
        result_path = screenshot_capture.capture_element(
            url=website_url,
            selector=selector,
            output_path=full_output_path,
            device=device,
            wait_time=wait_time
        )
        
        console.print(f"✅ 元素截图完成: {result_path}", style="green")
        
        # 显示文件信息
        if os.path.exists(result_path):
            file_size = os.path.getsize(result_path)
            console.print(f"📄 文件大小: {file_size / 1024:.1f} KB")
            
            # 使用PIL获取图片尺寸
            try:
                from PIL import Image
                with Image.open(result_path) as img:
                    console.print(f"🖼️  图片尺寸: {img.width} x {img.height}")
            except Exception:
                pass
        
        console.print(f"📁 保存位置: {os.path.abspath(result_path)}", style="cyan")
        
    except Exception as e:
        console.print(f"❌ 截图失败: {e}", style="red")
        logger.error(f"元素截图失败: {e}")

@cli.command()
@click.option('--app-token', '-a', required=True, help='多维表格应用token / Bitable app token')
@click.option('--table-id', '-t', required=True, help='数据表ID / Table ID')
@click.option('--record-id', '-r', required=True, help='记录ID / Record ID')
@click.option('--prd-document-token', '-p', required=True, help='PRD文档token / PRD document token')
@click.option('--figma-url', '-f', required=True, help='Figma设计稿URL / Figma design URL')
@click.option('--website-url', '-w', required=True, help='网站URL / Website URL')
@click.option('--website-classes', '-c', help='网站CSS类名(可选) / Website CSS classes (optional)')
@click.option('--device', '-d', default='desktop', help='设备类型 / Device type (desktop, mobile, tablet)')
@click.option('--output-dir', '-o', default='reports', help='输出目录 / Output directory')
@click.option('--test-type', '--type', type=click.Choice(['功能测试', 'UI测试', '完整测试']), default='完整测试', help='测试类型 / Test type')
def execute_workflow(app_token, table_id, record_id, prd_document_token, 
                    figma_url, website_url, website_classes, device, output_dir, test_type):
    """执行工作流：根据测试类型执行相应流程 / Execute workflow: execute corresponding processes based on test type"""
    test_type_display = {
        '功能测试': '🧪 功能测试 (PRD解析+测试用例生成)',
        'UI测试': '🎨 UI测试 (Figma与网站视觉比较)',
        '完整测试': '🚀 完整测试 (功能测试+UI测试)'
    }
    
    panel_title = test_type_display.get(test_type, f"🚀 {test_type}")
    console.print(Panel.fit(panel_title, style="blue"))
    
    try:
        # 验证配置
        if not Config.validate_config():
            console.print("❌ 配置验证失败，请检查.env文件", style="red")
            return
        
        # 创建工作流执行器
        executor = WorkflowExecutor()
        
        console.print("📋 工作流参数 / Workflow Parameters:")
        param_table = Table()
        param_table.add_column("参数 / Parameter", style="cyan")
        param_table.add_column("值 / Value", style="green")
        
        param_table.add_row("测试类型 / Test Type", test_type)
        param_table.add_row("多维表格Token / App Token", app_token)
        param_table.add_row("数据表ID / Table ID", table_id)
        param_table.add_row("记录ID / Record ID", record_id)
        param_table.add_row("PRD文档Token / PRD Document Token", prd_document_token)
        param_table.add_row("Figma URL", figma_url)
        param_table.add_row("网站URL / Website URL", website_url)
        param_table.add_row("CSS类名 / CSS Classes", website_classes or "全页截图")
        param_table.add_row("设备类型 / Device", device)
        param_table.add_row("输出目录 / Output Directory", output_dir)
        
        console.print(param_table)
        
        # 执行工作流
        console.print(f"\n🔄 开始执行{test_type}...")
        result = executor.execute_button_click(
            app_token=app_token,
            table_id=table_id,
            record_id=record_id,
            prd_document_token=prd_document_token,
            figma_url=figma_url,
            website_url=website_url,
            xpath_selector=website_classes,
            device=device,
            output_dir=output_dir,
            test_type=test_type
        )
        
        # 显示结果
        if result['status'] == 'success':
            executed_test_type = result.get('test_type', test_type)
            console.print(f"✅ {executed_test_type}执行成功！", style="green")
            
            # 根据测试类型显示相应结果
            if test_type == "功能测试" or test_type == "完整测试":
                # 显示测试用例生成结果
                if result['test_cases']:
                    test_cases = result['test_cases']
                    console.print(f"\n📋 功能测试结果 (测试用例生成):")
                    console.print(f"• PRD文档长度: {test_cases['prd_text_length']} 字符")
                    console.print(f"• 生成时间: {test_cases['generated_at']}")
                    console.print(f"• 测试用例已填入多维表格")
                    
                    # 显示API状态
                    api_status = test_cases.get('api_status', 'unknown')
                    if api_status == 'failed':
                        console.print(f"⚠️  Gemini API调用失败，已生成错误报告", style="yellow")
                    else:
                        console.print(f"✅ 测试用例生成成功", style="green")
                elif test_type == "功能测试":
                    console.print(f"\n⚠️  功能测试未产生结果", style="yellow")
            
            if test_type == "UI测试" or test_type == "完整测试":
                # 显示视觉比较结果
                if result['comparison_result']:
                    comp_result = result['comparison_result']
                    comp_data = comp_result['comparison_result']
                    
                    console.print(f"\n🔍 UI测试结果 (视觉比较):")
                    comp_table = Table()
                    comp_table.add_column("指标 / Metric", style="cyan")
                    comp_table.add_column("值 / Value", style="green")
                    
                    comp_table.add_row("相似度分数 / Similarity Score", f"{comp_data['similarity_score']:.3f}")
                    comp_table.add_row("结构相似性 / SSIM", f"{comp_data['ssim_score']:.3f}")
                    comp_table.add_row("均方误差 / MSE", f"{comp_data['mse_score']:.2f}")
                    comp_table.add_row("哈希距离 / Hash Distance", str(comp_data['hash_distance']))
                    comp_table.add_row("差异区域数 / Differences", str(comp_data['differences_count']))
                    
                    console.print(comp_table)
                    console.print(f"📁 输出目录: {comp_result['output_directory']}")
                elif test_type == "UI测试":
                    console.print(f"\n⚠️  UI测试未产生结果", style="yellow")
            
            # 显示多维表格更新结果
            if result['bitable_updates']:
                bitable_result = result['bitable_updates']
                console.print(f"\n📊 多维表格更新结果:")
                console.print(f"• 更新字段: {', '.join(bitable_result['updated_fields'])}")
                console.print(f"• 更新时间: {bitable_result['updated_at']}")
            
        else:
            console.print(f"❌ {test_type}执行失败", style="red")
            for error in result['errors']:
                console.print(f"• {error}", style="red")
    
    except Exception as e:
        console.print(f"❌ 工作流执行异常: {e}", style="red")
        logger.error(f"工作流执行异常: {e}")

@cli.command()
@click.option('--app-token', '-a', required=True, help='多维表格应用token / Bitable app token')
@click.option('--table-id', '-t', required=True, help='数据表ID / Table ID')
def inspect_bitable(app_token, table_id):
    """检查多维表格结构 / Inspect bitable structure"""
    console.print(Panel.fit("🔍 检查多维表格结构 / Inspect Bitable Structure", style="blue"))
    
    try:
        # 创建工作流执行器
        executor = WorkflowExecutor()
        
        console.print(f"📊 正在检查表格: {table_id}")
        structure = executor.get_bitable_structure(app_token, table_id)
        
        # 显示表格信息
        table_info = structure['table_info']
        info_table = Table(title="表格信息 / Table Information")
        info_table.add_column("属性 / Property", style="cyan")
        info_table.add_column("值 / Value", style="green")
        
        info_table.add_row("表格名称 / Name", table_info.get('name', 'N/A'))
        info_table.add_row("表格ID / Table ID", table_info.get('table_id', 'N/A'))
        info_table.add_row("总记录数 / Total Records", str(structure['total_records']))
        
        console.print(info_table)
        
        # 显示字段信息
        fields = structure['fields']
        console.print(f"\n📋 字段列表 / Fields List ({len(fields)} 个字段):")
        
        fields_table = Table()
        fields_table.add_column("字段名 / Field Name", style="cyan")
        fields_table.add_column("类型 / Type", style="green")
        fields_table.add_column("描述 / Description", style="yellow")
        
        for field in fields:
            field_name = field.get('field_name', 'N/A')
            field_type = field.get('type', 'N/A')
            description = field.get('description', '') or 'N/A'
            
            # Ensure all values are strings for proper rendering
            field_name = str(field_name) if field_name is not None else 'N/A'
            field_type = str(field_type) if field_type is not None else 'N/A'  
            description = str(description) if description is not None else 'N/A'
            
            fields_table.add_row(field_name, field_type, description)
        
        console.print(fields_table)
        
        # 显示示例记录
        sample_records = structure['sample_records']
        if sample_records:
            console.print(f"\n📄 示例记录 / Sample Records (显示前3条):")
            for i, record in enumerate(sample_records[:3], 1):
                record_id = record.get('record_id', 'N/A')
                console.print(f"\n记录 {i} / Record {i} (ID: {record_id}):")
                record_fields = record.get('fields', {})
                for field_name, field_value in record_fields.items():
                    # 限制显示长度
                    if isinstance(field_value, str) and len(field_value) > 100:
                        field_value = field_value[:100] + "..."
                    # Ensure field values are strings for proper display
                    field_value = str(field_value) if field_value is not None else 'N/A'
                    field_name = str(field_name) if field_name is not None else 'N/A'
                    console.print(f"  • {field_name}: {field_value}")
        
        console.print(f"\n💡 使用提示:")
        console.print(f"• 确保多维表格中包含以下字段用于工作流更新:")
        console.print(f"  - 测试用例 (用于存储生成的测试用例)")
        console.print(f"  - 网站相似度报告 (用于存储比较结果)")
        console.print(f"  - 执行结果 (用于标记执行状态)")
        console.print(f"  - 执行时间 (用于记录执行时间)")
        
    except Exception as e:
        console.print(f"❌ 检查表格结构失败: {e}", style="red")
        logger.error(f"检查表格结构失败: {e}")

@cli.command()
@click.option('--app-token', '-a', required=True, help='多维表格应用token / Bitable app token')
@click.option('--table-id', '-t', required=True, help='数据表ID / Table ID')
@click.option('--record-id', '-r', required=True, help='记录ID / Record ID')
@click.option('--field-name', '-f', required=True, help='字段名称 / Field name')
@click.option('--field-value', '-v', required=True, help='字段值 / Field value')
def test_bitable_update(app_token, table_id, record_id, field_name, field_value):
    """测试多维表格字段更新 / Test bitable field update"""
    console.print(Panel.fit("🧪 测试多维表格字段更新 / Test Bitable Field Update", style="blue"))
    
    try:
        # 验证配置
        if not Config.validate_config():
            console.print("❌ 配置验证失败，请检查.env文件", style="red")
            return
        
        # 创建飞书客户端
        feishu_client = FeishuClient()
        
        console.print("📋 更新参数 / Update Parameters:")
        param_table = Table()
        param_table.add_column("参数 / Parameter", style="cyan")
        param_table.add_column("值 / Value", style="green")
        
        param_table.add_row("多维表格Token / App Token", app_token)
        param_table.add_row("数据表ID / Table ID", table_id)
        param_table.add_row("记录ID / Record ID", record_id)
        param_table.add_row("字段名称 / Field Name", field_name)
        param_table.add_row("字段值 / Field Value", field_value[:100] + "..." if len(field_value) > 100 else field_value)
        
        console.print(param_table)
        
        # 构造更新字段
        update_fields = {
            field_name: field_value
        }
        
        console.print(f"\n🔄 正在更新字段: {field_name}")
        
        # 执行更新
        result = feishu_client.update_bitable_record(
            app_token=app_token,
            table_id=table_id,
            record_id=record_id,
            fields=update_fields
        )
        
        console.print("✅ 字段更新成功！", style="green")
        
        # 显示更新结果
        console.print(f"\n📊 更新结果:")
        console.print(f"• 记录ID: {result.get('record_id', 'N/A')}")
        console.print(f"• 更新时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 显示更新后的字段值
        updated_fields = result.get('fields', {})
        if field_name in updated_fields:
            updated_value = updated_fields[field_name]
            if isinstance(updated_value, str) and len(updated_value) > 200:
                updated_value = updated_value[:200] + "..."
            console.print(f"• 更新后的值: {updated_value}")
        
        console.print(f"\n💡 测试成功！可以继续运行完整工作流。", style="cyan")
        
    except Exception as e:
        console.print(f"❌ 字段更新失败: {e}", style="red")
        logger.error(f"字段更新失败: {e}")

def main():
    """主函数 Main function"""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n👋 程序已退出 / Program exited", style="yellow")
    except Exception as e:
        console.print(f"❌ 程序错误: {e}", style="red")
        logger.error(f"程序错误: {e}")

if __name__ == "__main__":
    main() 