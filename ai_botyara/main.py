import requests
import sys
from http import HTTPStatus
from telegram.ext import CallbackContext, CommandHandler, Updater, Filters, MessageHandler
from constants import TOKEN_TG, MODEL_NAME, API_URL, YA_TOKEN
from exceptions import RequestErrorApi, NotConstants, NotData, NotMessage
from settings_logs import logger


def check_constants() -> None:
    """
    Функция проверки необходимых переменных окружения
    """
    required_vars: list = [TOKEN_TG, MODEL_NAME, API_URL, YA_TOKEN]
    if not all(required_vars):
        logger.critical(
            "Отсутствуют обязательные переменные, "
            "работа остановлена.")
        sys.exit(1)


def check_and_return_response(response: requests.Response) -> str:
    """
    Функция проверки ответа АПИ на валидность
    и наличия необходимых данных
    """
    try:
        response: dict[str, any] = response.json()
    except ValueError as e:
        raise RequestErrorApi(
            f"Ошибка при преобразовании ответа: {e}"
        )
    output: str = response.get(
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
    """Функция запроса к апи ИИ-модели"""
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
        response: requests.Response = requests.post(API_URL, headers=headers, json=promt)
    except requests.RequestException as e:
        raise RequestErrorApi(
            f"Ошибка при отправке запроса: {e}"
        )
    if response.status_code != HTTPStatus.OK:
        raise RequestErrorApi(
            f"Ошибка при получении овета, статус овета: {response.status_code}"
        )
    return response


def request_for_api_and_send_message(context: CallbackContext, chat: any, message: str) -> None:
    """Функция отправки сообщения в чат"""
    try:
        response: requests.Response = request_for_model(message)
        output: str = check_and_return_response(response)
        context.bot.send_message(chat_id=chat.id, text=output)
    except Exception as e:
        text = f"Возникла ошибка: {e}"
        context.bot.send_message(chat_id=chat.id, text=text)


def messages(update: Updater, context: CallbackContext) -> None:
    """
    Функция получения сообщения и распредления,
    личный или групповой чат
    """
    chat: any = update.effective_chat
    message: str = update.message.text
    if chat.type == "private":
        private_chat(chat, context, message)
    else:
        group_chat(chat, context, message)


def private_chat(chat: any, context: CallbackContext, message: str):
    """Функция ответа бота в личных сообщениях"""
    request_for_api_and_send_message(context, chat, message)


def group_chat(chat: any, context: CallbackContext, message: str):
    """
    Функция ответа бота в групповом чате
    Регирует только если к нему обращаются
    """
    if "@TestIntelligenceModelBot" in message:
        message_new: str = message.replace("@TestIntelligenceModelBot", "")
        request_for_api_and_send_message(context, chat, message_new[1:])


def hello(update: Updater, context: CallbackContext):
    """Функция приветствия, отрабатывает команду /start"""
    chat: any = update.effective_chat
    output: str = (
        f"Привет {update.message.from_user.username}.\n"
        f"Я бот в который без его ведома засунули "
        f"Yandex GPT. Он как раз и отвечает на все сообщения "
        f"кроме этого."
    )
    context.bot.send_message(chat_id=chat.id, text=output)


def main() -> None:
    """Основная функция"""
    check_constants()
    updater: Updater = Updater(token=TOKEN_TG)
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
