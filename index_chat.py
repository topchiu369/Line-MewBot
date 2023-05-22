from flask import Flask, request, abort
import os
import openai
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

openai.api_type = "azure"
openai.api_base = "https://qna-openai.openai.azure.com/"
openai.api_version = "2023-03-15-preview"
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_base = os.getenv("OPENAI_API_BASE")

app = Flask(__name__)

# Initialize messages list with the system message
messages = [
    {"role": "system", "content": "You are a helpful assistant that has a deep understanding of cat and also speak like a cat. \
                                   You know everything about cats, lifestyles, habits, anecdotes, and rarely-known cat facts. \
                                   Refrain from responding in simplified Chinese, you will primarily respond in traditional Chinese."},
]

def aoai_chat_model(chat):
    # Append the user's message to the messages list
    messages.append({"role": "user", "content": chat})

    # Only send the last 5 messages to the API
    recent_messages = messages[-5:]


    response_chat = openai.ChatCompletion.create(
        engine="gpt-35-turbo",
        messages=recent_messages,
        temperature=0.7,
        max_tokens=150,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None
    )

    # Append the assistant's response to the messages list
    messages.append({"role": "assistant", "content": response_chat['choices'][0]['message']['content'].strip()})

    return response_chat['choices'][0]['message']['content'].strip()

# while True:
#     chat = input('來抬槓：')
#     if chat.lower() == "沒問題了":
#         break
#     print(aoai_chat_model(chat))  

line_bot_api = LineBotApi(os.getenv('LINE_ACCESS_TOKEN'))
handler1 = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

@app.route("/")
def mewobot():
    return 'Cat Time!!!'

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    try:
        handler1.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)
    return 'OK'

@handler1.add(MessageEvent, message=TextMessage)
def handle_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=aoai_chat_model(event.message.text))
    )

if __name__ == "__main__":
    app.run()
