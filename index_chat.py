from flask import Flask, request, abort
import os
import openai
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# Set OpenAI API details
openai.api_type = "azure"
openai.api_version = "2023-05-15"
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_base = os.getenv("OPENAI_API_BASE")

app = Flask(__name__)

# Initialize messages list with the system message
messages = [
    {"role": "system", "content": "{{
  "Expert": "LangGPT",
  "Profile": {
    "Author": "YZFly",
    "Version": "1.0",
    "Language": "English",
    "Description": "You are an expert in .NET Core and Entity Framework Core. Your goal is to provide assistance and guidance on using these technologies effectively."
  },
  "Skills": [
    "Proficiency in .NET Core",
    "Expertise in Entity Framework Core",
    "Troubleshooting and problem-solving skills"
  ],
  "Goals": [
    "Help users with .NET Core and Entity Framework Core queries",
    "Provide best practices and code examples",
    "Explain complex concepts in a simple manner"
  ],
  "Constraints": [
    "Don't break character under any circumstance.",
    "Don't talk nonsense and make up facts.",
    "You are a .NET Core and Entity Framework Core expert.",
    "You will strictly follow these constraints.",
    "You will try your best to accomplish these goals."
  ],
  "Init": [
    "Ask user to input [Specific Query or Issue].",
    "Provide relevant code examples and explanations."
  ]
}}"},
]

# This function takes a chat message as input, appends it to the messages list, sends the recent messages to the OpenAI API, and returns the assistant's response.
def aoai_chat_model(chat):
    # Append the user's message to the messages list
    messages.append({"role": "user", "content": chat})

    # Only send the last 5 messages to the API
    recent_messages = messages[-5:]

    # Send the recent messages to the OpenAI API and get the response
    response_chat = openai.ChatCompletion.create(
        engine="GPT35_Dev",
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

# Initialize Line API with access token and channel secret
line_bot_api = LineBotApi(os.getenv('LINE_ACCESS_TOKEN'))
handler1 = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

# This route serves as a health check or landing page for the web app.
@app.route("/")
def mewobot():
    return 'Cat Time!!!'

# This route handles callbacks from the Line API, verifies the signature, and passes the request body to the handler.
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

# This event handler is triggered when a message event is received from the Line API. It sends the user's message to the OpenAI chat model and replies with the assistant's response.
@handler1.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.message.text.startswith("gpt "):
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=aoai_chat_model(event.message.text))
        )

if __name__ == "__main__":
    app.run()
