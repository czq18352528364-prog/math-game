"""
批量生成语音 MP3 ── 数字游乐园 · 第一课
=====================================
两种方式任选：
  方式一（推荐·免费）：edge-tts，微软 Xiaoxiao 女声，音质好无需任何 Key
  方式二（最佳音质）：  火山引擎豆包 TTS 桃子音

新版控制台（推荐）：
  https://console.volcengine.com/speech/new → API Key 管理 → 复制 Key
  set VOLC_API_KEY=你的Key
  python gen_audio.py volc

旧版控制台（兼容）：
  set VOLC_APP_ID=你的AppID
  set VOLC_TOKEN=你的Token
  python gen_audio.py volc

免费（无需任何Key）：
  pip install edge-tts
  python gen_audio.py
"""

import os
import asyncio
import sys
import base64
import json

OUT_DIR = "audio"

# ================================================================
# 全部语音片段（id → 要说的文本）
# ================================================================
CLIPS = {
    # ── 夸奖（8句，答对随机抽） ──
    "p1": "太棒啦！你真聪明！",
    "p2": "答对咯！你好厉害呀！",
    "p3": "哇，全对！小脑袋转得真快！",
    "p4": "真了不起，一百分！",
    "p5": "又答对了，你真是小天才！",
    "p6": "好棒呀！企鹅给你拍拍手~",
    "p7": "没错！你越来越厉害了！",
    "p8": "答对啦，闪闪亮亮就是你！",

    # ── 答错前半段（拼答案用） ──
    "w1": "正确答案是",
    "w2": "应该是",
    "w3": "再想想，答案是",

    # ── 答错后半段（鼓励） ──
    "e1": "没关系，我们看看下一题吧",
    "e2": "慢慢来，下次就对啦",
    "e3": "你已经很棒了，继续加油",

    # ── 结果页评语 ──
    "r1": "满分通关！你是最棒的数学小天才！小企鹅为你疯狂鼓掌！",
    "r2": "太厉害啦！你闯过了大部分关卡，再玩一次就能拿满分咯！",
    "r3": "不错哦！你学会了好多本领，再来一次会更好！",
    "r4": "没关系，小企鹅陪你多练几次，下次一定更棒！",

    # ── 欢迎语 + 游戏提示语 ──
    "welcome": "你好呀！我是小企鹅数数~今天我们要玩五个数学小游戏，准备好了吗？",
    "q_count": "数一数，下面有几个气球呀？",
    "q_compare": "哪边更多呀？点点多的那边",
    "q_len_long": "哪条更长呀？点点长的那条",
    "q_len_short": "哪条更短呀？点点短的那条",
    "q_sort": "找出不一样的那个哦",
    "q_pos": "看一看，哪个在上面呀？",
    "q_pos2": "看一看，哪个在左边呀？",
}

# ================================================================
# 方式一：edge-tts（免费，微软 Xiaoxiao 女声，温柔自然）
# ================================================================
VOICE_EDGE = "zh-CN-XiaoxiaoNeural"

async def gen_edge_tts():
    import edge_tts
    os.makedirs(OUT_DIR, exist_ok=True)
    for fid, text in CLIPS.items():
        out = os.path.join(OUT_DIR, f"{fid}.mp3")
        if os.path.exists(out):
            print(f"  ⏭  跳过: {fid}.mp3")
            continue
        print(f"  🎤 {fid}.mp3 ← {text}")
        comm = edge_tts.Communicate(text, VOICE_EDGE)
        await comm.save(out)
    print(f"\n✅ {len(CLIPS)} 个 mp3 → {OUT_DIR}/")


