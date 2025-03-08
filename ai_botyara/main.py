import requests
import sys
from http import HTTPStatus
from telegram.ext import CommandHandler, Updater, Filters, MessageHandler
from constants import TOKEN_TG, MODEL_NAME, API_URL, YA_TOKEN
from exceptions import RequestErrorApi, NotConstants, NotData, NotMessage


def check_constants() -> None:
    required_vars = [TOKEN_TG, MODEL_NAME, API_URL, YA_TOKEN]
    if not all(required_vars):
        raise NotConstants(
            "Отсутствуют обязательные переменные, "
            "работа остановлена."
        )


def check_and_return_response(response: requests.Response) -> str:
    try:
        response = response.json()
    except ValueError as e:
        raise RequestErrorApi(
            f"Ошибка при преобразовании ответа: {e}"
        )
    output = response.get(
        "result"
        ).get("alternatives")[0].get(
            "message"
        ).get("text")

    if not output:
        raise NotData(
            "Отсутствуют данные в ответе"
        )
    return output


def request_for_model(message: str) -> requests.Response:
    if not message:
        raise NotMessage(
            "Message text is empty"
        )
    headers = {
        "Authorization": f"Api-Key {YA_TOKEN}",
        "Content-Type": "application/json"
    }
    promt = {
        "modelUri": MODEL_NAME,
        "completionOptions": {
            "stream": False,
            "temperature": 1,
            "maxTokens": "2000",
            "reasoningOptions": {
                "mode": "ENABLED_HIDDEN"
            }
        },
        "messages": [
            {
                "role": "user",
                "text": message
            }
        ]
    }
    try:
        response = requests.post(API_URL, headers=headers, json=promt)
    except requests.RequestException as e:
        raise RequestErrorApi(
            f"Ошибка при отправке запроса: {e}"
        )
    if response.status_code != HTTPStatus.OK:
        raise RequestErrorApi(
            f"Ошибка при получении овета, статус овета: {response.status_code}"
        )
    return response


def request_for_api_and_send_message(context, chat, message) -> None:
    try:
        response = request_for_model(message)
        output = check_and_return_response(response)
        context.bot.send_message(chat_id=chat.id, text=output)
    except Exception as e:
        text = f"Возникла ошибка: {e}"
        context.bot.send_message(chat_id=chat.id, text=text)


def messages(update, context) -> None:
    chat = update.effective_chat
    message: str = update.message.text
    if chat.type == "private":
        private_chat(chat, context, message)
    else:
        group_chat(chat, context, message)


def private_chat(chat, context, message):
    request_for_api_and_send_message(context, chat, message)


def group_chat(chat, context, message):
    if "@TestIntelligenceModelBot" in message:
        message_new = message.replace("@TestIntelligenceModelBot", "")
        request_for_api_and_send_message(context, chat, message_new)


def hello(update, context):
    chat = update.effective_chat
    output = (
        f"Привет {update.message.from_user.username}.\n"
        f"Я бот в который без его ведома засунули "
        f"Yandex GPT. Он как раз и отвечает на все сообщения "
        f"кроме этого."
    )
    context.bot.send_message(chat_id=chat.id, text=output)


def main() -> None:
    updater = Updater(token=TOKEN_TG)
    try:
        check_constants()
    except Exception:
        sys.exit(1)
    updater.dispatcher.add_handler(
        CommandHandler("start", hello)
    )
    updater.dispatcher.add_handler(
        MessageHandler(Filters.text, messages)
    )
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
