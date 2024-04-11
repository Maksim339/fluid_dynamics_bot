import difflib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import random
import os
from dotenv import load_dotenv
import telebot
from telebot import types
import psycopg2
import re
from langchain.schema import HumanMessage, SystemMessage
from langchain.chat_models.gigachat import GigaChat
from telebot.types import Message, CallbackQuery

chat = GigaChat(
    credentials=os.environ['GIGACHAT_TOKEN'],
    verify_ssl_certs=False)

messages = [
    SystemMessage(
        content="Ты чат-бот для крутых гидродинамиков Альберт"
    )
]

load_dotenv()

API_TOKEN: str = os.environ['BOT_TOKEN']

EMAIL_ADDRESS: str = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD: str = os.getenv('EMAIL_PASSWORD')

DB_PARAMS: dict = {
    "dbname": os.environ['DB_NAME'],
    "user": os.environ['DB_USER'],
    "password": os.environ['DB_PASSWORD'],
    "host": os.environ['DB_HOST'],
}

bot = telebot.TeleBot(API_TOKEN)


@bot.message_handler(commands=['del'])
def delete_faq_start(message: Message) -> None:
    user_id: int = message.from_user.id
    if is_user_registered(user_id):
        msg = bot.send_message(message.chat.id, "Какой вопрос вы хотите удалить?")
        bot.register_next_step_handler(msg, find_question_to_delete, message.chat.id)
    else:
        bot.send_message(message.chat.id,
                         "Для использования этой команды необходимо зарегистрироваться. Используйте команду /register.")


def find_question_to_delete(message: Message, chat_id: int) -> None:
    user_question: str = message.text
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT question FROM faq")
        questions = [row[0] for row in cur.fetchall()]
        closest_match = difflib.get_close_matches(user_question, questions, n=1, cutoff=0.6)
        if closest_match:
            markup = types.InlineKeyboardMarkup()
            yes_button = types.InlineKeyboardButton("Да", callback_data=f"del_yes|{closest_match[0]}")
            no_button = types.InlineKeyboardButton("Нет", callback_data="del_no")
            markup.add(yes_button, no_button)
            bot.send_message(chat_id, f"Вы хотите удалить этот вопрос: \"{closest_match[0]}\"?", reply_markup=markup)
        else:
            bot.send_message(chat_id, "Похожий вопрос не найден. Попробуйте снова.")
    except Exception as e:
        print(e)
    finally:
        cur.close()
        conn.close()


@bot.callback_query_handler(func=lambda call: call.data.startswith("del_"))
def handle_delete_query(call: CallbackQuery) -> None:
    if call.data.startswith("del_yes"):
        _, question = call.data.split("|", 1)
        delete_faq(question, call.message.chat.id)
    elif call.data == "del_no":
        bot.send_message(call.message.chat.id, "Попробуйте указать другой вопрос для удаления или отмените операцию.")


def delete_faq(question: str, chat_id: int) -> None:
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM faq WHERE question = %s", (question,))
        conn.commit()
        bot.send_message(chat_id, "Вопрос успешно удален из базы данных.")
    except Exception as e:
        print(e)
        bot.send_message(chat_id, "Произошла ошибка при удалении вопроса.")
    finally:
        cur.close()
        conn.close()


@bot.message_handler(commands=['edit'])
def edit_faq_start(message: Message) -> None:
    user_id: int = message.from_user.id
    if is_user_registered(user_id):
        msg = bot.send_message(message.chat.id, "Какой вопрос вы хотите изменить?")
        bot.register_next_step_handler(msg, find_question_to_edit, message.chat.id)
    else:
        bot.send_message(message.chat.id,
                         "Для использования этой команды необходимо зарегистрироваться. Используйте команду /register.")


def find_question_to_edit(message: Message, chat_id: int) -> None:
    user_question: str = message.text
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT question FROM faq")
        questions = [row[0] for row in cur.fetchall()]
        closest_match = difflib.get_close_matches(user_question, questions, n=1, cutoff=0.6)
        if closest_match:
            markup = types.InlineKeyboardMarkup()
            yes_button = types.InlineKeyboardButton("Да", callback_data=f"edit_yes|{closest_match[0]}")
            no_button = types.InlineKeyboardButton("Нет", callback_data="edit_no")
            markup.add(yes_button, no_button)
            bot.send_message(chat_id, f"Вы хотите изменить этот вопрос: \"{closest_match[0]}\"?", reply_markup=markup)
        else:
            bot.send_message(chat_id, "Похожий вопрос не найден. Попробуйте снова.")
    except Exception as e:
        print(e)
    finally:
        cur.close()
        conn.close()


@bot.callback_query_handler(func=lambda call: True)
def handle_query(call: CallbackQuery) -> None:
    if call.data.startswith("edit_yes"):
        _, question = call.data.split("|", 1)
        msg = bot.send_message(call.message.chat.id, "Введите новый ответ на вопрос:")
        bot.register_next_step_handler(msg, update_faq, question)
    elif call.data == "edit_no":
        bot.send_message(call.message.chat.id, "Введите вопрос, который вы хотите изменить:")
        bot.register_next_step_handler(call.message, find_question_to_edit, call.message.chat.id)


def update_faq(message: Message, question: str) -> None:
    new_answer: str = message.text
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE faq SET answer = %s WHERE question = %s", (new_answer, question))
        conn.commit()
        bot.send_message(message.chat.id, "Ответ успешно обновлен.")
    except Exception as e:
        print(e)
        bot.send_message(message.chat.id, "Произошла ошибка при обновлении ответа.")
    finally:
        cur.close()
        conn.close()


