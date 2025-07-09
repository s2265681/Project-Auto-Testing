"""
飞书多维表格按钮触发的Web API服务器
Web API Server for Feishu Bitable Button Triggers
"""
import os
import json
import logging
import numpy as np
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# 导入项目模块
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
                    logger.warning(f"无法解析目录时间戳: {item}")
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
                logger.info(f"删除旧报告目录: {dir_path}")
                shutil.rmtree(dir_path)
            except Exception as e:
                logger.warning(f"删除目录失败 {dir_path}: {e}")
        
        if dirs_to_delete:
            logger.info(f"已清理 {len(dirs_to_delete)} 个旧报告目录，保留最新的报告")
        
    except Exception as e:
        logger.warning(f"清理旧报告时出错: {e}")
        # 清理失败不应该影响主流程

app = Flask(__name__)
CORS(app)  # 启用跨域支持

def safe_json_convert(obj):
    """
    安全的JSON转换函数，处理numpy类型
    Safe JSON conversion function to handle numpy types
    """
    if isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: safe_json_convert(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [safe_json_convert(v) for v in obj]
    return obj

def convert_local_path_to_url(file_path, base_url=None):
    """
    将本地文件路径转换为可访问的URL
    Convert local file path to accessible URL
    
    Args:
        file_path: 本地文件路径
        base_url: 基础URL，如果为None则使用request的host
    
    Returns:
        可访问的图片URL
    """
    if not file_path or not os.path.exists(file_path):
        return None
    
    # 获取相对于项目根目录的路径
    project_root = os.getcwd()
    try:
        rel_path = os.path.relpath(file_path, project_root)
        # 将Windows路径分隔符转换为URL格式
        url_path = rel_path.replace('\\', '/')
        
        # 构建完整URL
        if base_url:
            return f"{base_url.rstrip('/')}/files/{url_path}"
        else:
            # 使用当前请求的host
            try:
                from flask import request
                return f"{request.scheme}://{request.host}/files/{url_path}"
            except:
                # 如果无法获取request信息，返回相对路径
                return f"/files/{url_path}"
    except Exception as e:
        logger.warning(f"路径转换失败: {e}")
        return None

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler('logs/api_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 初始化工作流执行器
try:
    workflow_executor = WorkflowExecutor()
    logger.info("工作流执行器初始化成功")
except Exception as e:
    logger.error(f"工作流执行器初始化失败: {e}")
    workflow_executor = None

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "飞书自动化测试服务"
    })

@app.route('/files/<path:filename>')
def serve_static_files(filename):
    """
    静态文件服务端点
    Static file serving endpoint
    """
    try:
        # 获取项目根目录
        project_root = os.getcwd()
        file_path = os.path.join(project_root, filename)
        
        # 安全检查：确保文件在项目目录内
        if not os.path.abspath(file_path).startswith(os.path.abspath(project_root)):
            logger.warning(f"尝试访问项目外文件: {filename}")
            return jsonify({"error": "Access denied"}), 403
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            logger.warning(f"文件不存在: {filename}")
            return jsonify({"error": "File not found"}), 404
        
        # 获取文件所在目录和文件名
        directory = os.path.dirname(file_path)
        file_name = os.path.basename(file_path)
        
        logger.info(f"提供静态文件: {filename}")
        return send_from_directory(directory, file_name)
        
    except Exception as e:
        logger.error(f"静态文件服务错误: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/images', methods=['GET'])
def list_generated_images():
    """
    列出所有生成的图片
    List all generated images
    """
    try:
        images = []
        reports_dir = "reports"
        
        if os.path.exists(reports_dir):
            for root, dirs, files in os.walk(reports_dir):
                for file in files:
                    if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, os.getcwd())
                        url_path = rel_path.replace('\\', '/')
                        
                        images.append({
                            "filename": file,
                            "path": file_path,
                            "url": f"{request.scheme}://{request.host}/files/{url_path}",
                            "created_time": os.path.getctime(file_path),
                            "size": os.path.getsize(file_path)
                        })
        
        # 按创建时间倒序排列
        images.sort(key=lambda x: x['created_time'], reverse=True)
        
        return jsonify({
            "success": True,
            "total": len(images),
            "images": images[:20]  # 只返回最新的20张图片
        })
        
    except Exception as e:
        logger.error(f"获取图片列表失败: {e}")
        return jsonify({"error": "Failed to get images list"}), 500

