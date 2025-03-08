import requests
import sys
from http import HTTPStatus
from telegram.ext import CommandHandler, Updater, Filters, MessageHandler
from constants import TOKEN_TG, MODEL_NAME, API_URL, YA_TOKEN
from exceptions import RequestErrorApi, NotConstants, NotData


def check_constants() -> None:
    required_vars = [TOKEN_TG, MODEL_NAME, API_URL, YA_TOKEN]
    if not all(required_vars):
        raise NotConstants(
            "Отсутствуют обязательные переменные, "
            "работа остановлена."
        )


def check_and_return_response(response) -> str:
    output = response["result"]["alternatives"][0]["message"]["text"]
    if not output:
        raise NotData(
            "Отсутствуют данные в ответе"
        )
    return output


def request_for_model(message) -> requests.Response:
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
    return response.json()


def messages(update, context) -> None:
    chat = update.effective_chat
    message = update.message.text
    try:
        response = request_for_model(message)
        output = check_and_return_response(response)
    except Exception as e:
        text = f"Возникла ошибка в работе программы: {e}"
        context.bot.sen_message(chat_id=chat.id, text=text)
    context.bot.send_message(chat_id=chat.id, text=output)


def main() -> None:
    updater = Updater(token=TOKEN_TG)
    try:
        check_constants()
    except Exception:
        sys.exit(1)
    updater.dispatcher.add_handler(
        MessageHandler(Filters.text, messages)
    )
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