# ================================================================
# 方式二：火山引擎豆包 TTS（V3 SSE，API Key 鉴权）
# ================================================================
def gen_volc_tts():
    """
    新版控制台（推荐）：只需 API_KEY 一个密钥
      https://console.volcengine.com/speech/new → API Key 管理 → 复制 Key
      set VOLC_API_KEY=你的Key
      python gen_audio.py volc

    旧版控制台（兼容）：需 APP_ID + TOKEN
      set VOLC_APP_ID=xxx & set VOLC_TOKEN=xxx
      python gen_audio.py volc
    """
    import requests

    API_KEY = os.environ.get("VOLC_API_KEY", "")
    APP_ID  = os.environ.get("VOLC_APP_ID",  "")
    TOKEN   = os.environ.get("VOLC_TOKEN",   "")

    # 判断鉴权方式
    if API_KEY:
        print("🔑 新版 API Key 鉴权")
        MODE = "new"
    elif APP_ID and TOKEN:
        print("🔑 旧版 AppID+Token 鉴权")
        MODE = "old"
    else:
        print("❌ 请设置环境变量：")
        print("   新版: set VOLC_API_KEY=你的Key  (https://console.volcengine.com/speech/new)")
        print("   旧版: set VOLC_APP_ID=xxx & set VOLC_TOKEN=xxx")
        return

    os.makedirs(OUT_DIR, exist_ok=True)

    # 女声音色（seed-tts-2.0）：
    #   zh_female_vv_uranus_bigtts    — 通用女声，清晰自然
    #   zh_female_xiaohe_uranus_bigtts — 小荷叶，温柔可爱（儿童推荐）
    #   zh_female_cancan_mars_bigtts   — 灿灿，活泼开朗
    #   zh_female_wanwan_mars_bigtts   — 婉婉，轻柔细腻
    SPEAKER = os.environ.get("VOLC_SPEAKER", "zh_female_xiaohe_uranus_bigtts")

    for fid, text in CLIPS.items():
        out = os.path.join(OUT_DIR, f"{fid}.mp3")
        if os.path.exists(out):
            print(f"  ⏭  跳过: {fid}.mp3")
            continue
        print(f"  🍑 {fid}.mp3 ← {text}")

        if MODE == "new":
            headers = {
                "X-Api-Key": API_KEY,
                "X-Api-Resource-Id": "seed-tts-2.0",
                "Content-Type": "application/json",
            }
        else:
            headers = {
                "X-Api-App-Id": APP_ID,
                "X-Api-Access-Key": TOKEN,
                "X-Api-Resource-Id": "seed-tts-2.0",
                "Content-Type": "application/json",
            }

        url = "https://openspeech.bytedance.com/api/v3/tts/unidirectional/sse"
        body = {
            "user": {"uid": "mathgame"},
            "req_params": {
                "text": text,
                "speaker": SPEAKER,
                "audio_params": {
                    "format": "mp3",
                    "sample_rate": 24000,
                },
            },
        }

        try:
            resp = requests.post(url, json=body, headers=headers, timeout=20)
            if resp.status_code != 200:
                print(f"    ⚠️ HTTP {resp.status_code}: {resp.text[:200]}")
                continue

            # SSE 解析：每行 "event: NNN" / "data: {...}"
            mp3_b64 = ""
            for line in resp.text.split("\n"):
                line = line.strip()
                if not line.startswith("data:"):
                    continue
                try:
                    obj = json.loads(line[5:].strip())
                    if obj.get("code", -1) != 0:
                        print(f"    ⚠️ {obj.get('message', obj)}")
                        continue
                    if obj.get("data"):
                        mp3_b64 += obj["data"]
                except json.JSONDecodeError:
                    continue

            if mp3_b64:
                with open(out, "wb") as f:
                    f.write(base64.b64decode(mp3_b64))
                print(f"    ✅ {len(mp3_b64)} chars base64 → mp3")
            else:
                print(f"    ⚠️ 空响应: {resp.text[:200]}")

        except Exception as e:
            print(f"    ⚠️ 异常: {e}")

    print(f"\n✅ 完成！{OUT_DIR}/ 共 {len(os.listdir(OUT_DIR))} 个 mp3")


# ================================================================
# 入口
# ================================================================
if __name__ == "__main__":
    print(__doc__)
    if len(sys.argv) > 1 and sys.argv[1] == "volc":
        print("🍑 火山引擎豆包 TTS (BV704 桃子音)\n")
        gen_volc_tts()
    else:
        print("🎤 edge-tts (微软 XiaoxiaoNeural 免费女声)\n")
        asyncio.run(gen_edge_tts())
