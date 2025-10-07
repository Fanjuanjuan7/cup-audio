import os
import subprocess
import re
import platform
import json


# 支持的音频格式
SUPPORTED_FORMATS = {
    "WAV": ".wav",
    "MP3": ".mp3",
    "FLAC": ".flac",
    "AAC": ".aac",
    "OGG": ".ogg",
    "M4A": ".m4a"
}


def get_audio_duration(file_path):
    """获取音频文件的总时长（秒）"""
    try:
        # 使用 ffprobe 获取音频时长
        cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError) as e:
        raise Exception(f"无法获取音频时长: {str(e)}")


def get_audio_channels(file_path):
    """获取音频文件的声道数"""
    try:
        # 使用 ffprobe 获取音频声道数
        cmd = [
            "ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", 
            "stream=channels", "-of", "default=noprint_wrappers=1:nokey=1", file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return int(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError) as e:
        print(f"无法获取音频声道数，假设为单声道: {str(e)}")
        return 1


def remove_silence_advanced(input_path, output_path):
    """使用专业方法去除非人声部分（静音检测）"""
    try:
        # 首先检查音频是否为立体声
        channels = get_audio_channels(input_path)
        
        if channels == 1:
            # 单声道音频 - 直接应用滤镜链
            cmd = [
                "ffmpeg", "-y", "-i", input_path,
                "-af", 
                # 信号增强：突出人声频段特征(200Hz-3kHz)
                "highpass=f=200,"  # 去除200Hz以下的低频噪声
                "lowpass=f=3000,"  # 去除3000Hz以上的高频噪声
                "acontrast=75,"  # 提升人声频段的信号对比度
                # 降噪提纯：去除残留非人声杂音
                "afftdn=nr=30",  # 频域降噪，nr为降噪强度
                "-c:a", "pcm_s16le", "-ar", "44100",
                output_path
            ]
        else:
            # 立体声或多声道音频 - 使用声道优化
            cmd = [
                "ffmpeg", "-y", "-i", input_path,
                "-af", 
                # 声道优化：将立体声转为单声道并混合人声信号
                "pan=mono|c0=0.5*c0+0.5*c1,"  # 立体声转单声道并混合左右声道
                # 信号增强：突出人声频段特征(200Hz-3kHz)
                "highpass=f=200,"  # 去除200Hz以下的低频噪声
                "lowpass=f=3000,"  # 去除3000Hz以上的高频噪声
                "acontrast=75,"  # 提升人声频段的信号对比度
                # 降噪提纯：去除残留非人声杂音
                "afftdn=nr=30",  # 频域降噪，nr为降噪强度
                "-c:a", "pcm_s16le", "-ar", "44100",
                output_path
            ]
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"去除非人声部分失败，尝试备用方案: {e}")
        # 如果高级处理失败，尝试使用标准参数
        try:
            channels = get_audio_channels(input_path)  # 重新获取声道数
            
            if channels == 1:
                cmd = [
                    "ffmpeg", "-y", "-i", input_path,
                    "-af", 
                    "highpass=f=150,"  # 轻度声道优化
                    "lowpass=f=3500,"  # 轻度频段优化
                    "acontrast=60,"  # 轻度信号增强
                    "afftdn=nr=20",  # 轻度降噪
                    "-c:a", "pcm_s16le", "-ar", "44100",
                    output_path
                ]
            else:
                cmd = [
                    "ffmpeg", "-y", "-i", input_path,
                    "-af", 
                    "pan=mono|c0=0.5*c0+0.5*c1,"  # 声道优化
                    "highpass=f=150,"  # 轻度声道优化
                    "lowpass=f=3500,"  # 轻度频段优化
                    "acontrast=60,"  # 轻度信号增强
                    "afftdn=nr=20",  # 轻度降噪
                    "-c:a", "pcm_s16le", "-ar", "44100",
                    output_path
                ]
            subprocess.run(cmd, check=True, capture_output=True)
            return output_path
        except subprocess.CalledProcessError as e2:
            print(f"备用方案也失败，直接复制文件: {e2}")
            # 如果仍然失败，就直接复制文件
            try:
                cmd = [
                    "ffmpeg", "-y", "-i", input_path,
                    "-c:a", "pcm_s16le", "-ar", "44100",
                    output_path
                ]
                subprocess.run(cmd, check=True, capture_output=True)
                return output_path
            except subprocess.CalledProcessError as e3:
                raise Exception(f"处理音频失败: {str(e3)}")


