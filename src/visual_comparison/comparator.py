"""
视觉比对器模块
Visual Comparator Module
"""
import os
import time
import gc
import psutil
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imagehash
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import json
from datetime import datetime

from ..utils.logger import get_logger
from ..utils.asset_url_converter import convert_diff_image_path, ensure_file_exists

logger = get_logger(__name__)

@dataclass
class ComparisonResult:
    """比对结果数据类"""
    similarity_score: float  # 相似度分数 (0-1)
    mse_score: float        # 均方误差
    ssim_score: float       # 结构相似性指数
    hash_distance: int      # 感知哈希距离
    differences_count: int   # 差异点数量
    diff_image_path: str    # 差异图像路径
    analysis: Dict          # 详细分析结果

class VisualComparator:
    """视觉比对器"""
    
    # 图像处理限制
    MAX_IMAGE_DIMENSION = 2048  # 最大图像尺寸
    MAX_MEMORY_MB = 512  # 最大内存使用(MB)
    
    def __init__(self):
        """初始化比对器"""
        self.process = psutil.Process()
        
    def _log_memory_usage(self, stage: str):
        """记录内存使用情况"""
        memory_info = self.process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        logger.info(f"[{stage}] 内存使用: {memory_mb:.1f} MB")
        
        if memory_mb > self.MAX_MEMORY_MB:
            logger.warning(f"内存使用超过限制 ({memory_mb:.1f} MB > {self.MAX_MEMORY_MB} MB)")
            # 强制垃圾回收
            gc.collect()
    
    def _optimize_image_size(self, image: np.ndarray, max_dimension: int = None) -> np.ndarray:
        """优化图像尺寸以减少内存使用"""
        if max_dimension is None:
            max_dimension = self.MAX_IMAGE_DIMENSION
            
        height, width = image.shape[:2]
        
        # 如果图像尺寸超过限制，进行缩放
        if max(height, width) > max_dimension:
            if height > width:
                new_height = max_dimension
                new_width = int(width * max_dimension / height)
            else:
                new_width = max_dimension
                new_height = int(height * max_dimension / width)
            
            logger.info(f"缩放图像: {width}x{height} -> {new_width}x{new_height}")
            resized_image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
            
            # 释放原图像内存
            del image
            gc.collect()
            
            return resized_image
        
        return image
    
    def compare_images(self, image1_path: str, image2_path: str, 
                      output_dir: str = "reports") -> ComparisonResult:
        """
        比较两张图片的相似度
        
        Args:
            image1_path: 第一张图片路径（网页截图）
            image2_path: 第二张图片路径（Figma设计稿）
            output_dir: 输出目录
            
        Returns:
            比对结果
        """
        try:
            self._log_memory_usage("开始比较")
            logger.info(f"开始比较图片: {image1_path} vs {image2_path}")
            
            # 验证文件路径
            if not os.path.exists(image1_path):
                raise FileNotFoundError(f"图片1不存在: {image1_path}")
            if not os.path.exists(image2_path):
                raise FileNotFoundError(f"图片2不存在: {image2_path}")
            
            # 验证文件大小
            if os.path.getsize(image1_path) == 0:
                raise ValueError(f"图片1文件为空: {image1_path}")
            if os.path.getsize(image2_path) == 0:
                raise ValueError(f"图片2文件为空: {image2_path}")
            
            logger.info(f"图片1路径: {os.path.abspath(image1_path)} (大小: {os.path.getsize(image1_path)} bytes)")
            logger.info(f"图片2路径: {os.path.abspath(image2_path)} (大小: {os.path.getsize(image2_path)} bytes)")
            
            # 读取图片
            img1 = cv2.imread(image1_path)
            img2 = cv2.imread(image2_path)
            
            if img1 is None:
                raise ValueError(f"无法读取图片文件1: {image1_path} (可能格式不支持或文件损坏)")
            if img2 is None:
                raise ValueError(f"无法读取图片文件2: {image2_path} (可能格式不支持或文件损坏)")
            
            logger.info(f"图片1尺寸: {img1.shape}")
            logger.info(f"图片2尺寸: {img2.shape}")
            
            self._log_memory_usage("图片加载完成")
            
            # 优化图像尺寸
            img1 = self._optimize_image_size(img1)
            img2 = self._optimize_image_size(img2)
            
            self._log_memory_usage("图片优化完成")
            
            # 调整图片尺寸到相同大小
            img1_resized, img2_resized = self._resize_images(img1, img2)
            
            # 释放原始图像内存
            del img1, img2
            gc.collect()
            
            self._log_memory_usage("图片缩放完成")
            
            # 计算各种相似度指标
            similarity_score = self._calculate_similarity(img1_resized, img2_resized)
            mse_score = self._calculate_mse(img1_resized, img2_resized)
            ssim_score = self._calculate_ssim(img1_resized, img2_resized)
            hash_distance = self._calculate_hash_distance(image1_path, image2_path)
            
            self._log_memory_usage("相似度计算完成")
            
            # 生成差异图像（使用优化版本）
            diff_image_path = self._generate_diff_image_optimized(
                img1_resized, img2_resized, output_dir
            )
            
            self._log_memory_usage("差异图像生成完成")
            
            # 分析差异
            analysis = self._analyze_differences(img1_resized, img2_resized)
            
            # 释放处理后的图像内存
            del img1_resized, img2_resized
            gc.collect()
            
            self._log_memory_usage("差异分析完成")
            
            result = ComparisonResult(
                similarity_score=similarity_score,
                mse_score=mse_score,
                ssim_score=ssim_score,
                hash_distance=hash_distance,
                differences_count=analysis.get('differences_count', 0),
                diff_image_path=diff_image_path,
                analysis=analysis
            )
            
            logger.info(f"图片比较完成，相似度: {similarity_score:.3f}")
            self._log_memory_usage("比较完成")
            return result
            
        except Exception as e:
            logger.error(f"图片比较失败: {e}")
            # 确保内存清理
            gc.collect()
            raise
    
    def _resize_images(self, img1: np.ndarray, img2: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """调整图片尺寸到相同大小，优化内存使用"""
        h1, w1 = img1.shape[:2]
        h2, w2 = img2.shape[:2]
        
        # 使用较小的尺寸以节省内存
        target_h = min(h1, h2, self.MAX_IMAGE_DIMENSION)
        target_w = min(w1, w2, self.MAX_IMAGE_DIMENSION)
        
        # 调整尺寸保持宽高比
        aspect1 = w1 / h1
        aspect2 = w2 / h2
        
        if aspect1 > 1:  # 横向图片
            final_w = target_w
            final_h = int(target_w / max(aspect1, aspect2))
        else:  # 纵向图片
            final_h = target_h
            final_w = int(target_h * min(aspect1, aspect2))
        
        # 使用INTER_AREA插值算法，适合缩小图像
        img1_resized = cv2.resize(img1, (final_w, final_h), interpolation=cv2.INTER_AREA)
        img2_resized = cv2.resize(img2, (final_w, final_h), interpolation=cv2.INTER_AREA)
        
        return img1_resized, img2_resized
    
    def _calculate_similarity(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """计算基础相似度（基于直方图），优化内存使用"""
        try:
            # 转换为HSV颜色空间
            hsv1 = cv2.cvtColor(img1, cv2.COLOR_BGR2HSV)
            hsv2 = cv2.cvtColor(img2, cv2.COLOR_BGR2HSV)
            
            # 使用较小的bin数量以减少内存使用
            hist1 = cv2.calcHist([hsv1], [0, 1, 2], None, [32, 32, 32], [0, 180, 0, 256, 0, 256])
            hist2 = cv2.calcHist([hsv2], [0, 1, 2], None, [32, 32, 32], [0, 180, 0, 256, 0, 256])
            
            # 释放HSV图像内存
            del hsv1, hsv2
            gc.collect()
            
            # 计算相关性
            correlation = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
            
            # 释放直方图内存
            del hist1, hist2
            gc.collect()
            
            return max(0, correlation)
        except Exception as e:
            logger.error(f"计算相似度失败: {e}")
            gc.collect()
            return 0.0
    
    def _calculate_mse(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """计算均方误差"""
        mse = np.mean((img1.astype(float) - img2.astype(float)) ** 2)
        return mse
    
    def _calculate_ssim(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """计算结构相似性指数，优化内存使用"""
        try:
            # 转换为灰度图
            gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
            
            # 如果图像太大，进一步缩小以节省计算时间和内存
            if gray1.shape[0] * gray1.shape[1] > 1024 * 1024:  # 1M 像素
                scale = 0.5
                new_height = int(gray1.shape[0] * scale)
                new_width = int(gray1.shape[1] * scale)
                
                gray1_small = cv2.resize(gray1, (new_width, new_height))
                gray2_small = cv2.resize(gray2, (new_width, new_height))
                
                del gray1, gray2
                gc.collect()
                
                gray1, gray2 = gray1_small, gray2_small
            
            # 计算SSIM
            from skimage.metrics import structural_similarity
            ssim = structural_similarity(gray1, gray2)
            
            # 释放灰度图像内存
            del gray1, gray2
            gc.collect()
            
            return ssim
        except Exception as e:
            logger.error(f"计算SSIM失败: {e}")
            gc.collect()
            return 0.0
    
    def _calculate_hash_distance(self, img1_path: str, img2_path: str) -> int:
        """计算感知哈希距离"""
        img1 = Image.open(img1_path)
        img2 = Image.open(img2_path)
        
        hash1 = imagehash.phash(img1)
        hash2 = imagehash.phash(img2)
        
        return hash1 - hash2
    
    def _generate_diff_image(self, img1: np.ndarray, img2: np.ndarray, 
                           output_dir: str) -> str:
        """生成差异图像"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            # 计算差异
            diff = cv2.absdiff(img1, img2)
            
            # 增强差异显示
            diff_enhanced = cv2.multiply(diff, 3)
            
            # 创建对比图像
            height, width = img1.shape[:2]
            comparison = np.zeros((height, width * 3, 3), dtype=np.uint8)
            
            # 拼接原图、目标图和差异图
            comparison[:, :width] = img1
            comparison[:, width:2*width] = img2
            comparison[:, 2*width:] = diff_enhanced
            
            # 添加标签
            comparison = self._add_labels(comparison, ['网页截图', 'Figma设计稿', '差异对比'])
            
            # 保存差异图像
            diff_path = os.path.join(output_dir, f"diff_comparison_{int(time.time())}.png")
            cv2.imwrite(diff_path, comparison)
            
            return diff_path
            
        except Exception as e:
            logger.error(f"生成差异图像失败: {e}")
            raise
    
    def _generate_diff_image_optimized(self, img1: np.ndarray, img2: np.ndarray, 
                           output_dir: str) -> str:
        """生成差异图像 (优化内存使用)"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            height, width = img1.shape[:2]
            
            # 为了节省内存，不创建完整的三联图，而是分别保存
            diff_timestamp = int(time.time())
            
            # 计算并保存差异图
            diff = cv2.absdiff(img1, img2)
            diff_enhanced = cv2.multiply(diff, 3)
            
            # 保存单独的差异图像
            diff_only_path = os.path.join(output_dir, f"diff_only_{diff_timestamp}.png")
            cv2.imwrite(diff_only_path, diff_enhanced)
            
            # 创建一个较小的对比图像（缩小尺寸以节省内存）
            scale_factor = min(1.0, 800 / max(width, height))  # 限制最大宽度800px
            if scale_factor < 1.0:
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                
                img1_small = cv2.resize(img1, (new_width, new_height))
                img2_small = cv2.resize(img2, (new_width, new_height))
                diff_small = cv2.resize(diff_enhanced, (new_width, new_height))
                
                # 释放原始差异图像内存
                del diff, diff_enhanced
                gc.collect()
            else:
                img1_small = img1.copy()
                img2_small = img2.copy()
                diff_small = diff_enhanced.copy()
                del diff, diff_enhanced
                gc.collect()
            
            # 创建对比图像（使用较小的尺寸）
            small_height, small_width = img1_small.shape[:2]
            comparison = np.zeros((small_height, small_width * 3, 3), dtype=np.uint8)
            
            # 拼接图像
            comparison[:, :small_width] = img1_small
            comparison[:, small_width:2*small_width] = img2_small
            comparison[:, 2*small_width:] = diff_small
            
            # 释放临时图像内存
            del img1_small, img2_small, diff_small
            gc.collect()
            
            # 添加标签
            comparison = self._add_labels(comparison, ['网页截图', 'Figma设计稿', '差异对比'])
            
            # 保存对比图像
            comparison_path = os.path.join(output_dir, f"diff_comparison_{diff_timestamp}.png")
            cv2.imwrite(comparison_path, comparison)
            
            # 释放对比图像内存
            del comparison
            gc.collect()
            
            return comparison_path
            
        except Exception as e:
            logger.error(f"生成差异图像失败: {e}")
            # 确保内存清理
            gc.collect()
            raise
    
    def _add_labels(self, image: np.ndarray, labels: List[str]) -> np.ndarray:
        """为图像添加标签"""
        try:
            # 转换为PIL图像以便添加文字
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            draw = ImageDraw.Draw(pil_image)
            
            # 尝试加载字体，如果失败则使用默认字体
            try:
                font = ImageFont.truetype("arial.ttf", 24)
            except:
                font = ImageFont.load_default()
            
            width = image.shape[1] // 3
            for i, label in enumerate(labels):
                x = i * width + 10
                y = 10
                draw.text((x, y), label, fill=(255, 255, 255), font=font)
                draw.text((x+1, y+1), label, fill=(0, 0, 0), font=font)  # 阴影效果
            
            # 转换回OpenCV格式
            return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            
        except Exception as e:
            logger.warning(f"添加标签失败，返回原图像: {e}")
            return image
    
    def _analyze_differences(self, img1: np.ndarray, img2: np.ndarray) -> Dict:
        """分析图像差异，优化内存使用"""
        try:
            # 转换为灰度图
            gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
            
            # 计算差异
            diff = cv2.absdiff(gray1, gray2)
            
            # 释放灰度图像内存
            del gray1, gray2
            gc.collect()
            
            # 应用阈值得到二值化差异图
            _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
            
            # 释放差异图像内存
            del diff
            gc.collect()
            
            # 查找轮廓（差异区域）
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # 释放阈值图像内存
            del thresh
            gc.collect()
            
            # 分析差异区域
            differences_count = len(contours)
            total_diff_area = sum(cv2.contourArea(contour) for contour in contours)
            total_area = img1.shape[0] * img1.shape[1]
            diff_percentage = (total_diff_area / total_area) * 100
            
            # 颜色差异分析（使用优化版本）
            color_diff = self._analyze_color_differences_optimized(img1, img2)
            
            analysis = {
                'differences_count': differences_count,
                'total_diff_area': int(total_diff_area),
                'diff_percentage': round(diff_percentage, 2),
                'color_analysis': color_diff,
                'image_dimensions': {
                    'width': img1.shape[1],
                    'height': img1.shape[0]
                }
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"分析差异失败: {e}")
            gc.collect()
            return {'error': str(e)}
    
    def _analyze_color_differences_optimized(self, img1: np.ndarray, img2: np.ndarray) -> Dict:
        """分析颜色差异，优化内存使用"""
        try:
            # 对大图像进行采样以减少计算量
            if img1.shape[0] * img1.shape[1] > 500000:  # 50万像素
                # 随机采样
                step = max(1, int(np.sqrt(img1.shape[0] * img1.shape[1] / 100000)))  # 采样到约10万像素
                sampled_img1 = img1[::step, ::step]
                sampled_img2 = img2[::step, ::step]
            else:
                sampled_img1 = img1
                sampled_img2 = img2
            
            # 计算平均颜色
            mean_color1 = np.mean(sampled_img1, axis=(0, 1))
            mean_color2 = np.mean(sampled_img2, axis=(0, 1))
            
            # 计算颜色差异
            color_diff = np.abs(mean_color1 - mean_color2)
            
            result = {
                'image1_mean_color': mean_color1.tolist(),
                'image2_mean_color': mean_color2.tolist(),
                'color_difference': color_diff.tolist(),
                'max_color_diff': float(np.max(color_diff))
            }
            
            # 释放采样图像内存（如果是复制的）
            if sampled_img1 is not img1:
                del sampled_img1, sampled_img2
                gc.collect()
            
            return result
            
        except Exception as e:
            logger.error(f"颜色分析失败: {e}")
            gc.collect()
            return {'error': str(e)}
    
    def generate_report(self, result: ComparisonResult, output_path: str) -> str:
        """生成比对报告"""
        try:
            # 转换numpy类型为Python原生类型
            def convert_numpy_types(obj):
                """递归转换numpy类型为Python原生类型"""
                if isinstance(obj, np.integer):
                    return int(obj)
                elif isinstance(obj, np.floating):
                    return float(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif isinstance(obj, dict):
                    return {key: convert_numpy_types(value) for key, value in obj.items()}
                elif isinstance(obj, list):
                    return [convert_numpy_types(item) for item in obj]
                else:
                    return obj
            
            report_data = {
                'comparison_result': {
                    'similarity_score': float(result.similarity_score),
                    'mse_score': float(result.mse_score),
                    'ssim_score': float(result.ssim_score),
                    'hash_distance': int(result.hash_distance),
                    'differences_count': int(result.differences_count),
                    'overall_rating': self._get_overall_rating(result.similarity_score)
                },
                'analysis': convert_numpy_types(result.analysis),
                'diff_image_path': result.diff_image_path,
                'recommendations': self._generate_recommendations(result)
            }
            
            # 保存JSON报告
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"比对报告生成成功: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"生成报告失败: {e}")
            raise
    
    def _get_overall_rating(self, similarity_score: float) -> str:
        """获取整体评级"""
        if similarity_score >= 0.9:
            return "优秀 (Excellent)"
        elif similarity_score >= 0.8:
            return "良好 (Good)"
        elif similarity_score >= 0.7:
            return "一般 (Fair)"
        elif similarity_score >= 0.6:
            return "较差 (Poor)"
        else:
            return "很差 (Very Poor)"
    
    def _generate_recommendations(self, result: ComparisonResult) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        if result.similarity_score < 0.8:
            recommendations.append("建议检查页面布局是否与设计稿一致")
        
        if result.analysis.get('color_analysis', {}).get('max_color_diff', 0) > 50:
            recommendations.append("建议检查颜色配置，存在较大颜色差异")
        
        if result.analysis.get('diff_percentage', 0) > 20:
            recommendations.append("建议检查页面元素位置，存在较大布局差异")
        
        if result.hash_distance > 10:
            recommendations.append("建议检查图像内容，结构差异较大")
        
        if not recommendations:
            recommendations.append("页面实现与设计稿匹配度较高，无重大问题")
        
        return recommendations
    
    def generate_html_report(self, result: ComparisonResult, output_path: str) -> str:
        """
        生成HTML视觉对比报告
        
        Args:
            result: 比对结果
            output_path: 输出路径
            
        Returns:
            HTML报告路径
        """
        try:
            # 生成HTML内容
            html_content = self._generate_html_content(result)
            
            # 写入文件
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"HTML比对报告生成成功: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"生成HTML报告失败: {e}")
            raise
    
    def _generate_html_content(self, result: ComparisonResult) -> str:
        """生成HTML内容"""
        
        # 转换差异图像路径
        diff_image_url = convert_diff_image_path(result.diff_image_path) if result.diff_image_path else ""
        
        # 生成评级样式
        rating_class = self._get_rating_class(result.similarity_score)
        
        # 生成推荐建议HTML
        recommendations = self._generate_recommendations(result)
        recommendations_html = self._generate_recommendations_html(recommendations)
        
        # 生成分析详情HTML
        analysis_html = self._generate_analysis_html(result.analysis)
        
        # HTML模板
        html_template = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>视觉对比报告</title>
    <style>
        {self._get_css_styles()}
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>🎨 视觉对比报告</h1>
            <div class="summary-cards">
                <div class="card similarity">
                    <h3>相似度</h3>
                    <div class="number {rating_class}">{result.similarity_score:.3f}</div>
                    <div class="rating">{self._get_overall_rating(result.similarity_score)}</div>
                </div>
                <div class="card mse">
                    <h3>均方误差</h3>
                    <div class="number">{result.mse_score:.2f}</div>
                </div>
                <div class="card ssim">
                    <h3>结构相似性</h3>
                    <div class="number">{result.ssim_score:.3f}</div>
                </div>
                <div class="card differences">
                    <h3>差异点数</h3>
                    <div class="number">{result.differences_count}</div>
                </div>
            </div>
        </header>
        
        <section class="diff-image-section">
            <h2>📷 差异对比图</h2>
            {f'<div class="diff-image-container"><img src="{diff_image_url}" alt="差异对比图" class="diff-image" onclick="showFullscreen(this)"></div>' if diff_image_url and ensure_file_exists(result.diff_image_path) else '<p>差异图像不可用</p>'}
        </section>
        
        <section class="analysis-section">
            <h2>📊 分析详情</h2>
            {analysis_html}
        </section>
        
        <section class="recommendations-section">
            <h2>💡 改进建议</h2>
            {recommendations_html}
        </section>
        
        <footer class="footer">
            <p>报告生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </footer>
    </div>
    
    <script>
        {self._get_javascript()}
    </script>
</body>
</html>
"""
        
        return html_template
    
    def _get_rating_class(self, similarity_score: float) -> str:
        """获取评级CSS类"""
        if similarity_score >= 0.9:
            return "excellent"
        elif similarity_score >= 0.8:
            return "good"
        elif similarity_score >= 0.7:
            return "fair"
        elif similarity_score >= 0.6:
            return "poor"
        else:
            return "very-poor"
    
    def _generate_recommendations_html(self, recommendations: List[str]) -> str:
        """生成推荐建议HTML"""
        if not recommendations:
            return "<p>无建议</p>"
        
        html_parts = ["<ul class='recommendations-list'>"]
        for recommendation in recommendations:
            html_parts.append(f"<li>{recommendation}</li>")
        html_parts.append("</ul>")
        
        return "\n".join(html_parts)
    
    def _generate_analysis_html(self, analysis: Dict) -> str:
        """生成分析详情HTML"""
        if not analysis or "error" in analysis:
            return "<p>分析数据不可用</p>"
        
        html_parts = ["<div class='analysis-grid'>"]
        
        # 差异统计
        html_parts.append(f"""
        <div class="analysis-item">
            <h3>差异统计</h3>
            <div class="stat-grid">
                <div class="stat">
                    <label>差异区域数量:</label>
                    <span>{analysis.get('differences_count', 0)}</span>
                </div>
                <div class="stat">
                    <label>差异面积:</label>
                    <span>{analysis.get('total_diff_area', 0)} 像素</span>
                </div>
                <div class="stat">
                    <label>差异百分比:</label>
                    <span>{analysis.get('diff_percentage', 0)}%</span>
                </div>
            </div>
        </div>
        """)
        
        # 图像信息
        dimensions = analysis.get('image_dimensions', {})
        html_parts.append(f"""
        <div class="analysis-item">
            <h3>图像信息</h3>
            <div class="stat-grid">
                <div class="stat">
                    <label>宽度:</label>
                    <span>{dimensions.get('width', 0)} px</span>
                </div>
                <div class="stat">
                    <label>高度:</label>
                    <span>{dimensions.get('height', 0)} px</span>
                </div>
            </div>
        </div>
        """)
        
        # 颜色分析
        color_analysis = analysis.get('color_analysis', {})
        if color_analysis and "error" not in color_analysis:
            max_color_diff = color_analysis.get('max_color_diff', 0)
            html_parts.append(f"""
            <div class="analysis-item">
                <h3>颜色分析</h3>
                <div class="stat-grid">
                    <div class="stat">
                        <label>最大颜色差异:</label>
                        <span>{max_color_diff:.2f}</span>
                    </div>
                </div>
            </div>
            """)
        
        html_parts.append("</div>")
        
        return "\n".join(html_parts)
    
    def _get_css_styles(self) -> str:
        """获取CSS样式"""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: white;
            border-radius: 10px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            text-align: center;
            margin-bottom: 30px;
            color: #2c3e50;
        }
        
        .summary-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }
        
        .card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border-left: 4px solid #ddd;
        }
        
        .card.similarity { border-left-color: #3498db; }
        .card.mse { border-left-color: #e74c3c; }
        .card.ssim { border-left-color: #27ae60; }
        .card.differences { border-left-color: #f39c12; }
        
        .card h3 {
            margin-bottom: 10px;
            color: #666;
            font-size: 14px;
        }
        
        .card .number {
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
        }
        
        .card .number.excellent { color: #27ae60; }
        .card .number.good { color: #2ecc71; }
        .card .number.fair { color: #f39c12; }
        .card .number.poor { color: #e67e22; }
        .card .number.very-poor { color: #e74c3c; }
        
        .card .rating {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }
        
        .diff-image-section,
        .analysis-section,
        .recommendations-section {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .diff-image-container {
            text-align: center;
        }
        
        .diff-image {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            cursor: pointer;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        
        .analysis-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        
        .analysis-item {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
        }
        
        .analysis-item h3 {
            margin-bottom: 15px;
            color: #2c3e50;
        }
        
        .stat-grid {
            display: grid;
            gap: 10px;
        }
        
        .stat {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .stat label {
            font-weight: bold;
            color: #666;
        }
        
        .stat span {
            color: #2c3e50;
        }
        
        .recommendations-list {
            list-style: none;
            padding: 0;
        }
        
        .recommendations-list li {
            background: #f8f9fa;
            padding: 10px 15px;
            margin-bottom: 10px;
            border-radius: 5px;
            border-left: 4px solid #3498db;
        }
        
        .footer {
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 14px;
        }
        
        h2 {
            color: #2c3e50;
            margin-bottom: 20px;
        }
        
        /* 全屏显示样式 */
        .fullscreen-modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
            cursor: pointer;
        }
        
        .fullscreen-modal img {
            max-width: 90%;
            max-height: 90%;
            border-radius: 8px;
        }
        """
    
    def _get_javascript(self) -> str:
        """获取JavaScript代码"""
        return """
        function showFullscreen(img) {
            const modal = document.createElement('div');
            modal.className = 'fullscreen-modal';
            
            const modalImg = document.createElement('img');
            modalImg.src = img.src;
            modalImg.alt = img.alt;
            
            modal.appendChild(modalImg);
            document.body.appendChild(modal);
            
            modal.onclick = () => document.body.removeChild(modal);
            
            // ESC键关闭
            const handleEsc = (e) => {
                if (e.key === 'Escape' && document.body.contains(modal)) {
                    document.body.removeChild(modal);
                    document.removeEventListener('keydown', handleEsc);
                }
            };
            document.addEventListener('keydown', handleEsc);
        }
        """ 