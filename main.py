import difflib
import os
from dotenv import load_dotenv
import telebot
import psycopg2

load_dotenv()

API_TOKEN = os.environ['BOT_TOKEN']
DB_PARAMS = {
    "dbname": os.environ['DB_NAME'],
    "user": os.environ['DB_USER'],
    "password": os.environ['DB_PASSWORD'],
    "host": os.environ['DB_HOST'],
}

bot = telebot.TeleBot(API_TOKEN)


def get_db_connection():
    conn = psycopg2.connect(**DB_PARAMS)
    return conn


def find_closest_match(user_question, chat_id):
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
            bot.send_message(chat_id, "Извините, я не могу найти ответ на ваш вопрос.")
    except Exception as e:
        print(e)
        bot.send_message(chat_id, "Произошла ошибка при поиске ответа.")
    finally:
        cur.close()
        conn.close()


@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(
        message.chat.id,
        "Привет! Я бот для гидродинамиков.\n"
             "Постараюсь ответить на ваши вопросы!\n"
             "Используйте команду /train для обучения меня новым вопросам."
    )


pending_additions = {}


@bot.message_handler(commands=['train'])
def add_faq_start(message):
    msg = bot.send_message(message.chat.id, "Введите вопрос:")
    bot.register_next_step_handler(msg, add_question, message.chat.id)


@bot.message_handler(func=lambda message: True, content_types=['text'])
def answer_question(message):
    user_question = message.text
    find_closest_match(user_question, message.chat.id)


def add_question(message, chat_id):
    question = message.text
    pending_additions[chat_id] = {'question': question}
    msg = bot.send_message(chat_id, "Теперь введите ответ на вопрос:")
    bot.register_next_step_handler(msg, add_answer, chat_id)


def add_answer(message, chat_id):
    answer = message.text
    if chat_id in pending_additions:
        pending_additions[chat_id]['answer'] = answer
        insert_faq(pending_additions[chat_id]['question'], answer, chat_id)
        del pending_additions[chat_id]


def insert_faq(question, answer, chat_id):
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
