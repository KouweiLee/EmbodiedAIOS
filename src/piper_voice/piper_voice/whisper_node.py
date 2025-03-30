import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import subprocess
import whisper
import time
import os
from piper_msgs.srv import PlayText


KEYWORDS = ["你好", "开始", "激活"]
TEMP_AUDIO_FILE = "./temp_listen.wav"

class WhisperNode(Node):
    def __init__(self):
        super().__init__('whisper_node')
        self.model = whisper.load_model("small")  # 可选 base / medium / large
        self.get_logger().info("✅ ✅ ✅ Whisper 模型加载完成，准备监听语音指令")
        self.publisher = self.create_publisher(String, 'voice_command', 10)
        # self.tts_pub = self.create_publisher(String, '·', 10)
        self.client = self.create_client(PlayText, 'play_tts')
        while not self.client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('等待 TTS 服务...')
        # 启动循环监听
        self.request = PlayText.Request()
        self.loop()

    def loop(self):
        while rclpy.ok():
            self.get_logger().info("🎙️ 正在录音 3 秒...")
            self.record_audio(TEMP_AUDIO_FILE, duration=3)
            text = self.transcribe_audio(TEMP_AUDIO_FILE).strip()
            if text:
            # if True:
                for keyword in KEYWORDS:
                    # if True:
                    if keyword in text:
                        print(f"🚀 关键词 '{keyword}' 触发！发布消息到topic")
                        text_command = ''
                        while not text_command:
                            start = time.time()

                            self.publlish_is_sync("你好，请您在我说完后发布指令，您有十秒时间", sync=True)
                            self.record_audio(TEMP_AUDIO_FILE, duration=10)
                            text_command = self.transcribe_audio(TEMP_AUDIO_FILE).strip()
                            if text_command:
                                msg = String(data=text + '。' + text_command)
                                self.publisher.publish(msg)
                                self.get_logger().info(f"📤 发布语音指令: {text + '。' + text_command}")
                                self.publlish_is_sync("收到，正在思考中", sync=False)
                                print('经过了', time.time() - start, ' 秒')
                                break
                            # edge_free_tts(['收到', '正在思考中'], 1, 'zh-CN-XiaoxiaoNeural', './tishi.wav')
                    else:
                        print(f"\r未识别到关键词^_^", end='')
                        continue
            else:
                self.get_logger().warn("🈳 无识别结果")
            time.sleep(1)


    def publlish_is_sync(self, text='说话啊', sync=False):
        self.request.text = text
        self.request.sync = sync
        future = self.client.call_async(self.request)
        rclpy.spin_until_future_complete(self, future)



    # def publlish_is_sync(self, text='说话啊', sync=False):
    #     if sync:
    #         self.tts_pub.publish(String(data="[SYNC]" + text))
    #     else:
    #         self.tts_pub.publish(String(data=text))


    def record_audio(self, filename, duration=3):
        cmd = ["arecord", "-D", "plughw:1,0", "-d", str(duration), "-f", "cd", filename]
        subprocess.run(cmd)

    def transcribe_audio(self, filename):
        result = self.model.transcribe(filename, language="zh")
        return result["text"]

def main(args=None):
    rclpy.init(args=args)
    try:
        rclpy.spin(WhisperNode())
    except KeyboardInterrupt:
        pass
    rclpy.shutdown()