@app.route('/api/execute-workflow', methods=['POST'])
def execute_workflow():
    """
    执行工作流程的主要API端点
    Main API endpoint for executing workflow
    """
    try:
        # 记录请求信息
        logger.info(f"收到工作流执行请求，来源IP: {request.remote_addr}")
        logger.info(f"请求方法: {request.method}")
        logger.info(f"请求URL: {request.url}")
        logger.info(f"请求头: {dict(request.headers)}")
        
        # 尝试从JSON请求体获取参数
        data = {}
        json_data = request.get_json(silent=True)
        if json_data:
            data.update(json_data)
            logger.info(f"JSON请求体: {json_data}")
        
        # 从URL query parameters获取参数
        query_params = request.args.to_dict()
        if query_params:
            data.update(query_params)
            logger.info(f"Query参数: {query_params}")
        
        # 从form data获取参数
        form_data = request.form.to_dict()
        if form_data:
            data.update(form_data)
            logger.info(f"Form数据: {form_data}")
        
        # 打印所有接收到的参数
        logger.info("=== 接收到的所有参数 ===")
        for key, value in data.items():
            # 对于长文本，只打印前200个字符
            if isinstance(value, str) and len(value) > 200:
                logger.info(f"  {key}: {value[:200]}... (截断，总长度: {len(value)})")
            else:
                logger.info(f"  {key}: {value}")
        logger.info("=== 参数打印完成 ===")
        
        # 如果没有参数，返回错误
        if not data:
            return jsonify({
                "success": False,
                "error": "未接收到任何参数"
            }), 400
        
        # 提取参数
        doc_token = data.get('docToken')
        
        # 处理超链接对象格式的docToken
        if isinstance(doc_token, dict):
            # 超链接对象格式：{"text": "AI 日历", "link": "https://..."}
            if 'link' in doc_token:
                actual_link = doc_token['link']
                logger.info(f"检测到docToken为超链接对象格式，提取链接: {actual_link}")
                doc_token = actual_link
            elif 'text' in doc_token:
                # 如果只有text字段，保持原样，让extract_document_token处理
                text_content = doc_token['text']
                logger.info(f"检测到docToken为超链接对象但无link字段，使用text内容: {text_content}")
                doc_token = text_content
            else:
                logger.warning(f"docToken超链接对象格式不正确: {doc_token}")
                doc_token = str(doc_token) if doc_token else None
        
        figma_url = data.get('figmaUrl')
        web_url_raw = data.get('webUrl')
        
        # 解析webUrl参数，支持URL:XPath格式和@URL:XPath格式
        website_url = None
        xpath_selector = None
        
        if web_url_raw:
            logger.info(f"原始webUrl: {web_url_raw}")
            
            # 处理@URL:XPath格式
            if web_url_raw.startswith('@') and ':' in web_url_raw:
                try:
                    # 移除@符号
                    url_xpath = web_url_raw[1:]
                    logger.info(f"移除@后: {url_xpath}")
                    
                    # 查找第一个:的位置（URL后面的冒号）
                    if '://' in url_xpath:
                        protocol_end = url_xpath.find('://') + 3
                        colon_pos = url_xpath.find(':', protocol_end)
                        logger.info(f"协议结束位置: {protocol_end}, 冒号位置: {colon_pos}")
                        
                        if colon_pos != -1:
                            website_url = url_xpath[:colon_pos]
                            xpath_selector = url_xpath[colon_pos + 1:]
                        else:
                            website_url = url_xpath
                    else:
                        parts = url_xpath.split(':', 1)
                        website_url = parts[0]
                        xpath_selector = parts[1] if len(parts) > 1 else None
                    
                    logger.info(f"解析@URL:XPath格式 - URL: {website_url}, XPath: {xpath_selector}")
                    
                except Exception as e:
                    logger.error(f"解析@URL:XPath格式失败: {e}")
                    return jsonify({
                        "success": False,
                        "error": f"webUrl格式错误，无法解析@URL:XPath格式: {str(e)}",
                        "webUrl": web_url_raw,
                        "webUrlPath": ""
                    }), 400
            
            # 处理直接的URL:XPath格式（不带@前缀）
            elif ':' in web_url_raw and web_url_raw.startswith(('http://', 'https://')):
                try:
                    # 查找协议后的第一个冒号
                    if '://' in web_url_raw:
                        protocol_end = web_url_raw.find('://') + 3
                        colon_pos = web_url_raw.find(':', protocol_end)
                        
                        if colon_pos != -1:
                            website_url = web_url_raw[:colon_pos]
                            xpath_selector = web_url_raw[colon_pos + 1:]
                            logger.info(f"解析URL:XPath格式 - URL: {website_url}, XPath: {xpath_selector}")
                        else:
                            # 没有找到XPath分隔符，整个作为URL
                            website_url = web_url_raw
                            logger.info(f"使用完整URL: {website_url}")
                    else:
                        website_url = web_url_raw
                        logger.info(f"使用完整URL: {website_url}")
                    
                except Exception as e:
                    logger.error(f"解析URL:XPath格式失败: {e}")
                    return jsonify({
                        "success": False,
                        "error": f"webUrl格式错误，无法解析URL:XPath格式: {str(e)}",
                        "webUrl": web_url_raw
                    }), 400
            
            else:
                # 兼容旧格式，直接作为URL
                website_url = web_url_raw
                web_url_path = data.get('webUrlPath', '')
                if web_url_path:
                    if web_url_path.startswith(('http://', 'https://')):
                        website_url = web_url_path
                    else:
                        website_url = f"{website_url.rstrip('/')}/{web_url_path.lstrip('/')}"
                logger.info(f"使用传统URL格式: {website_url}")
        
        # 可选参数（先获取测试类型）
        test_type = data.get('testType', '完整测试')  # 先获取测试类型，决定验证逻辑
        app_token = data.get('appToken', os.getenv('FEISHU_APP_TOKEN'))
        table_id = data.get('tableId', os.getenv('FEISHU_TABLE_ID'))
        record_id = data.get('recordId')
        
        # 处理设备类型 - 支持新的"是否是移动端"字段
        is_mobile = data.get('isMobile', data.get('是否是移动端'))  # 支持中英文字段名
        if is_mobile is not None:
            # 根据"是否是移动端"字段设置device
            if str(is_mobile).strip() in ['是', 'true', 'True', '1', 'yes', 'Yes']:
                device = 'mobile'
                logger.info("检测到移动端标识，设置device为mobile")
            else:
                device = 'desktop'
                logger.info("检测到非移动端标识，设置device为desktop")
        else:
            # 兼容原有的device参数
            device = data.get('device', 'desktop')
            logger.info(f"使用传统device参数: {device}")
        
        # 验证测试类型
        valid_test_types = ['功能测试', 'UI测试', '完整测试']
        if test_type not in valid_test_types:
            return jsonify({
                "success": False,
                "error": f"无效的测试类型: {test_type}，支持的类型: {valid_test_types}"
            }), 400
        
        # 根据测试类型验证必需参数
        if test_type == "功能测试":
            # 功能测试只需要docToken
            if not doc_token:
                return jsonify({
                    "success": False,
                    "error": "功能测试需要提供docToken参数"
                }), 400
        elif test_type == "UI测试":
            # UI测试需要figmaUrl和webUrl，docToken可以为空
            if not figma_url:
                return jsonify({
                    "success": False,
                    "error": "UI测试需要提供figmaUrl参数"
                }), 400
            if not website_url:
                return jsonify({
                    "success": False,
                    "error": "UI测试需要提供webUrl参数",
                    "webUrl": web_url_raw,
                    "webUrlPath": data.get('webUrlPath', '')
                }), 400
            # 验证URL格式
            if not website_url.startswith(('http://', 'https://')):
                return jsonify({
                    "success": False,
                    "error": f"无效的URL格式: {web_url_raw}",
                    "webUrl": web_url_raw,
                    "webUrlPath": data.get('webUrlPath', '')
                }), 400
        else:
            # 完整测试需要所有参数
            if not doc_token:
                return jsonify({
                    "success": False,
                    "error": "完整测试需要提供docToken参数"
                }), 400
            if not figma_url:
                return jsonify({
                    "success": False,
                    "error": "完整测试需要提供figmaUrl参数"
                }), 400
            if not website_url:
                return jsonify({
                    "success": False,
                    "error": "完整测试需要提供webUrl参数",
                    "webUrl": web_url_raw,
                    "webUrlPath": data.get('webUrlPath', '')
                }), 400
            # 验证URL格式
            if not website_url.startswith(('http://', 'https://')):
                return jsonify({
                    "success": False,
                    "error": f"无效的URL格式: {web_url_raw}",
                    "webUrl": web_url_raw,
                    "webUrlPath": data.get('webUrlPath', '')
                }), 400
        
        # 检查docToken是否是错误信息（仅当需要docToken时）
        if test_type in ["功能测试", "完整测试"] and doc_token and doc_token.startswith('#'):
            logger.warning(f"docToken看起来是错误信息，不是有效的token: {doc_token[:100]}...")
            return jsonify({
                "success": False,
                "error": "docToken参数无效 - 似乎是错误信息而不是文档token",
                "received_docToken": doc_token[:200] + "..." if len(doc_token) > 200 else doc_token
            }), 400
        
        # 日志记录参数
        logger.info(f"执行参数: testType={test_type}, docToken={doc_token or 'N/A'}, figmaUrl={figma_url or 'N/A'}, webUrl={website_url or 'N/A'}, xpath={xpath_selector or 'N/A'}")
        
        # 检查工作流执行器
        if not workflow_executor:
            return jsonify({
                "success": False,
                "error": "工作流执行器未初始化"
            }), 500
        
        # 清理旧报告（只保留最新的一个）
        cleanup_old_reports("reports")
        
        # 执行工作流
        try:
            result = workflow_executor.execute_button_click(
                app_token=app_token,
                table_id=table_id,
                record_id=record_id,
                prd_document_token=doc_token,
                figma_url=figma_url,
                website_url=website_url,
                xpath_selector=xpath_selector,  # 新增XPath参数
                device=device,
                output_dir="reports",
                test_type=test_type  # 新增测试类型参数
            )
            
            logger.info(f"{test_type}执行成功")
            
            # 构建返回数据
            return_data = {
                "execution_id": result.get('output_directory', '').split('/')[-1] if result.get('comparison_result') else f"exec_{int(datetime.now().timestamp())}",
                "test_type": test_type,
                "prd_document_token": doc_token,
                "figma_url": figma_url,
                "website_url": website_url,
                "xpath_selector": xpath_selector,
                "device": device,
                "status_updates": result.get('status_updates', []),
                "completed_at": datetime.now().isoformat()
            }
            
            # 根据测试类型添加相应的结果
            if test_type == "功能测试" or test_type == "完整测试":
                if result.get('test_cases'):
                    return_data["test_cases_result"] = safe_json_convert({
                        "generated": result['test_cases'].get('api_status') == 'success',
                        "api_status": result['test_cases'].get('api_status'),
                        "prd_text_length": result['test_cases'].get('prd_text_length'),
                        "generated_at": result['test_cases'].get('generated_at')
                    })
                else:
                    return_data["test_cases_result"] = {"generated": False, "reason": "未执行或执行失败"}
            
            if test_type == "UI测试" or test_type == "完整测试":
                if result.get('comparison_result'):
                    comparison_data = result['comparison_result'].get('comparison_result', {})
                    
                    # 转换图片路径为可访问的URL
                    figma_image_path = result['comparison_result'].get('figma_screenshot')
                    website_image_path = result['comparison_result'].get('website_screenshot')
                    diff_image_path = comparison_data.get('diff_image_path')
                    
                    return_data["comparison_result"] = safe_json_convert({
                        "similarity_score": comparison_data.get('similarity_score', 0),
                        "ssim_score": comparison_data.get('ssim_score', 0),
                        "mse_score": comparison_data.get('mse_score', 0),
                        "hash_distance": comparison_data.get('hash_distance', 0),
                        "differences_count": comparison_data.get('differences_count', 0),
                        "output_directory": result['comparison_result'].get('output_directory'),
                        "figma_image_path": figma_image_path,
                        "website_image_path": website_image_path,
                        "diff_image_path": diff_image_path,
                        "figma_image_url": convert_local_path_to_url(figma_image_path),
                        "website_image_url": convert_local_path_to_url(website_image_path),
                        "diff_image_url": convert_local_path_to_url(diff_image_path)
                    })
                else:
                    return_data["comparison_result"] = {"completed": False, "reason": "未执行或执行失败"}
            
            return jsonify({
                "success": True,
                "message": f"{test_type}执行成功",
                "data": return_data
            })
            
        except Exception as workflow_error:
            logger.error(f"工作流执行失败: {workflow_error}")
            return jsonify({
                "success": False,
                "error": f"工作流执行失败: {str(workflow_error)}"
            }), 500
    
    except Exception as e:
        logger.error(f"API请求处理失败: {e}")
        return jsonify({
            "success": False,
            "error": f"服务器内部错误: {str(e)}"
        }), 500

