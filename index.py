import config
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageMessage
import json
from openai import OpenAI
from dotenv import load_dotenv

app = Flask(__name__)

line_bot_api = LineBotApi(config.LINE_CHANNEL_ACCESS_TOKEN)    
handler = WebhookHandler(config.LINE_CHANNEL_SECRET)    
load_dotenv()
client = OpenAI()

# Dictionary to store conversation history for each user
conversation_history = {}

@app.route("/", methods=['GET'])
def callback():
    return 'OK'

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)
    
    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    
    if event.reply_token == "00000000000000000000000000000000":
        return
    
    # Initialize history for new users
    if user_id not in conversation_history:
        conversation_history[user_id] = []
    
    # Append the new message to the user's conversation history
    conversation_history[user_id].append({"role": "user", "content": event.message.text})
    
    # Limit history to last 4 messages
    if len(conversation_history[user_id]) > 6:
        conversation_history[user_id] = conversation_history[user_id][-6:]
    
    if event.message.text == "食事投稿":
        reply = TextSendMessage(text="食事の画像を送ってくださいにゃん")
    else:
        # Add the initial system message and the user's conversation history
        messages = [{"role": "system", "content": "あなたはみうらそうま23歳です。岡山弁で、興味なさそうなタメ口ではなします。あなたの話す言葉は日本語で40文字以下です。配信者のMKRがとても大好きです。そして話し上手なので新しい話題を振ったりもします。遊びに誘うと彼女のりりちゃんとの予定があり断ります。句読点やビックリマークは使いません。みうらそうまの彼女はりりちゃんという名前で、りりちゃんの話題になると非常に楽しそうに話します。りりちゃんは熊本に住んでいて、MKRのディスコードで知り合いました。スマブラではソラを使います。ポケモンの中ではアチゲータが好きです。"}] + conversation_history[user_id]
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        bot_reply = completion.choices[0].message.content
        
        # Add bot's response to the conversation history
        conversation_history[user_id].append({"role": "assistant", "content": bot_reply})
        
        reply = TextSendMessage(text=bot_reply)
    
    line_bot_api.reply_message(
        event.reply_token,
        reply
    )


@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    reply = TextSendMessage(text="その画像しゅええわ")
    line_bot_api.reply_message(
        event.reply_token,
        reply
    )

if __name__ == "__main__":
    app.run(host="localhost", port=5001, debug=True)
