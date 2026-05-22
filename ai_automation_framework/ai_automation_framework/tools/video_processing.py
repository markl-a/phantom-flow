"""
視頻處理工具
Video Processing Tools

提供視頻剪輯、轉碼、提取幀、添加字幕等功能。
"""

import os
import subprocess
import logging
from typing import Optional, List, Tuple, Dict, Any
from pathlib import Path

# Set up logger for this module
logger = logging.getLogger(__name__)

try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False

try:
    from moviepy.editor import VideoFileClip, concatenate_videoclips, TextClip, CompositeVideoClip
    HAS_MOVIEPY = True
except ImportError:
    HAS_MOVIEPY = False


class VideoProcessor:
    """視頻處理器"""

    def __init__(self):
        """初始化視頻處理器"""
        if not HAS_OPENCV:
            logger.warning("OpenCV 未安裝，某些功能可能不可用")
        if not HAS_MOVIEPY:
            logger.warning("MoviePy 未安裝，某些功能可能不可用")

    def extract_frames(
        self,
        video_path: str,
        output_dir: str,
        interval: int = 30,
        max_frames: Optional[int] = None
    ) -> List[str]:
        """
        從視頻中提取幀

        Args:
            video_path: 視頻文件路徑
            output_dir: 輸出目錄
            interval: 提取間隔（幀數）
            max_frames: 最大提取幀數

        Returns:
            提取的幀文件路徑列表
        """
        if not HAS_OPENCV:
            raise ImportError("需要安裝 OpenCV: pip install opencv-python")

        # Validate video file exists
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        os.makedirs(output_dir, exist_ok=True)

        cap = cv2.VideoCapture(video_path)

        # Validate video capture was successful
        if not cap.isOpened():
            raise RuntimeError(f"Failed to open video file: {video_path}")

        try:
            frame_count = 0
            saved_count = 0
            saved_frames = []

            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_count % interval == 0:
                    output_path = os.path.join(output_dir, f"frame_{saved_count:04d}.jpg")
                    cv2.imwrite(output_path, frame)
                    saved_frames.append(output_path)
                    saved_count += 1

                    if max_frames and saved_count >= max_frames:
                        break

                frame_count += 1

            return saved_frames
        finally:
            cap.release()

    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """
        獲取視頻信息

        Args:
            video_path: 視頻文件路徑

        Returns:
            視頻信息字典
        """
        if not HAS_OPENCV:
            raise ImportError("需要安裝 OpenCV: pip install opencv-python")

        # Validate video file exists
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        cap = cv2.VideoCapture(video_path)

        # Validate video capture was successful
        if not cap.isOpened():
            raise RuntimeError(f"Failed to open video file: {video_path}")

        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)

            info = {
                "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                "fps": fps,
                "frame_count": int(frame_count),
                "duration": int(frame_count / fps) if fps > 0 else 0,
            }

            return info
        finally:
            cap.release()

    def trim_video(
        self,
        video_path: str,
        output_path: str,
        start_time: float,
        end_time: float
    ) -> str:
        """
        剪輯視頻

        Args:
            video_path: 輸入視頻路徑
            output_path: 輸出視頻路徑
            start_time: 開始時間（秒）
            end_time: 結束時間（秒）

        Returns:
            輸出文件路徑
        """
        if not HAS_MOVIEPY:
            raise ImportError("需要安裝 MoviePy: pip install moviepy")

        clip = VideoFileClip(video_path).subclip(start_time, end_time)
        clip.write_videofile(output_path)
        clip.close()

        return output_path

    def concatenate_videos(
        self,
        video_paths: List[str],
        output_path: str
    ) -> str:
        """
        拼接多個視頻

        Args:
            video_paths: 視頻文件路徑列表
            output_path: 輸出視頻路徑

        Returns:
            輸出文件路徑
        """
        if not HAS_MOVIEPY:
            raise ImportError("需要安裝 MoviePy: pip install moviepy")

        clips = [VideoFileClip(path) for path in video_paths]
        final_clip = concatenate_videoclips(clips)
        final_clip.write_videofile(output_path)

        for clip in clips:
            clip.close()
        final_clip.close()

        return output_path

    def add_subtitles(
        self,
        video_path: str,
        output_path: str,
        subtitles: List[Tuple[float, float, str]],
        font_size: int = 24,
        color: str = 'white'
    ) -> str:
        """
        添加字幕到視頻

        Args:
            video_path: 輸入視頻路徑
            output_path: 輸出視頻路徑
            subtitles: 字幕列表 [(開始時間, 結束時間, 文本), ...]
            font_size: 字體大小
            color: 字體顏色

        Returns:
            輸出文件路徑
        """
        if not HAS_MOVIEPY:
            raise ImportError("需要安裝 MoviePy: pip install moviepy")

        video = VideoFileClip(video_path)
        subtitle_clips = []

        for start, end, text in subtitles:
            txt_clip = (TextClip(text, fontsize=font_size, color=color)
                       .set_position(('center', 'bottom'))
                       .set_start(start)
                       .set_duration(end - start))
            subtitle_clips.append(txt_clip)

        final_video = CompositeVideoClip([video] + subtitle_clips)
        final_video.write_videofile(output_path)

        video.close()
        final_video.close()

        return output_path

    def convert_format(
        self,
        input_path: str,
        output_path: str,
        codec: str = 'libx264',
        audio_codec: str = 'aac'
    ) -> str:
        """
        轉換視頻格式

        Args:
            input_path: 輸入視頻路徑
            output_path: 輸出視頻路徑
            codec: 視頻編碼器
            audio_codec: 音頻編碼器

        Returns:
            輸出文件路徑
        """
        # Validate codec parameters
        if not codec or not isinstance(codec, str) or not codec.strip():
            raise ValueError(f"Invalid codec parameter: {codec}")
        if not audio_codec or not isinstance(audio_codec, str) or not audio_codec.strip():
            raise ValueError(f"Invalid audio_codec parameter: {audio_codec}")

        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-c:v', codec,
            '-c:a', audio_codec,
            output_path
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=300)
            return output_path
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"視頻轉換失敗: {e.stderr.decode()}")
        except subprocess.TimeoutExpired:
            raise TimeoutError("視頻轉換超時 (300秒)")

    def resize_video(
        self,
        input_path: str,
        output_path: str,
        width: int,
        height: int
    ) -> str:
        """
        調整視頻大小

        Args:
            input_path: 輸入視頻路徑
            output_path: 輸出視頻路徑
            width: 新寬度
            height: 新高度

        Returns:
            輸出文件路徑
        """
        if not HAS_MOVIEPY:
            raise ImportError("需要安裝 MoviePy: pip install moviepy")

        clip = VideoFileClip(input_path)
        resized = clip.resize((width, height))
        resized.write_videofile(output_path)

        clip.close()
        resized.close()

        return output_path

    def extract_audio(
        self,
        video_path: str,
        output_path: str
    ) -> str:
        """
        從視頻中提取音頻

        Args:
            video_path: 視頻文件路徑
            output_path: 輸出音頻路徑

        Returns:
            輸出文件路徑
        """
        if not HAS_MOVIEPY:
            raise ImportError("需要安裝 MoviePy: pip install moviepy")

        clip = VideoFileClip(video_path)
        clip.audio.write_audiofile(output_path)
        clip.close()

        return output_path

    def create_thumbnail(
        self,
        video_path: str,
        output_path: str,
        time: float = 1.0
    ) -> str:
        """
        創建視頻縮略圖

        Args:
            video_path: 視頻文件路徑
            output_path: 輸出圖片路徑
            time: 截取時間點（秒）

        Returns:
            輸出文件路徑
        """
        if not HAS_MOVIEPY:
            raise ImportError("需要安裝 MoviePy: pip install moviepy")

        clip = VideoFileClip(video_path)
        clip.save_frame(output_path, t=time)
        clip.close()

        return output_path


__all__ = ['VideoProcessor']