@app.route('/api/execute-comparison', methods=['POST'])
def execute_comparison():
    """
    仅执行视觉比较的API端点
    API endpoint for executing visual comparison only
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "请求体为空或格式不正确"
            }), 400
        
        # 提取参数
        figma_url = data.get('figmaUrl')
        web_url_raw = data.get('webUrl')
        
        # 解析webUrl参数，支持@URL:XPath格式
        website_url = None
        xpath_selector = None
        
        if web_url_raw:
            if web_url_raw.startswith('@') and ':' in web_url_raw:
                # 解析@URL:XPath格式
                try:
                    # 移除@符号
                    url_xpath = web_url_raw[1:]
                    
                    # 查找第一个:的位置（URL后面的冒号）
                    # 由于URL中可能包含:（如https:），我们需要找到://后面的第一个:
                    if '://' in url_xpath:
                        protocol_end = url_xpath.find('://') + 3
                        colon_pos = url_xpath.find(':', protocol_end)
                        if colon_pos != -1:
                            website_url = url_xpath[:colon_pos]
                            xpath_selector = url_xpath[colon_pos + 1:]
                        else:
                            # 没有找到XPath分隔符，整个作为URL
                            website_url = url_xpath
                    else:
                        # 没有协议，按第一个:分割
                        parts = url_xpath.split(':', 1)
                        website_url = parts[0]
                        xpath_selector = parts[1] if len(parts) > 1 else None
                    
                    logger.info(f"解析@URL:XPath格式 - URL: {website_url}, XPath: {xpath_selector}")
                except Exception as e:
                    logger.error(f"解析@URL:XPath格式失败: {e}")
                    return jsonify({
                        "success": False,
                        "error": f"webUrl格式错误，无法解析@URL:XPath格式: {web_url_raw}"
                    }), 400
            else:
                # 兼容旧格式，直接作为URL
                website_url = web_url_raw
                web_url_path = data.get('webUrlPath', '')
                if web_url_path:
                    if web_url_path.startswith(('http://', 'https://')):
                        website_url = web_url_path
                    else:
                        website_url = f"{website_url.rstrip('/')}/{web_url_path.lstrip('/')}"
                logger.info(f"使用传统URL格式: {website_url}")
        
        # 验证必需参数
        if not figma_url or not website_url:
            return jsonify({
                "success": False,
                "error": "缺少必需参数: figmaUrl 或 webUrl"
            }), 400
        
        # 验证URL格式
        if not website_url.startswith(('http://', 'https://')):
            return jsonify({
                "success": False,
                "error": f"无效的URL格式: {website_url}"
            }), 400
        
        device = data.get('device', 'desktop')
        
        logger.info(f"执行视觉比较: figmaUrl={figma_url}, webUrl={website_url}, xpath={xpath_selector}")
        
        # 检查工作流执行器是否初始化
        if workflow_executor is None:
            return jsonify({
                "success": False,
                "error": "工作流执行器未初始化，请检查服务器配置"
            }), 500
        
        # 清理旧报告（只保留最新的一个）
        cleanup_old_reports("reports")
        
        # 执行视觉比较
        comparison_result = workflow_executor._compare_figma_and_website(
            figma_url=figma_url,
            website_url=website_url,
            xpath_selector=xpath_selector,  # 新增XPath参数
            device=device,
            output_dir="reports"
        )
        
        logger.info("视觉比较执行成功")
        
        # 转换图片路径为可访问的URL
        figma_image_path = comparison_result.get('figma_screenshot')
        website_image_path = comparison_result.get('website_screenshot')
        diff_image_path = comparison_result.get('comparison_result', {}).get('diff_image_path')
        
        return jsonify({
            "success": True,
            "message": "视觉比较执行成功",
            "data": safe_json_convert({
                "figma_url": figma_url,
                "website_url": website_url,
                "xpath_selector": xpath_selector,
                "device": device,
                "similarity_score": comparison_result.get('comparison_result', {}).get('similarity_score', 0),
                "ssim_score": comparison_result.get('comparison_result', {}).get('ssim_score', 0),
                "mse_score": comparison_result.get('comparison_result', {}).get('mse_score', 0),
                "hash_distance": comparison_result.get('comparison_result', {}).get('hash_distance', 0),
                "differences_count": comparison_result.get('comparison_result', {}).get('differences_count', 0),
                "output_directory": comparison_result.get('output_directory'),
                "figma_image_path": figma_image_path,
                "website_image_path": website_image_path,
                "diff_image_path": diff_image_path,
                "figma_image_url": convert_local_path_to_url(figma_image_path),
                "website_image_url": convert_local_path_to_url(website_image_path),
                "diff_image_url": convert_local_path_to_url(diff_image_path),
                "completed_at": datetime.now().isoformat()
            })
        })
        
    except Exception as e:
        logger.error(f"视觉比较执行失败: {e}")
        return jsonify({
            "success": False,
            "error": f"视觉比较执行失败: {str(e)}"
        }), 500

@app.route('/api/generate-test-cases', methods=['POST'])
def generate_test_cases():
    """
    仅生成测试用例的API端点
    API endpoint for generating test cases only
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "请求体为空或格式不正确"
            }), 400
        
        doc_token = data.get('docToken')
        if not doc_token:
            return jsonify({
                "success": False,
                "error": "缺少必需参数: docToken"
            }), 400
        
        logger.info(f"生成测试用例: docToken={doc_token}")
        
        # 检查工作流执行器是否初始化
        if workflow_executor is None:
            return jsonify({
                "success": False,
                "error": "工作流执行器未初始化，请检查服务器配置"
            }), 500
        
        # 生成测试用例
        test_cases_result = workflow_executor._generate_test_cases_from_prd(doc_token)
        
        logger.info("测试用例生成成功")
        
        return jsonify({
            "success": True,
            "message": "测试用例生成成功",
            "data": {
                "document_token": doc_token,
                "test_cases": test_cases_result.get('test_cases_text', ''),
                "api_status": test_cases_result.get('api_status', 'unknown'),
                "prd_text_length": test_cases_result.get('prd_text_length', 0),
                "generated_at": test_cases_result.get('generated_at')
            }
        })
        
    except Exception as e:
        logger.error(f"测试用例生成失败: {e}")
        return jsonify({
            "success": False,
            "error": f"测试用例生成失败: {str(e)}"
        }), 500

