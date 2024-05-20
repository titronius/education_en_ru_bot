import random
import settings
from telebot import types, TeleBot
from models import BdInstruments, User, UserStatus, CategoryName, UserWord, UserWordStatus, Vocabulary

token_bot = settings.bot_token
bot = TeleBot(token_bot)

bot_about_msg = """
👋🏻 *Добро пожаловать в бота-помощника по изучению английских слов.*

*В боте реализованы три категории для изучения:*
1️⃣ Python
2️⃣ Colors
3️⃣ Users\\_words

3 категорию Вы наполняете сами теми словами, которые желаете изучить,
минимум 4 слова понадобится чтобы заработал этот раздел.

Добавлять слова можно при помощи кнопки 'Добавить слово в users\\_word'.

Также Вы можете нажать кнопку 'Выбрать категорию' и начать изучать предложенные темы.

*Удачи!* 😀
"""

class Command():
    choose_category = "👆🏻 Выбрать категорию"
    bot_about = "🤖 О боте"
    word_add = "➕ Добавить слово в users_word"

def add_words_for_user(chat_id, category_id):
    continue_func = True
    if category_id == '3':
        words = UserWord.get_words_for_category(chat_id, category_id, 3, 4)
        if len(words) < 4:
            continue_func = False
            keyboard = types.InlineKeyboardMarkup()
            button = types.InlineKeyboardButton("➕ Добавить слово", callback_data = "addword:")
            keyboard.add(button)
            bot.send_message(chat_id, f"🤷 *Маловато слов для изучения*, сейчас {len(words)}, минимум нужно 4!", parse_mode = "Markdown", reply_markup = keyboard)
    if continue_func:
        user_words_status = UserWordStatus.get_status_for_cat(chat_id, category_id)
        in_study = False
        if user_words_status:
            for word in user_words_status:
                if word.status_id in [3,4]:
                    in_study = True
                    break
        if not in_study:
            len_of_words = UserWord.add_words_for_user(chat_id, category_id)
            category = CategoryName.get_category(category_id)
            bot.send_message(chat_id, f"👨‍🎓 Вам предстоит изучить {len_of_words} слов из категории: {category.name}", parse_mode = "Markdown")
        study_category(chat_id, category_id)

def study_category(chat_id, category_id):
    status_id = 3
    limit = 1
    word = UserWord.get_words_for_category(chat_id, category_id, status_id, limit)
    if word:
        word_info = Vocabulary.get_word(word.word_id)
        wrong_words = Vocabulary.get_wrong_words(word.word_id, category_id)
        random_wrong_words = []
        number_of_wrong_words = 3
        while len(random_wrong_words) != number_of_wrong_words:
            random_element = random.choice(wrong_words)
            if random_element not in random_wrong_words:
                random_wrong_words.append(random_element)
        keyboard = types.InlineKeyboardMarkup(row_width = 1)
        buttons = []
        button = types.InlineKeyboardButton(f"{word_info.en}", callback_data = f"answer:{word_info.id};{word_info.id};{category_id}")
        buttons.append(button)
        for wrong_word in random_wrong_words:
            button = types.InlineKeyboardButton(f"{wrong_word.en}", callback_data = f"answer:{word_info.id};{wrong_word.id};{category_id}")
            buttons.append(button)
        random.shuffle(buttons)
        keyboard.add(*buttons)
        button = types.InlineKeyboardButton("⏭ Пропустить слово", callback_data = f"skip:{word_info.id};{category_id}")
        keyboard.add(button)
        button = types.InlineKeyboardButton("❌ Удалить слово", callback_data = f"delete:{word.id};{category_id}")
        keyboard.add(button)
        bot.send_message(chat_id, f"🔠 Выберите правильный перевод для слова:\n*{word_info.ru}*", parse_mode = "Markdown", reply_markup = keyboard)
    else:
        keyboard = types.InlineKeyboardMarkup()
        button = types.InlineKeyboardButton("Начать заново", callback_data = f"refresh_cat:{category_id}")
        keyboard.add(button)
        bot.send_message(chat_id, "🎉 Великолепно! Вы изучили все слова в данной категории.", parse_mode = "Markdown", reply_markup = keyboard)

def add_custom_word(chat_id):
    msg = bot.send_message(chat_id, "📩 Send me english word", parse_mode="Markdown")

    bot.register_next_step_handler(msg, add_custom_word_2)

def add_custom_word_2(msg):
    msg_2 = bot.send_message(msg.chat.id, "📩 Отправьте мне перевод слова на русском языке", parse_mode="Markdown")
    bot.register_next_step_handler(msg_2, add_custom_word_3, msg.text)

def add_custom_word_3(msg, en_word):
    word_id = Vocabulary.add_word(en_word, msg.text, 3)
    user_word_id = UserWord.add_word(msg.chat.id, word_id)
    UserWordStatus.add_word(user_word_id, 3)
    add_words_for_user(msg.chat.id, '3')


