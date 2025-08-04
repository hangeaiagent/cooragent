"""
文件清理管理器

负责定期清理生成的项目文件和临时文件
"""

import asyncio
import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class FileCleanupManager:
    """文件清理管理器"""
    
    def __init__(self, output_dir: Path, max_age_hours: int = 24, max_files: int = 100):
        self.output_dir = Path(output_dir)
        self.max_age_hours = max_age_hours
        self.max_files = max_files
        self.output_dir.mkdir(exist_ok=True)
    
    async def cleanup_old_files(self) -> dict:
        """清理过期文件"""
        cleanup_stats = {
            "files_removed": 0,
            "dirs_removed": 0,
            "space_freed": 0,
            "errors": []
        }
        
        if not self.output_dir.exists():
            return cleanup_stats
        
        cutoff_time = datetime.now() - timedelta(hours=self.max_age_hours)
        
        try:
            for item in self.output_dir.iterdir():
                try:
                    # 检查文件/目录的修改时间
                    if item.stat().st_mtime < cutoff_time.timestamp():
                        file_size = 0
                        
                        if item.is_file():
                            file_size = item.stat().st_size
                            item.unlink()
                            cleanup_stats["files_removed"] += 1
                        elif item.is_dir():
                            file_size = self._get_directory_size(item)
                            shutil.rmtree(item)
                            cleanup_stats["dirs_removed"] += 1
                        
                        cleanup_stats["space_freed"] += file_size
                        logger.debug(f"清理过期文件: {item}")
                        
                except Exception as e:
                    error_msg = f"清理文件失败 {item}: {e}"
                    cleanup_stats["errors"].append(error_msg)
                    logger.warning(error_msg)
        
        except Exception as e:
            error_msg = f"遍历输出目录失败: {e}"
            cleanup_stats["errors"].append(error_msg)
            logger.error(error_msg)
        
        total_removed = cleanup_stats["files_removed"] + cleanup_stats["dirs_removed"]
        if total_removed > 0:
            space_mb = cleanup_stats["space_freed"] / (1024 * 1024)
            logger.info(
                f"清理完成: 删除 {total_removed} 个项目, "
                f"释放 {space_mb:.2f} MB 空间"
            )
        
        return cleanup_stats
    
    async def cleanup_by_count(self) -> dict:
        """根据文件数量清理（保持最新的N个文件）"""
        cleanup_stats = {
            "files_removed": 0,
            "space_freed": 0,
            "errors": []
        }
        
        if not self.output_dir.exists():
            return cleanup_stats
        
        try:
            # 获取所有文件并按修改时间排序
            files = []
            for item in self.output_dir.iterdir():
                if item.is_file():
                    files.append((item, item.stat().st_mtime))
            
            # 按修改时间降序排序（最新的在前）
            files.sort(key=lambda x: x[1], reverse=True)
            
            # 删除超过限制数量的旧文件
            if len(files) > self.max_files:
                files_to_remove = files[self.max_files:]
                
                for file_path, _ in files_to_remove:
                    try:
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        cleanup_stats["files_removed"] += 1
                        cleanup_stats["space_freed"] += file_size
                        logger.debug(f"清理超量文件: {file_path}")
                    except Exception as e:
                        error_msg = f"删除文件失败 {file_path}: {e}"
                        cleanup_stats["errors"].append(error_msg)
                        logger.warning(error_msg)
        
        except Exception as e:
            error_msg = f"按数量清理失败: {e}"
            cleanup_stats["errors"].append(error_msg)
            logger.error(error_msg)
        
        if cleanup_stats["files_removed"] > 0:
            space_mb = cleanup_stats["space_freed"] / (1024 * 1024)
            logger.info(
                f"按数量清理完成: 删除 {cleanup_stats['files_removed']} 个文件, "
                f"释放 {space_mb:.2f} MB 空间"
            )
        
        return cleanup_stats
    
    def _get_directory_size(self, directory: Path) -> int:
        """获取目录大小"""
        total_size = 0
        try:
            for item in directory.rglob('*'):
                if item.is_file():
                    total_size += item.stat().st_size
        except Exception as e:
            logger.warning(f"计算目录大小失败 {directory}: {e}")
        return total_size
    
    async def get_directory_stats(self) -> dict:
        """获取输出目录统计信息"""
        stats = {
            "total_files": 0,
            "total_dirs": 0,
            "total_size": 0,
            "oldest_file": None,
            "newest_file": None
        }
        
        if not self.output_dir.exists():
            return stats
        
        try:
            oldest_time = float('inf')
            newest_time = 0
            
            for item in self.output_dir.iterdir():
                mtime = item.stat().st_mtime
                
                if item.is_file():
                    stats["total_files"] += 1
                    stats["total_size"] += item.stat().st_size
                elif item.is_dir():
                    stats["total_dirs"] += 1
                    stats["total_size"] += self._get_directory_size(item)
                
                if mtime < oldest_time:
                    oldest_time = mtime
                    stats["oldest_file"] = {
                        "path": str(item),
                        "modified": datetime.fromtimestamp(mtime).isoformat()
                    }
                
                if mtime > newest_time:
                    newest_time = mtime
                    stats["newest_file"] = {
                        "path": str(item),
                        "modified": datetime.fromtimestamp(mtime).isoformat()
                    }
        
        except Exception as e:
            logger.error(f"获取目录统计失败: {e}")
        
        return stats
    
    async def start_cleanup_scheduler(self, interval_hours: int = 1):
        """启动定时清理任务"""
        logger.info(f"启动文件清理调度器，间隔: {interval_hours} 小时")
        
        while True:
            try:
                await asyncio.sleep(interval_hours * 3600)
                
                # 按时间清理
                time_stats = await self.cleanup_old_files()
                
                # 按数量清理
                count_stats = await self.cleanup_by_count()
                
                # 记录清理结果
                total_removed = (
                    time_stats["files_removed"] + time_stats["dirs_removed"] +
                    count_stats["files_removed"]
                )
                
                if total_removed > 0:
                    total_space = (time_stats["space_freed"] + count_stats["space_freed"]) / (1024 * 1024)
                    logger.info(f"定时清理完成: 删除 {total_removed} 个项目, 释放 {total_space:.2f} MB")
                
            except Exception as e:
                logger.error(f"定时清理任务出错: {e}")
    
    async def force_cleanup_all(self) -> dict:
        """强制清理所有生成的文件（危险操作）"""
        logger.warning("执行强制清理所有文件...")
        
        cleanup_stats = {
            "files_removed": 0,
            "dirs_removed": 0,
            "space_freed": 0,
            "errors": []
        }
        
        if not self.output_dir.exists():
            return cleanup_stats
        
        try:
            for item in self.output_dir.iterdir():
                try:
                    file_size = 0
                    
                    if item.is_file():
                        file_size = item.stat().st_size
                        item.unlink()
                        cleanup_stats["files_removed"] += 1
                    elif item.is_dir():
                        file_size = self._get_directory_size(item)
                        shutil.rmtree(item)
                        cleanup_stats["dirs_removed"] += 1
                    
                    cleanup_stats["space_freed"] += file_size
                    
                except Exception as e:
                    error_msg = f"强制清理失败 {item}: {e}"
                    cleanup_stats["errors"].append(error_msg)
                    logger.error(error_msg)
        
        except Exception as e:
            error_msg = f"强制清理遍历失败: {e}"
            cleanup_stats["errors"].append(error_msg)
            logger.error(error_msg)
        
        total_removed = cleanup_stats["files_removed"] + cleanup_stats["dirs_removed"]
        space_mb = cleanup_stats["space_freed"] / (1024 * 1024)
        logger.warning(f"强制清理完成: 删除 {total_removed} 个项目, 释放 {space_mb:.2f} MB 空间")
        
        return cleanup_stats