@app.route('/api/reset-status', methods=['POST'])
def reset_execution_status():
    """
    重置执行状态为"未开始"
    Reset execution status to "未开始"
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "请求体为空或格式不正确"
            }), 400
        
        # 提取必需参数
        app_token = data.get('appToken', os.getenv('FEISHU_APP_TOKEN'))
        table_id = data.get('tableId', os.getenv('FEISHU_TABLE_ID'))
        record_id = data.get('recordId')
        
        if not app_token or not table_id or not record_id:
            return jsonify({
                "success": False,
                "error": "缺少必需参数: appToken, tableId, recordId"
            }), 400
        
        logger.info(f"重置执行状态: record_id={record_id}")
        
        # 重置状态
        reset_result = workflow_executor.reset_execution_status_to_default(
            app_token=app_token,
            table_id=table_id,
            record_id=record_id
        )
        
        logger.info("执行状态重置成功")
        
        return jsonify({
            "success": True,
            "message": "执行状态重置成功",
            "data": {
                "app_token": app_token,
                "table_id": table_id,
                "record_id": record_id,
                "new_status": "未开始",
                "reset_at": reset_result.get('updated_at')
            }
        })
        
    except Exception as e:
        logger.error(f"重置执行状态失败: {e}")
        return jsonify({
            "success": False,
            "error": f"重置执行状态失败: {str(e)}"
        }), 500

@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return jsonify({
        "success": False,
        "error": "请求的端点不存在"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    logger.error(f"内部服务器错误: {error}")
    return jsonify({
        "success": False,
        "error": "内部服务器错误"
    }), 500

if __name__ == '__main__':
    # 确保日志目录存在
    os.makedirs('logs', exist_ok=True)
    
    # 启动服务器
    host = os.getenv('API_HOST', '0.0.0.0')
    port = int(os.getenv('API_PORT', 5001))
    debug = os.getenv('API_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"启动API服务器: http://{host}:{port}")
    logger.info("可用的API端点:")
    logger.info("  GET  /health - 健康检查")
    logger.info("  GET  /files/<path:filename> - 静态文件服务（图片访问）")
    logger.info("  GET  /api/images - 列出生成的图片")
    logger.info("  POST /api/execute-workflow - 执行工作流 (支持testType参数)")
    logger.info("    • testType='功能测试' - 仅执行PRD解析和测试用例生成")
    logger.info("    • testType='UI测试' - 仅执行Figma与网站视觉比较") 
    logger.info("    • testType='完整测试' - 执行功能测试+UI测试 (默认)")
    logger.info("    • 自动状态更新：未开始 → 进行中 → 已完成/失败")
    logger.info("  POST /api/execute-comparison - 执行视觉比较")
    logger.info("  POST /api/generate-test-cases - 生成测试用例")
    logger.info("  POST /api/reset-status - 重置执行状态为'未开始'")
    logger.info("")
    logger.info("💡 现在可以通过URL直接访问生成的对比图片:")
    logger.info(f"   例如: http://{host}:{port}/files/reports/comparison_xxxxx/diff_comparison_xxxxx.png")
    
    app.run(host=host, port=port, debug=debug) 