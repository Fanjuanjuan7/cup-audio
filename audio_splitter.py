import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import threading
import webbrowser
import platform
from audio_processor import process_audio_file, check_ffmpeg_available, SUPPORTED_FORMATS
from config_manager import ConfigManager


class AudioSplitterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("音频分割工具")
        
        # 初始化配置管理器
        self.config_manager = ConfigManager()
        
        # 加载配置
        self.load_config()
        
        # 音频文件夹路径
        self.audio_folder = tk.StringVar(value=self.config_manager.get("audio_folder", ""))
        # 分割时长(秒)
        self.segment_duration = tk.IntVar(value=self.config_manager.get("segment_duration", 30))
        # 高级处理选项
        self.advanced_processing = tk.BooleanVar(value=self.config_manager.get("advanced_processing", True))
        # 输出文件夹路径
        self.output_folder = tk.StringVar(value=self.config_manager.get("output_folder", ""))
        # 输出格式
        self.output_format = tk.StringVar(value=self.config_manager.get("output_format", "WAV"))
        # 过渡音效文件路径
        self.transition_sound = tk.StringVar(value=self.config_manager.get("transition_sound", ""))
        # 进度变量
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar(value="就绪")
        
        self.create_widgets()
        
        # 绑定窗口关闭事件以保存配置
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def load_config(self):
        """加载窗口配置"""
        geometry = self.config_manager.get("window_geometry", "650x520")
        self.root.geometry(geometry)
    
    def save_config(self):
        """保存当前配置"""
        config_updates = {
            "audio_folder": self.audio_folder.get(),
            "segment_duration": self.segment_duration.get(),
            "advanced_processing": self.advanced_processing.get(),
            "output_folder": self.output_folder.get(),
            "output_format": self.output_format.get(),
            "transition_sound": self.transition_sound.get(),
            "window_geometry": self.root.geometry()
        }
        self.config_manager.update(config_updates)
        self.config_manager.save_config()
    
    def on_closing(self):
        """窗口关闭时保存配置"""
        self.save_config()
        self.root.destroy()
    
    def create_widgets(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # 选择音频文件夹
        ttk.Label(main_frame, text="音频文件夹:").grid(row=0, column=0, sticky="w", pady=5)
        folder_frame = ttk.Frame(main_frame)
        folder_frame.grid(row=0, column=1, columnspan=2, sticky="ew", pady=5)
        folder_frame.columnconfigure(0, weight=1)
        
        ttk.Entry(folder_frame, textvariable=self.audio_folder, state="readonly").grid(row=0, column=0, sticky="ew", padx=(0, 5))
        ttk.Button(folder_frame, text="浏览", command=self.browse_folder).grid(row=0, column=1)
        
        # 分割时长设置
        ttk.Label(main_frame, text="分割时长(秒):").grid(row=1, column=0, sticky="w", pady=5)
        duration_frame = ttk.Frame(main_frame)
        duration_frame.grid(row=1, column=1, sticky="w", pady=5)
        
        ttk.Entry(duration_frame, textvariable=self.segment_duration, width=10).grid(row=0, column=0, padx=(0, 5))
        ttk.Label(duration_frame, text="秒").grid(row=0, column=1)
        
        # 输出格式选择
        ttk.Label(main_frame, text="输出格式:").grid(row=2, column=0, sticky="w", pady=5)
        format_combo = ttk.Combobox(main_frame, textvariable=self.output_format, 
                                   values=list(SUPPORTED_FORMATS.keys()), state="readonly", width=15)
        format_combo.grid(row=2, column=1, sticky="w", pady=5)
        
        # 过渡音效文件选择
        ttk.Label(main_frame, text="过渡音效:").grid(row=3, column=0, sticky="w", pady=5)
        transition_frame = ttk.Frame(main_frame)
        transition_frame.grid(row=3, column=1, columnspan=2, sticky="ew", pady=5)
        transition_frame.columnconfigure(0, weight=1)
        
        ttk.Entry(transition_frame, textvariable=self.transition_sound, state="readonly").grid(row=0, column=0, sticky="ew", padx=(0, 5))
        ttk.Button(transition_frame, text="浏览", command=self.browse_transition_sound).grid(row=0, column=1)
        
        # 高级处理选项
        ttk.Checkbutton(main_frame, text="启用高级音频处理", variable=self.advanced_processing).grid(row=4, column=0, columnspan=3, sticky="w", pady=5)
        
        # 处理说明
        ttk.Label(main_frame, text="高级处理包括:", foreground="gray").grid(row=5, column=0, columnspan=3, sticky="w")
        ttk.Label(main_frame, text="- 智能去除非人声部分", foreground="gray").grid(row=6, column=0, columnspan=3, sticky="w")
        ttk.Label(main_frame, text="- 高级淡出和过渡音效", foreground="gray").grid(row=7, column=0, columnspan=3, sticky="w")
        ttk.Label(main_frame, text="- 平滑的音频片段结束", foreground="gray").grid(row=8, column=0, columnspan=3, sticky="w")
        
        # 输出路径显示
        ttk.Label(main_frame, text="输出路径:").grid(row=9, column=0, sticky="w", pady=(10, 5))
        output_frame = ttk.Frame(main_frame)
        output_frame.grid(row=9, column=1, columnspan=2, sticky="ew", pady=(10, 5))
        output_frame.columnconfigure(0, weight=1)
        
        ttk.Entry(output_frame, textvariable=self.output_folder, state="readonly").grid(row=0, column=0, sticky="ew", padx=(0, 5))
        ttk.Button(output_frame, text="浏览", command=self.browse_output_folder).grid(row=0, column=1, padx=(0, 5))
        ttk.Button(output_frame, text="打开文件夹", command=self.open_output_folder).grid(row=0, column=2)
        
        # 开始处理按钮
        self.start_button = ttk.Button(main_frame, text="开始处理", command=self.start_processing)
        self.start_button.grid(row=10, column=0, columnspan=3, pady=20)
        
        # 进度条
        ttk.Label(main_frame, text="处理进度:").grid(row=11, column=0, sticky="w", pady=5)
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=11, column=1, columnspan=2, sticky="ew", pady=5)
        
        # 状态标签
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var)
        self.status_label.grid(row=12, column=0, columnspan=3, sticky="ew", pady=5)
        
        # 日志文本框
        ttk.Label(main_frame, text="处理日志:").grid(row=13, column=0, sticky="wn", pady=5)
        self.log_text = tk.Text(main_frame, height=12, state="disabled")
        log_scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.grid(row=13, column=1, columnspan=1, sticky="nsew", pady=5)
        log_scrollbar.grid(row=13, column=2, sticky="ns", pady=5)
        
        # 配置行权重
        main_frame.rowconfigure(13, weight=1)
    
    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.audio_folder.set(folder_selected)
            # 如果没有设置输出文件夹，则设置默认输出文件夹路径
            if not self.output_folder.get():
                output_folder = os.path.join(folder_selected, "split_audio")
                self.output_folder.set(output_folder)
            # 保存配置
            self.save_config()
    
    def browse_transition_sound(self):
        """浏览并选择过渡音效文件"""
        file_selected = filedialog.askopenfilename(
            title="选择过渡音效文件",
            filetypes=[("音频文件", "*.wav *.mp3 *.flac *.aac *.ogg *.m4a"), ("所有文件", "*.*")]
        )
        if file_selected:
            self.transition_sound.set(file_selected)
            # 保存配置
            self.save_config()
    
    def browse_output_folder(self):
        """浏览并选择输出文件夹"""
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.output_folder.set(folder_selected)
            # 保存配置
            self.save_config()
    
    def open_output_folder(self):
        """打开输出文件夹"""
        output_folder = self.output_folder.get()
        if output_folder and os.path.exists(output_folder):
            # 跨平台打开文件夹
            try:
                system = platform.system()
                if system == "Windows":
                    os.startfile(output_folder)
                elif system == "Darwin":  # macOS
                    subprocess.run(["open", output_folder], check=True)
                elif system == "Linux":
                    subprocess.run(["xdg-open", output_folder], check=True)
                else:
                    # 其他系统使用webbrowser模块
                    webbrowser.open(f"file://{output_folder}")
            except Exception as e:
                messagebox.showerror("错误", f"无法打开文件夹: {str(e)}")
        else:
            messagebox.showwarning("警告", "输出文件夹不存在")
    
    def log_message(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.config(state="disabled")
        self.log_text.see(tk.END)
    
    def start_processing(self):
        if not self.audio_folder.get():
            messagebox.showerror("错误", "请选择音频文件夹")
            return
        
        if self.segment_duration.get() <= 0:
            messagebox.showerror("错误", "分割时长必须大于0")
            return
        
        # 检查ffmpeg是否可用
        if not check_ffmpeg_available():
            messagebox.showerror("错误", "未找到 ffmpeg，请确保已安装并添加到系统路径")
            return
        
        # 保存配置
        self.save_config()
        
        # 在新线程中处理，避免阻塞UI
        self.start_button.config(state="disabled")
        processing_thread = threading.Thread(target=self.process_audio)
        processing_thread.daemon = True
        processing_thread.start()
    
    def process_audio(self):
        try:
            folder_path = self.audio_folder.get()
            duration = self.segment_duration.get()
            output_format = self.output_format.get()
            transition_sound = self.transition_sound.get() if self.transition_sound.get() else None
            
            self.status_var.set("正在扫描音频文件...")
            self.root.update()
            
            # 获取所有音频文件
            audio_files = []
            for file in os.listdir(folder_path):
                if file.lower().endswith(('.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a')):
                    audio_files.append(file)
            
            if not audio_files:
                self.log_message("未找到音频文件")
                self.status_var.set("未找到音频文件")
                self.start_button.config(state="normal")
                return
            
            self.log_message(f"找到 {len(audio_files)} 个音频文件")
            total_files = len(audio_files)
            
            # 获取输出文件夹路径
            output_folder = self.output_folder.get()
            if not output_folder:
                output_folder = os.path.join(folder_path, "split_audio")
            
            # 创建输出文件夹
            os.makedirs(output_folder, exist_ok=True)
            
            # 处理每个音频文件
            for i, filename in enumerate(audio_files):
                self.status_var.set(f"正在处理: {filename} ({i+1}/{total_files})")
                self.progress_var.set((i / total_files) * 100)
                self.root.update()
                
                input_path = os.path.join(folder_path, filename)
                file_base_name = os.path.splitext(filename)[0]
                
                try:
                    # 处理单个音频文件
                    segments = self.split_single_audio(input_path, output_folder, file_base_name, duration, output_format, transition_sound)
                    self.log_message(f"  完成分割: {filename} -> {len(segments)} 个片段 ({output_format})")
                except Exception as e:
                    self.log_message(f"处理 {filename} 时出错: {str(e)}")
            
            self.progress_var.set(100)
            self.status_var.set("处理完成")
            self.log_message("所有文件处理完成")
            self.log_message(f"输出文件保存在: {output_folder}")
            self.log_message(f"输出格式: {output_format}")
            messagebox.showinfo("完成", "音频分割处理已完成")
            
        except Exception as e:
            self.log_message(f"处理过程中出错: {str(e)}")
            messagebox.showerror("错误", f"处理过程中出错:\n{str(e)}")
        finally:
            self.start_button.config(state="normal")
    
    def split_single_audio(self, input_path, output_folder, file_base_name, segment_duration, output_format, transition_sound=None):
        """处理单个音频文件"""
        self.log_message(f"开始处理 {file_base_name} (格式: {output_format})")
        
        # 调用音频处理模块
        segments = process_audio_file(input_path, output_folder, file_base_name, segment_duration, output_format, transition_sound)
        
        self.log_message(f"完成处理 {file_base_name}")
        return segments


def main():
    root = tk.Tk()
    app = AudioSplitterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()