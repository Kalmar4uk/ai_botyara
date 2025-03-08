import requests
import sys
from http import HTTPStatus
from telegram.ext import (
    CallbackContext, CommandHandler, Updater, Filters, MessageHandler
)
from constants import TOKEN_TG, MODEL_NAME, API_URL, YA_TOKEN
from exceptions import RequestErrorApi, NotData, NotMessage
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
        logger.info("Преобразовываем ответ из json")
        response: dict[str, any] = response.json()
    except ValueError as error:
        logger.critical(
            error
        )
        raise RequestErrorApi(
            f"Ошибка при преобразовании ответа: {error}"
        )
    logger.info("Получаем текст сообщения из ответа")
    output: str = response.get(
        "result"
        ).get("alternatives")[0].get(
            "message"
        ).get("text")

    logger.info(
        f"Текст полученного сообщения: "
        f"\"{output}\""
    )
    if not output:
        logger.warning(
            "Отсутствуют данные в ответе"
        )
        raise NotData(
            "Отсутствуют данные в ответе"
        )
    logger.debug("Возвращаем текст сообщения из ответа")
    return output


def request_for_model(message: str) -> requests.Response:
    """Функция запроса к апи ИИ-модели"""
    if not message:
        logger.warning(
            "Отсутствует текст в полученном сообщении"
        )
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
        logger.info(
            "Отправляем запрос к АПИ"
        )
        response: requests.Response = requests.post(API_URL, headers=headers, json=promt)
    except requests.RequestException as error:
        logger.critical(
            error
        )
        raise RequestErrorApi(
            f"Ошибка при отправке запроса: {error}"
        )
    if response.status_code != HTTPStatus.OK:
        logger.critical(
            f"Статус ответа не соответствует ожиданию: {response.status_code}"
        )
        raise RequestErrorApi(
            f"Ошибка при получении овета, статус овета: {response.status_code}"
        )
    logger.debug(
        "Вернули ответ запроса АПИ"
    )
    return response


def request_for_api_and_send_message(
        context: CallbackContext,
        chat: any,
        message: str
) -> None:
    """Функция отправки сообщения в чат"""
    try:
        logger.debug(
            "Вызываем функции для отправки запроса к АПИ"
        )
        response: requests.Response = request_for_model(message)
        output: str = check_and_return_response(response)
        logger.info(
            "Отправили сообщение в чат"
        )
        context.bot.send_message(chat_id=chat.id, text=output)
    except Exception as error:
        logger.critical(
            error
        )
        text = f"Возникла ошибка: {error}"
        context.bot.send_message(chat_id=chat.id, text=text)


def messages(update: Updater, context: CallbackContext) -> None:
    """
    Функция получения сообщения и распредления,
    личный или групповой чат
    """
    logger.info(
        f"Получили сообщение \"{update.message.text}\" от "
        f"{update.message.from_user.username}"
    )
    chat: any = update.effective_chat
    message: str = update.message.text
    if chat.type == "private":
        logger.debug(
            "Вызвали функцию ответа для личных сообщений"
        )
        private_chat(chat, context, message)
    else:
        logger.debug(
            "Вызвали функцию ответа для группового чата"
        )
        group_chat(chat, context, message)


def private_chat(chat: any, context: CallbackContext, message: str):
    """Функция ответа бота в личных сообщениях"""
    logger.debug(
        "Вызвали функцию отправки запроса к АПИ"
    )
    request_for_api_and_send_message(context, chat, message)


def group_chat(chat: any, context: CallbackContext, message: str):
    """
    Функция ответа бота в групповом чате
    Регирует только если к нему обращаются
    """
    logger.debug(
        "Вызвали функцию отправки запроса к АПИ"
    )
    if "@TestIntelligenceModelBot" in message:
        message_new: str = message.replace("@TestIntelligenceModelBot", "")
        request_for_api_and_send_message(context, chat, message_new[1:])
    else:
        logger.info(
            "В сообщении из группы отсутствует @TestIntelligenceModelBot, "
            "сообщение проигнорировано"
        )


def hello(update: Updater, context: CallbackContext):
    """Функция приветствия, отрабатывает команду /start"""
    chat: any = update.effective_chat
    output: str = (
        f"Привет {update.message.from_user.username}.\n"
        f"Я бот в который без его ведома засунули "
        f"Yandex GPT. Он как раз и отвечает на все сообщения "
        f"кроме этого."
    )
    logger.info(
        "Отправили сообщение приветствия в чат"
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