class ProjectCompressor:
    """项目压缩器"""
    
    @staticmethod
    async def compress_project(project_path: Path, compression_level: int = 6) -> Path:
        """
        压缩项目目录
        
        Args:
            project_path: 项目路径
            compression_level: 压缩级别 (0-9, 6为默认)
            
        Returns:
            压缩包路径
        """
        import zipfile
        
        zip_path = project_path.parent / f"{project_path.name}.zip"
        
        logger.info(f"开始压缩项目: {project_path} -> {zip_path}")
        
        def _compress():
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=compression_level) as zipf:
                for file_path in project_path.rglob('*'):
                    if file_path.is_file():
                        arc_name = file_path.relative_to(project_path.parent)
                        zipf.write(file_path, arc_name)
        
        # 在线程池中执行压缩操作，避免阻塞事件循环
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _compress)
        
        # 获取压缩后大小
        zip_size = zip_path.stat().st_size
        original_size = ProjectCompressor._get_directory_size(project_path)
        compression_ratio = (1 - zip_size / original_size) * 100 if original_size > 0 else 0
        
        logger.info(
            f"压缩完成: {zip_path}, "
            f"大小: {zip_size / (1024*1024):.2f} MB, "
            f"压缩率: {compression_ratio:.1f}%"
        )
        
        # 删除原目录以节省空间
        shutil.rmtree(project_path)
        logger.info(f"已删除原项目目录: {project_path}")
        
        return zip_path
    
    @staticmethod
    def _get_directory_size(directory: Path) -> int:
        """获取目录大小"""
        total_size = 0
        try:
            for file_path in directory.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except Exception as e:
            logger.warning(f"计算目录大小失败 {directory}: {e}")
        return total_size 