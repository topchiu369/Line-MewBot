from flask import Flask, request, abort, jsonify
import os
import openai
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_bolt.adapter.flask import SlackRequestHandler
from slack_bolt import App

# Set OpenAI API details
openai.api_type = "azure"
openai.api_version = "2023-05-15"
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_base = os.getenv("OPENAI_API_BASE")
bot_token = os.getenv("SLACK_TOKEN")
verification_token = os.getenv("V_TOKEN")
SLACK_SIGNING_SECRET = os.getenv["SLACK_SIGNING_SECRET"]
SLACK_BOT_USER_ID = os.getenv["SLACK_BOT_USER_ID"]

app = App(token=SLACK_BOT_TOKEN)
signature_verifier = SignatureVerifier(SLACK_SIGNING_SECRET)

app = Flask(__name__)
handler = SlackRequestHandler(app)

# Initialize messages list with the system message
messages = [
    {"role": "system", "content": '''{{
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
  ]
}}'''},
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

def require_slack_verification(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not verify_slack_request():
            abort(403)
        return f(*args, **kwargs)

    return decorated_function


def verify_slack_request():
    # Get the request headers
    timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
    signature = request.headers.get("X-Slack-Signature", "")

    # Check if the timestamp is within five minutes of the current time
    current_timestamp = int(time.time())
    if abs(current_timestamp - int(timestamp)) > 60 * 5:
        return False

    # Verify the request signature
    return signature_verifier.is_valid(
        body=request.get_data().decode("utf-8"),
        timestamp=timestamp,
        signature=signature,
    )


def get_bot_user_id():
    """
    Get the bot user ID using the Slack API.
    Returns:
        str: The bot user ID.
    """
    try:
        # Initialize the Slack client with your bot token
        slack_client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
        response = slack_client.auth_test()
        return response["user_id"]
    except SlackApiError as e:
        print(f"Error: {e}")

@app.event("app_mention")                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      
def mention_handler(body, say):
    text = body["event"]["text"]

    mention = f"<@{SLACK_BOT_USER_ID}>"
    text = text.replace(mention, "").strip()
    logging.info("Received text: " + text.replace("\n", " "))

    say("Sure, I'll get right on that!")
    # response = my_function(text)
    response = aoai_chat_model(text)
    logging.info("Generated response: " + response.replace("\n", " "))
    say(response)


@flask_app.route("/slack/events", methods=["POST"])
@require_slack_verification
def slack_events():
    return handler.handle(request)

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
