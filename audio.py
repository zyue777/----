import os
import subprocess
import threading
import edge_tts
import asyncio
from pathlib import Path

# 本地音频缓存目录
AUDIO_CACHE_DIR = os.path.join(os.path.dirname(__file__), '.cache', 'audio')

# 确保缓存目录存在
os.makedirs(AUDIO_CACHE_DIR, exist_ok=True)

async def _generate_audio(text: str, filepath: str, voice: str = "en-US-AriaNeural"):
    """
    内部异步方法：使用 edge-tts 生成音频并保存
    """
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(filepath)

def _run_in_thread(coro):
    """在独立线程中运行协程, 避免与 Textual 的 event loop 冲突"""
    def runner():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(coro)
        finally:
            loop.close()
    t = threading.Thread(target=runner, daemon=True)
    t.start()
    t.join()  # 等待生成完成再播放

def play_audio(word: str, bg_playback: bool = True):
    """
    主要调用入口：
    1. 检查本地是否有该单词的缓存 mp3
    2. 如果没有 -> 在独立线程中调用 edge-tts 生成（避免与 Textual event loop 冲突）
    3. 如果有 -> 直接使用 mpv 在终端后台静默播放
    """
    # 清理文件名可能存在的不合法字符
    safe_word = "".join(c for c in word if(c.isalnum() or c in "'-_ ")).strip()
    if not safe_word:
        return
        
    filename = f"{safe_word.replace(' ', '_')}.mp3"
    filepath = os.path.join(AUDIO_CACHE_DIR, filename)
    
    # 若缓存不存在，在独立线程中生成
    if not os.path.exists(filepath):
        try:
            _run_in_thread(_generate_audio(word, filepath))
        except Exception as e:
            print(f"音频生成失败: {e}")
            return
            
    # 使用系统级 mpv 播放器播放
    try:
        # --no-terminal 静默后台播放，防止污染 TUI 界面
        if bg_playback:
            subprocess.Popen(['mpv', '--no-terminal', filepath], 
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL)
        else:
            # 同步阻塞播放 (主要用于测试)
            subprocess.run(['mpv', '--no-terminal', filepath], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL, 
                           check=True)
    except FileNotFoundError:
        print("【错误】未找到 mpv 播放器。请确保系统已安装 (如: sudo apt install mpv)")
    except Exception as e:
        print(f"播放音频失败: {e}")

if __name__ == "__main__":
    # 简单测试逻辑
    print("Testing edge-tts... generating and playing 'Hello World'...")
    play_audio("Hello World", bg_playback=False)
    print("Test finished.")
