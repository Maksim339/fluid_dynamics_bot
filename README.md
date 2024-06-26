# Telegram Bot для Гидродинамиков

Этот бот создан для помощи и обслуживания гидродинамиков, позволяя им регистрироваться, задавать вопросы, получать ответы, а также управлять базой данных часто задаваемых вопросов (FAQ).

## Начало работы

### Предварительные требования

- Python версии 3.8 или выше.
- Установленные библиотеки. Их можно установить с помощью pip:

```pip install -r requirements.txt```

- PostgreSQL база данных. 
- Зарегистрированный Telegram бот через BotFather в Telegram.

### Настройка

1. Клонируйте репозиторий на свой локальный компьютер или сервер.
2. Создайте файл `.env` в корневой директории проекта со следующим содержанием:

```bibtex
BOT_TOKEN=<токен вашего бота>
EMAIL_ADDRESS=<адрес вашей электронной почты>
EMAIL_PASSWORD=<пароль от вашей электронной почты>
DB_NAME=<имя вашей базы данных>
DB_USER=<имя пользователя базы данных>
DB_PASSWORD=<пароль базы данных>
DB_HOST=<хост базы данных>
```
### Настройка базы данных

Для начала создайте базу данных PostgreSQL:

```sudo -u postgres psql -c "CREATE DATABASE <имя вашей базы данных>;"```

Затем примените дамп из репозитория [schema_dump.sql](https://github.com/Maksim339/fluid_dynamics_bot/blob/main/schema_dump.sql)


```sudo -u postgres psql <имя вашей базы данных> < schema_dump.sql```

### Запуск бота

Выполните следующую команду для запуска бота:

```python bot.py```


Замените `bot.py` на имя файла вашего скрипта.

## Развертывание на сервере Ubuntu через systemd

Следуйте инструкциям ниже для настройки бота как сервиса systemd:

1. Создайте файл сервиса:

```sudo vim /etc/systemd/system/your_bot.service```


2. Добавьте следующее содержание, заменив значения на свои:

```bibtex
[Unit]
Description=Telegram Bot
After=network.target

[Service]
User=<ваш пользователь>
WorkingDirectory=/путь/к/директории/с/ботом
ExecStart=/usr/bin/python3 /путь/к/директории/с/ботом/имя_файла.py

[Install]
WantedBy=multi-user.target
```

3. Перезагрузите daemon systemd:

```sudo systemctl daemon-reload```


4. Включите сервис, чтобы он запускался при старте системы:

```sudo systemctl enable your_bot.service```


5. Запустите сервис:

```sudo systemctl start your_bot.service```

6. Проверьте статус сервиса:

```sudo systemctl status your_bot.service```


## Использование бота

Бот поддерживает следующие команды:

- `/start` - начало работы с ботом. Бот приветствует пользователя и предлагает основную информацию о себе.
- `/register` - регистрация пользователя. Бот запрашивает email пользователя и отправляет на него код подтверждения. После ввода кода пользователь считается зарегистрированным.
- `/del` - удаление вопроса из базы данных. Бот запрашивает у пользователя вопрос, который необходимо удалить, и удаляет его после подтверждения.
- `/edit` - редактирование ответа на вопрос в базе данных. Пользователь указывает вопрос, который хочет отредактировать, и вводит новый ответ.
- `/train` - добавление нового вопроса и ответа в базу данных. Бот запрашивает у пользователя вопрос и ответ, затем сохраняет их в базе данных.

Пользователи могут задавать вопросы напрямую боту, и он будет искать наиболее подходящие ответы в базе данных или генерировать ответы с помощью внешнего API, если вопрос новый и не содержится в базе.

## Авторы

- [Максим Пугачев](https://t.me/pugachev_maksim)
- [Илья Удовиченко](https://t.me/skittelsilya)
- [Кира Ворон](https://t.me/kiravoron7)
- [Эмиль Мухамедов](https://t.me/Emilio_1717)









