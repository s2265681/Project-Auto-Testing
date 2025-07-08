"""
视觉比对器模块
Visual Comparator Module
"""
import os
import time
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imagehash
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import json

from ..utils.logger import get_logger

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
    
    def __init__(self):
        """初始化比对器"""
        pass
    
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
            
            # 调整图片尺寸到相同大小
            img1_resized, img2_resized = self._resize_images(img1, img2)
            
            # 计算各种相似度指标
            similarity_score = self._calculate_similarity(img1_resized, img2_resized)
            mse_score = self._calculate_mse(img1_resized, img2_resized)
            ssim_score = self._calculate_ssim(img1_resized, img2_resized)
            hash_distance = self._calculate_hash_distance(image1_path, image2_path)
            
            # 生成差异图像
            diff_image_path = self._generate_diff_image(
                img1_resized, img2_resized, output_dir
            )
            
            # 分析差异
            analysis = self._analyze_differences(img1_resized, img2_resized)
            
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
            return result
            
        except Exception as e:
            logger.error(f"图片比较失败: {e}")
            raise
    
    def _resize_images(self, img1: np.ndarray, img2: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """调整图片尺寸到相同大小"""
        h1, w1 = img1.shape[:2]
        h2, w2 = img2.shape[:2]
        
        # 使用较小的尺寸
        target_h = min(h1, h2)
        target_w = min(w1, w2)
        
        img1_resized = cv2.resize(img1, (target_w, target_h))
        img2_resized = cv2.resize(img2, (target_w, target_h))
        
        return img1_resized, img2_resized
    
    def _calculate_similarity(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """计算基础相似度（基于直方图）"""
        # 转换为HSV颜色空间
        hsv1 = cv2.cvtColor(img1, cv2.COLOR_BGR2HSV)
        hsv2 = cv2.cvtColor(img2, cv2.COLOR_BGR2HSV)
        
        # 计算直方图
        hist1 = cv2.calcHist([hsv1], [0, 1, 2], None, [50, 60, 60], [0, 180, 0, 256, 0, 256])
        hist2 = cv2.calcHist([hsv2], [0, 1, 2], None, [50, 60, 60], [0, 180, 0, 256, 0, 256])
        
        # 计算相关性
        correlation = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
        return max(0, correlation)
    
    def _calculate_mse(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """计算均方误差"""
        mse = np.mean((img1.astype(float) - img2.astype(float)) ** 2)
        return mse
    
    def _calculate_ssim(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """计算结构相似性指数"""
        # 转换为灰度图
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        
        # 计算SSIM
        from skimage.metrics import structural_similarity
        ssim = structural_similarity(gray1, gray2)
        return ssim
    
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
        """分析图像差异"""
        try:
            # 转换为灰度图
            gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
            
            # 计算差异
            diff = cv2.absdiff(gray1, gray2)
            
            # 应用阈值得到二值化差异图
            _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
            
            # 查找轮廓（差异区域）
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # 分析差异区域
            differences_count = len(contours)
            total_diff_area = sum(cv2.contourArea(contour) for contour in contours)
            total_area = gray1.shape[0] * gray1.shape[1]
            diff_percentage = (total_diff_area / total_area) * 100
            
            # 颜色差异分析
            color_diff = self._analyze_color_differences(img1, img2)
            
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
            return {'error': str(e)}
    
    def _analyze_color_differences(self, img1: np.ndarray, img2: np.ndarray) -> Dict:
        """分析颜色差异"""
        try:
            # 计算平均颜色
            mean_color1 = np.mean(img1, axis=(0, 1))
            mean_color2 = np.mean(img2, axis=(0, 1))
            
            # 计算颜色差异
            color_diff = np.abs(mean_color1 - mean_color2)
            
            return {
                'image1_mean_color': mean_color1.tolist(),
                'image2_mean_color': mean_color2.tolist(),
                'color_difference': color_diff.tolist(),
                'max_color_diff': float(np.max(color_diff))
            }
            
        except Exception as e:
            logger.error(f"颜色分析失败: {e}")
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