def sophisticated_end_effect(input_path, output_path, transition_sound_path=None):
    """应用高级的过渡音效和淡出效果"""
    try:
        # 按照您提供的专业逻辑实现过渡音效
        # 步骤1: 音效与片段的同步对齐
        # 步骤2: 音频层混合 - 叠加过渡音效
        # 步骤3: 结尾淡出 - 弱化中断感
        
        if transition_sound_path and os.path.exists(transition_sound_path):
            # 如果提供了过渡音效文件，则使用音效混合
            # 获取音频时长
            duration = get_audio_duration(input_path)
            # 预留0.2秒过渡时间
            transition_start = max(0, duration - 0.2)
            
            # 使用复合命令实现音效混合和淡出
            cmd = [
                "ffmpeg", "-y",
                "-i", input_path,
                "-i", transition_sound_path,
                "-filter_complex", 
                f"[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=0.1,"  # 音频混合
                f"afade=t=out:st={transition_start}:d=0.2",  # 结尾淡出
                "-c:a", "pcm_s16le", "-ar", "44100",
                output_path
            ]
        else:
            # 如果没有过渡音效文件，则只使用淡出效果
            duration = get_audio_duration(input_path)
            fade_start = max(0, duration - 0.1)  # 100毫秒前开始淡出
            
            cmd = [
                "ffmpeg", "-y", "-i", input_path,
                "-af", f"afade=t=out:st={fade_start}:d=0.1",  # 渐进式淡出
                "-c:a", "pcm_s16le", "-ar", "44100",
                output_path
            ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"应用过渡音效失败，使用简化版本: {e}")
        # 如果高级效果失败，回退到渐进式淡出
        try:
            duration = get_audio_duration(input_path)
            fade_start = max(0, duration - 0.1)  # 100毫秒前开始淡出
            
            cmd = [
                "ffmpeg", "-y", "-i", input_path,
                "-af", f"afade=t=out:st={fade_start}:d=0.1",  # 渐进式淡出
                "-c:a", "pcm_s16le", "-ar", "44100",
                output_path
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            return output_path
        except subprocess.CalledProcessError as e2:
            print(f"简化版本也失败，使用最基本的淡出: {e2}")
            # 最后的回退方案
            try:
                duration = get_audio_duration(input_path)
                fade_start = max(0, duration - 0.05)  # 50毫秒前开始淡出
                
                cmd = [
                    "ffmpeg", "-y", "-i", input_path,
                    "-af", f"afade=t=out:st={fade_start}:d=0.05",
                    "-c:a", "pcm_s16le", "-ar", "44100",
                    output_path
                ]
                subprocess.run(cmd, check=True, capture_output=True)
                return output_path
            except subprocess.CalledProcessError as e3:
                raise Exception(f"应用结束效果失败: {str(e3)}")


def get_ffmpeg_codec_params(output_format):
    """根据输出格式获取FFmpeg编码参数"""
    codec_params = {
        "WAV": ["-c:a", "pcm_s16le"],
        "MP3": ["-c:a", "libmp3lame", "-b:a", "192k"],
        "FLAC": ["-c:a", "flac"],
        "AAC": ["-c:a", "aac", "-b:a", "192k"],
        "OGG": ["-c:a", "libvorbis", "-b:a", "192k"],
        "M4A": ["-c:a", "aac", "-b:a", "192k"]
    }
    return codec_params.get(output_format, ["-c:a", "pcm_s16le"])


def split_audio_with_fade(input_path, output_folder, file_base_name, segment_duration, output_format="WAV", transition_sound_path=None):
    """按指定时长分割音频，并对每个片段进行高级平滑结束处理"""
    try:
        # 获取音频总时长
        total_duration = get_audio_duration(input_path)
        
        # 计算可以分割的完整片段数量
        full_segments = int(total_duration // segment_duration)
        
        if full_segments == 0:
            raise Exception("音频时长不足一个分割片段")
        
        # 获取文件扩展名
        file_extension = SUPPORTED_FORMATS.get(output_format, ".wav")
        
        # 创建临时文件列表用于拼接
        segment_files = []
        
        # 分割音频并应用高级平滑结束处理
        for i in range(full_segments):
            start_time = i * segment_duration
            output_file = os.path.join(output_folder, f"{file_base_name}_part{i+1:03d}{file_extension}")
            
            # 提取音频片段（不使用-t参数，避免截断问题）
            cmd = [
                "ffmpeg", "-y", "-ss", str(start_time), "-i", input_path,
                "-t", str(segment_duration)
            ]
            
            # 添加编码参数
            cmd.extend(get_ffmpeg_codec_params(output_format))
            cmd.append(output_file)
            
            subprocess.run(cmd, check=True, capture_output=True)
            
            # 应用高级"自然结束"效果（仅对WAV格式，其他格式直接使用）
            if output_format == "WAV":
                temp_file = output_file.replace(".wav", "_temp.wav")
                os.rename(output_file, temp_file)
                sophisticated_end_effect(temp_file, output_file, transition_sound_path)  # 自然结束效果
                
                # 删除临时文件
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            
            segment_files.append(output_file)
        
        return segment_files
    
    except subprocess.CalledProcessError as e:
        raise Exception(f"分割音频失败: {str(e)}")
    except Exception as e:
        raise Exception(f"处理音频时出错: {str(e)}")


def crossfade_segments(segments, output_folder, file_base_name, crossfade_duration=0.5):
    """对相邻片段应用交叉淡入淡出效果（用于更好的连续性）"""
    try:
        if len(segments) < 2:
            return segments
        
        crossfaded_segments = []
        
        # 处理第一个片段（只做淡入）
        first_segment = segments[0]
        first_output = os.path.join(output_folder, f"{file_base_name}_crossfade_001.wav")
        
        cmd = [
            "ffmpeg", "-y", "-i", first_segment,
            "-af", f"afade=t=in:st=0:d={crossfade_duration}",
            "-c:a", "pcm_s16le", "-ar", "44100", first_output
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        crossfaded_segments.append(first_output)
        
        # 处理中间片段（淡入+淡出）
        for i in range(1, len(segments) - 1):
            segment = segments[i]
            output_file = os.path.join(output_folder, f"{file_base_name}_crossfade_{i+1:03d}.wav")
            
            cmd = [
                "ffmpeg", "-y", "-i", segment,
                "-af", f"afade=t=in:st=0:d={crossfade_duration},afade=t=out:st={get_audio_duration(segment)-crossfade_duration}:d={crossfade_duration}",
                "-c:a", "pcm_s16le", "-ar", "44100", output_file
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            crossfaded_segments.append(output_file)
        
        # 处理最后一个片段（只做淡出）
        last_segment = segments[-1]
        last_output = os.path.join(output_folder, f"{file_base_name}_crossfade_{len(segments):03d}.wav")
        
        # 获取最后一个片段的时长
        last_duration = get_audio_duration(last_segment)
        
        cmd = [
            "ffmpeg", "-y", "-i", last_segment,
            "-af", f"afade=t=out:st={last_duration-crossfade_duration}:d={crossfade_duration}",
            "-c:a", "pcm_s16le", "-ar", "44100", last_output
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        crossfaded_segments.append(last_output)
        
        return crossfaded_segments
    
    except subprocess.CalledProcessError as e:
        raise Exception(f"应用交叉淡入淡出效果失败: {str(e)}")


def process_audio_file(input_path, output_folder, file_base_name, segment_duration, output_format="WAV", transition_sound_path=None):
    """处理单个音频文件的完整流程"""
    try:
        # 步骤1: 创建临时文件用于去除非人声部分
        temp_folder = os.path.join(output_folder, "temp")
        os.makedirs(temp_folder, exist_ok=True)
        cleaned_audio = os.path.join(temp_folder, f"{file_base_name}_clean.wav")
        
        # 步骤2: 使用高级方法去除非人声部分
        remove_silence_advanced(input_path, cleaned_audio)
        
        # 步骤3: 分割音频并应用高级平滑结束处理
        segments = split_audio_with_fade(cleaned_audio, output_folder, file_base_name, segment_duration, output_format, transition_sound_path)
        
        # 步骤4: 应用交叉淡入淡出效果（可选，提升连续性）
        # crossfaded_segments = crossfade_segments(segments, output_folder, f"{file_base_name}_cf", 0.5)
        
        # 步骤5: 清理临时文件
        if os.path.exists(cleaned_audio):
            os.remove(cleaned_audio)
        
        # 清理临时目录
        if os.path.exists(temp_folder):
            import shutil
            shutil.rmtree(temp_folder, ignore_errors=True)
        
        return segments
    
    except Exception as e:
        # 清理可能存在的临时文件
        temp_folder = os.path.join(output_folder, "temp")
        if os.path.exists(temp_folder):
            import shutil
            shutil.rmtree(temp_folder, ignore_errors=True)
        raise e


def check_ffmpeg_available():
    """检查ffmpeg是否可用"""
    try:
        # 在Windows上可能需要指定完整路径
        system = platform.system()
        if system == "Windows":
            # 尝试在常见位置查找ffmpeg
            common_paths = [
                "ffmpeg",
                "C:\\ffmpeg\\bin\\ffmpeg.exe",
                "C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe",
                "C:\\Program Files (x86)\\ffmpeg\\bin\\ffmpeg.exe"
            ]
            
            for path in common_paths:
                try:
                    subprocess.run([path, "-version"], 
                                  stdout=subprocess.DEVNULL, 
                                  stderr=subprocess.DEVNULL,
                                  check=True)
                    return True
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue
            return False
        else:
            subprocess.run(["ffmpeg", "-version"], 
                          stdout=subprocess.DEVNULL, 
                          stderr=subprocess.DEVNULL,
                          check=True)
            return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False