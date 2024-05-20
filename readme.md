# Курсовая работа «ТГ-чат-бот «Обучалка английскому языку»» по курсу «Базы данных»

Бот-переводчик предполагает работу с несколькими категориями, изначально добавлены категории:
- Python;
- Colors;
- Users_words - категория для добавления пользователем своих слов.

Программно количество слов в категориях порезано до 10, чтобы соответстовать требованиям задания, в БД слов больше.

Интерфейс UX/UI адаптирован (по мнению автора).

## Структура БД
Бд выглядит следующим образом:
![Структура БД](education_en_ru.png "БД education_en_ru")

## Работа с БД из бота:
Имеются три команды:
<br>/create_tables - создаёт необходимые таблицы в БД
<br>/drop_tables - дропает таблицы
<br>/add_data_to_bd - добавляет данные в таблицы

## settings.py
Также для работы бота необходимо создать файл settings.py, со след содержанием:
<br>bot_token = 'токен бота'
<br>DSN = "postgresql://username:userpassword@localhost:5432/bdname" #подключение к бд
<br>admin_chat_id = [chat_id_of_admin] #список chat_id для работы с бд
<br>word_limit = 10 #лимит на выборку слов на изучение пользователем