# callback_data_handler
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
        act,data = call.data.split(":")

        if act == "category":
            if "choose" in data:
                nomatter,category_id = data.split(";")
                add_words_for_user(call.message.chat.id, category_id)

        if act == "answer":
            word_id, ans_word_id, category_id = data.split(";")
            if word_id == ans_word_id:
                if UserWordStatus.get_status_of_word(call.message.chat.id, word_id) != 3:
                    bot.send_message(call.message.chat.id, "🤷 Вы уже отвечали на этот вопрос, продолжите ваше обучение:", parse_mode = "Markdown")
                else:
                    UserWordStatus.set_status_word(call.message.chat.id, word_id, 4)
                study_category(call.message.chat.id, category_id)
            else:
                bot.send_message(call.message.chat.id, "🙅🏻 Неправильный ответ, попробуйте снова.", parse_mode = "Markdown")
                study_category(call.message.chat.id, category_id)
        
        if act == "refresh_cat":
            UserWordStatus.set_status_for_all_cat(call.message.chat.id, data, 3)
            study_category(call.message.chat.id, data)

        if act == "skip":
            word_id, category_id = data.split(';')
            UserWordStatus.set_status_word(call.message.chat.id, word_id, 5)
            study_category(call.message.chat.id, category_id)

        if act == "delete":
            word_id, category_id = data.split(';')
            UserWordStatus.delete_word(call.message.chat.id, word_id)
            UserWord.delete_word(call.message.chat.id, word_id)
            study_category(call.message.chat.id, category_id)
        
        if act == "addword":
            add_custom_word(call.message.chat.id)
                
# command_handler
@bot.message_handler(commands=['start'])
def start(message):
    check = User.check_user(message.chat.id)
    if not check:
        User.add_user(message.chat.id)
        UserStatus.set_status(1,message.chat.id)
        keyboard_mm = types.ReplyKeyboardMarkup(resize_keyboard=True)
        key1 = types.InlineKeyboardButton(Command.choose_category)
        key2 = types.InlineKeyboardButton(Command.bot_about)
        key3 = types.InlineKeyboardButton(Command.word_add)
        keyboard_mm.add(key1,key2)
        keyboard_mm.add(key3)
        bot.send_message(message.chat.id, bot_about_msg, reply_markup=keyboard_mm, parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, bot_about_msg, parse_mode="Markdown")

@bot.message_handler(commands=['create_tables'])
def create_tables(message):
    if message.chat.id in settings.admin_chat_id:
        BdInstruments.create_tables()
        bot.send_message(message.chat.id, "🆗 Таблицы созданы", parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, "😬 Не балуйся!", parse_mode="Markdown")

@bot.message_handler(commands=['drop_tables'])
def create_tables(message):
    if message.chat.id in settings.admin_chat_id:
        BdInstruments.drop_tables()
        bot.send_message(message.chat.id, "🆗 Таблицы удалены", parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, "😬 Не балуйся!", parse_mode="Markdown")

@bot.message_handler(commands=['add_data_to_bd'])
def create_tables(message):
    if message.chat.id in settings.admin_chat_id:
        BdInstruments.data_add()
        bot.send_message(message.chat.id, "🆗 Данные добавлены", parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, "😬 Не балуйся!", parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == Command.choose_category)
def choose_category(message):
    categories = CategoryName.categories_get()
    keyboard = types.InlineKeyboardMarkup()
    buttons = []
    for cat in categories:
        button = types.InlineKeyboardButton(text=cat.name, callback_data=f"category:choose;{str(cat.id)}")
        buttons.append(button)
    keyboard.add(*buttons)
    bot.send_message(message.chat.id, "🗳 Выберите категорию слов", reply_markup=keyboard, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == Command.word_add)
def choose_category(message):
    bot.send_message(message.chat.id, "☝🏻 Новые слова будут доступны в категории users\\_words", parse_mode="Markdown")
    add_custom_word(message.chat.id)

@bot.message_handler(func=lambda message: message.text == Command.bot_about)
def choose_category(message):
    add_custom_word(message.chat.id)

@bot.message_handler(func=lambda message: True, content_types=['text'])
def start(message):
    keyboard_mm = types.ReplyKeyboardMarkup(resize_keyboard=True)
    key1 = types.InlineKeyboardButton(Command.choose_category)
    key2 = types.InlineKeyboardButton(Command.bot_about)
    key3 = types.InlineKeyboardButton(Command.word_add)
    keyboard_mm.add(key1,key2)
    keyboard_mm.add(key3)
    bot.send_message(message.chat.id, "Не знаю что ответить на это😜", reply_markup=keyboard_mm, parse_mode="Markdown")


bot.infinity_polling(skip_pending=True)