import os
import subprocess
import re
import platform


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


def remove_silence(input_path, output_path):
    """使用ffmpeg去除非人声部分（静音检测）"""
    try:
        # 使用ffmpeg的silenceremove滤镜去除非人声部分
        # 调整参数以避免错误
        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-af", "silenceremove=1:0:-50dB:-1:0:-50dB,areverse,silenceremove=1:0:-50dB:-1:0:-50dB,areverse",
            output_path
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        return output_path
    except subprocess.CalledProcessError as e:
        # 如果静音移除失败，就直接复制文件
        try:
            cmd = [
                "ffmpeg", "-y", "-i", input_path,
                "-c:a", "pcm_s16le", "-ar", "44100", output_path
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            return output_path
        except subprocess.CalledProcessError as e2:
            raise Exception(f"处理音频失败: {str(e2)}")


def advanced_fade_out(input_path, output_path, fade_duration=1.0):
    """应用高级淡出效果"""
    try:
        # 获取音频时长
        duration = get_audio_duration(input_path)
        # 确保淡出开始时间不会超过音频时长
        fade_start = max(0, duration - fade_duration)
        
        # 使用更复杂的音频滤镜实现高级淡出
        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-af", f"afade=t=out:st={fade_start}:d={fade_duration}:curve=exp",  # 指数衰减曲线
            "-c:a", "pcm_s16le", "-ar", "44100", output_path
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        return output_path
    except subprocess.CalledProcessError as e:
        raise Exception(f"应用高级淡出效果失败: {str(e)}")


def split_audio_with_fade(input_path, output_folder, file_base_name, segment_duration):
    """按指定时长分割音频，并对每个片段进行高级平滑结束处理"""
    try:
        # 获取音频总时长
        total_duration = get_audio_duration(input_path)
        
        # 计算可以分割的完整片段数量
        full_segments = int(total_duration // segment_duration)
        
        if full_segments == 0:
            raise Exception("音频时长不足一个分割片段")
        
        # 创建临时文件列表用于拼接
        segment_files = []
        
        # 分割音频并应用高级平滑结束处理
        for i in range(full_segments):
            start_time = i * segment_duration
            output_file = os.path.join(output_folder, f"{file_base_name}_part{i+1:03d}.wav")
            
            # 提取音频片段（不使用-t参数，避免截断问题）
            cmd = [
                "ffmpeg", "-y", "-ss", str(start_time), "-i", input_path,
                "-t", str(segment_duration),
                "-c:a", "pcm_s16le", "-ar", "44100", output_file
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            
            # 应用高级淡出效果
            temp_file = output_file.replace(".wav", "_temp.wav")
            os.rename(output_file, temp_file)
            advanced_fade_out(temp_file, output_file, 1.0)  # 1秒高级淡出
            
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


def process_audio_file(input_path, output_folder, file_base_name, segment_duration):
    """处理单个音频文件的完整流程"""
    try:
        # 步骤1: 创建临时文件用于去除非人声部分
        temp_folder = os.path.join(output_folder, "temp")
        os.makedirs(temp_folder, exist_ok=True)
        cleaned_audio = os.path.join(temp_folder, f"{file_base_name}_clean.wav")
        
        # 步骤2: 去除非人声部分
        remove_silence(input_path, cleaned_audio)
        
        # 步骤3: 分割音频并应用高级平滑结束处理
        segments = split_audio_with_fade(cleaned_audio, output_folder, file_base_name, segment_duration)
        
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