def send_confirmation_email(email: str, code: int) -> None:
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = email
    msg['Subject'] = 'Код подтверждения регистрации'
    body = f'Ваш код подтверждения: {code}'
    msg.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    text = msg.as_string()
    server.sendmail(EMAIL_ADDRESS, email, text)
    server.quit()


@bot.message_handler(commands=['register'])
def request_email(message: Message) -> None:
    msg = bot.send_message(message.chat.id, "Введите вашу почту (@contractor.gazprom-neft.ru или @gazprom-neft.ru):")
    bot.register_next_step_handler(msg, process_email_registration, message.from_user.id)


def process_email_registration(message: Message, user_id: int) -> None:
    email: str = message.text.lower()
    if re.match(r".+@(contractor\.gazprom-neft\.ru|gazprom-neft\.ru)$", email):
        confirmation_code: int = random.randint(100000, 999999)
        send_confirmation_email(email, confirmation_code)

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO registered_users (user_id, email, email_confirmed) VALUES (%s, %s, FALSE) ON CONFLICT (user_id) DO UPDATE SET email = %s, email_confirmed = FALSE",
                (user_id, email, email))
            conn.commit()
            msg = bot.send_message(message.chat.id, "Мы отправили код подтверждения на вашу почту. Введите его здесь:")
            bot.register_next_step_handler(msg, confirm_email_registration, user_id, confirmation_code)
        except Exception as e:
            print(e)
            bot.send_message(message.chat.id, "Произошла ошибка при регистрации.")
        finally:
            cur.close()
            conn.close()
    else:
        bot.send_message(message.chat.id,
                         "Почта должна быть на домене @contractor.gazprom-neft.ru или @gazprom-neft.ru.")


def confirm_email_registration(message: Message, user_id: int, expected_code: int) -> None:
    entered_code: str = message.text
    if str(expected_code) == entered_code:
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("UPDATE registered_users SET email_confirmed = TRUE WHERE user_id = %s", (user_id,))
            conn.commit()
            bot.send_message(message.chat.id, "Вы успешно зарегистрированы и подтвердили свою почту.")
        except Exception as e:
            print(e)
            bot.send_message(message.chat.id, "Произошла ошибка при подтверждении почты.")
        finally:
            cur.close()
            conn.close()
    else:
        bot.send_message(message.chat.id, "Код подтверждения неверен.")


def is_user_registered(user_id: int) -> bool:
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT EXISTS(SELECT 1 FROM registered_users WHERE user_id = %s)", (user_id,))
        return cur.fetchone()[0]
    except Exception as e:
        print(e)
        return False
    finally:
        cur.close()
        conn.close()


def get_db_connection() -> psycopg2.extensions.connection:
    return psycopg2.connect(**DB_PARAMS)


def find_closest_match(user_question: str, chat_id: int) -> None:
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT question, answer FROM faq")
        faq_data = cur.fetchall()
        questions = [row[0] for row in faq_data]
        closest_match = difflib.get_close_matches(user_question, questions, n=1, cutoff=0.6)
        if closest_match:
            answer = next((row[1] for row in faq_data if row[0] == closest_match[0]), None)
            bot.send_message(chat_id, answer)
        else:
            messages.append(HumanMessage(content=user_question))
            res = chat.invoke(messages)
            messages.append(res)
            bot.send_message(chat_id, res.content)
    except Exception as e:
        print(e)
        bot.send_message(chat_id, "Произошла ошибка при поиске ответа.")
    finally:
        cur.close()
        conn.close()


@bot.message_handler(commands=['start'])
def start_message(message: Message) -> None:
    bot.send_message(
        message.chat.id,
        "Привет! Я бот для гидродинамиков.\n"
        "Постараюсь ответить на ваши вопросы!\n"
        "Используйте команду /train для обучения меня новым вопросам."
    )


pending_additions: dict = {}


@bot.message_handler(commands=['train'])
def add_faq_start(message: Message) -> None:
    user_id: int = message.from_user.id
    if is_user_registered(user_id):
        msg = bot.send_message(message.chat.id, "Введите вопрос:")
        bot.register_next_step_handler(msg, add_question, message.chat.id)
    else:
        bot.send_message(message.chat.id,
                         "Для использования этой команды необходимо зарегистрироваться. Используйте команду /register.")


@bot.message_handler(func=lambda message: True, content_types=['text'])
def answer_question(message: Message) -> None:
    user_question: str = message.text
    find_closest_match(user_question, message.chat.id)


def add_question(message: Message, chat_id: int) -> None:
    question: str = message.text
    pending_additions[chat_id] = {'question': question}
    msg = bot.send_message(chat_id, "Теперь введите ответ на вопрос:")
    bot.register_next_step_handler(msg, add_answer, chat_id)


def add_answer(message: Message, chat_id: int) -> None:
    answer: str = message.text
    if chat_id in pending_additions:
        pending_additions[chat_id]['answer'] = answer
        insert_faq(pending_additions[chat_id]['question'], answer, chat_id)
        del pending_additions[chat_id]


def insert_faq(question: str, answer: str, chat_id: int) -> None:
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO faq (question, answer) VALUES (%s, %s)", (question, answer))
        conn.commit()
        bot.send_message(chat_id, "Вопрос и ответ успешно добавлены.")
    except Exception as e:
        print(e)
        bot.send_message(chat_id, "Произошла ошибка при добавлении вопроса и ответа.")
    finally:
        cur.close()
        conn.close()


if __name__ == '__main__':
    bot.polling(none_stop=True)
