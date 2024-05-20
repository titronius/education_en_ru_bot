import sqlalchemy as sq
import json
import settings
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()

class User(Base):
    __tablename__ = "user"

    id = sq.Column(sq.Integer, primary_key=True)
    chat_id = sq.Column(sq.Integer, unique=True, nullable=False)

    def add_user(chat_id):
        user = User(chat_id = chat_id)
        session = BdInstruments.get_session()
        session.add(user)
        session.commit()

    def check_user(chat_id):
        session = BdInstruments.get_session()
        q = session.query(User).filter(User.chat_id == chat_id)
        if q.one_or_none():
            return q.one_or_none().id
        else:
            return False

class Vocabulary(Base):
    __tablename__ = "vocabulary"

    id = sq.Column(sq.Integer, primary_key=True)
    category_id = sq.Column(sq.String(length=120), nullable=False)
    en = sq.Column(sq.String(length=120), nullable=False)
    ru = sq.Column(sq.String(length=120), nullable=False)

    def get_words(category_id):
        session = BdInstruments.get_session()
        q = session.query(Vocabulary).filter(Vocabulary.category_id == category_id).limit(settings.word_limit)
        return q.all()
    
    def get_word(word_id):
        session = BdInstruments.get_session()
        q = session.query(Vocabulary).filter(Vocabulary.id == word_id)
        return q.one()
    
    def get_wrong_words(word_id, category_id):
        session = BdInstruments.get_session()
        q = session.query(Vocabulary).filter(Vocabulary.id != word_id, Vocabulary.category_id == category_id)
        return q.all()
    
    def add_word(en_word, ru_word, category_id):
        session = BdInstruments.get_session()
        word = Vocabulary(category_id = category_id, en = en_word, ru = ru_word)
        session.add(word)
        session.commit()

        return word.id

class StatusName(Base):
    __tablename__ = "status_name"

    id = sq.Column(sq.Integer, primary_key=True)
    name = sq.Column(sq.String(length=120), nullable=False)

class CategoryName(Base):
    __tablename__ = "category_name"

    id = sq.Column(sq.Integer, primary_key=True)
    name = sq.Column(sq.String(length=120), nullable=False)

    def get_category(category_id):
        session = BdInstruments.get_session()
        q = session.query(CategoryName).filter(CategoryName.id == category_id)
        return q.one()

    def categories_get():
        session = BdInstruments.get_session()
        q = session.query(CategoryName)
        return q.all()

class UserStatus(Base):
    __tablename__ = "user_status"

    id = sq.Column(sq.Integer, primary_key=True)
    user_id = sq.Column(sq.Integer, sq.ForeignKey("user.id"), nullable=False)
    status_id = sq.Column(sq.Integer, sq.ForeignKey("status_name.id"), nullable=False)
    category_id = sq.Column(sq.Integer, sq.ForeignKey("category_name.id"), nullable=True)

    user = relationship(User, backref="user_status")
    status_name = relationship(StatusName, backref="user_status")
    category_name = relationship(CategoryName, backref="user_status")

    def set_status(status_id,chat_id, category_id = None):
        user_id = User.check_user(chat_id)
        user_status = UserStatus(user_id = user_id, status_id = status_id, category_id = category_id)
        session = BdInstruments.get_session()
        session.add(user_status)
        session.commit()


class UserWord(Base):
    __tablename__ = "user_word"

    id = sq.Column(sq.Integer, primary_key=True)
    user_id = sq.Column(sq.Integer, sq.ForeignKey("user.id"), nullable=False)
    word_id = sq.Column(sq.Integer, sq.ForeignKey("vocabulary.id"), nullable=False)

    user = relationship(User, backref="user_word")
    vocabulary = relationship(Vocabulary, backref="user_word")

    def add_words_for_user(chat_id, category_id):
        user_id = User.check_user(chat_id)
        words = Vocabulary.get_words(category_id)
        session = BdInstruments.get_session()
        for word in words:
            user_word = UserWord(user_id = user_id, word_id = word.id)
            session.add(user_word)
            session.commit()
            UserWordStatus.add_word(user_word.id, 3)
        return len(words)

    def get_words_for_category(chat_id, category_id, status_id, limit = None):
        session = BdInstruments.get_session()
        q = session.query(UserWord).join(UserWord.vocabulary).join(UserWord.user)\
            .join(UserWordStatus)\
            .filter(User.chat_id == chat_id, Vocabulary.category_id == category_id, UserWordStatus.status_id == status_id)
        if limit:
            q = q.limit(limit)
        if limit == 1:
            return q.one_or_none()
        else:
            return q.all()
    
    def delete_word(chat_id, word_id):
        session = BdInstruments.get_session()
        session.query(UserWord).filter(UserWord.id == word_id).delete()
        session.commit()
        
    def get_user_word_id(user_id, word_id):
        session = BdInstruments.get_session()
        q = session.query(UserWord).filter(UserWord.user_id == user_id, UserWord.word_id == word_id)
        return q.one().id
    
    def add_word(chat_id, word_id):
        session = BdInstruments.get_session()
        user_id = User.check_user(chat_id)
        user_word = UserWord(user_id = user_id, word_id = word_id)
        session.add(user_word)
        session.commit()

        return user_word.id


class UserWordStatus(Base):
    __tablename__ = "user_word_status"

    id = sq.Column(sq.Integer, primary_key=True)
    user_word_id = sq.Column(sq.Integer, sq.ForeignKey("user_word.id"), nullable=False)
    status_id = sq.Column(sq.Integer, sq.ForeignKey("status_name.id"), nullable=False)

    status_name = relationship(StatusName, backref="user_word_status")
    user_word = relationship(UserWord, backref="user_word_status")

    def add_word(word_id, status_id):
        session = BdInstruments.get_session()
        user_word_status = UserWordStatus(user_word_id = word_id, status_id = status_id)
        session.add(user_word_status)
        session.commit()

    def get_status_for_cat(chat_id,category_id):
        session = BdInstruments.get_session()
        q = session.query(UserWordStatus).join(UserWordStatus.user_word)\
            .join(UserWord.vocabulary).join(UserWord.user)\
            .filter(Vocabulary.category_id == category_id, User.chat_id == chat_id)
        return q.all()
    
    def set_status_word(chat_id, word_id, status_id):
        session = BdInstruments.get_session()
        user_id = User.check_user(chat_id)
        user_word_id = UserWord.get_user_word_id(user_id, word_id)
        session.query(UserWordStatus).filter(UserWordStatus.user_word_id == user_word_id).update({"status_id": status_id})
        session.commit()

    def set_status_for_all_cat(chat_id, category_id, status_id):
        session = BdInstruments.get_session()
        q = session.query(Vocabulary).join(UserWord.vocabulary).join(UserWord.user)\
            .filter(Vocabulary.category_id == category_id, User.chat_id == chat_id)
        words = q.all()
        for word in words:
            UserWordStatus.set_status_word(chat_id, word.id, status_id)

    def get_status_of_word(chat_id, word_id):
        session = BdInstruments.get_session()
        user_id = User.check_user(chat_id)
        user_word_id = UserWord.get_user_word_id(user_id, word_id)
        q = session.query(UserWordStatus).filter(UserWordStatus.user_word_id == user_word_id)
        return q.one().status_id
    
    def delete_word(chat_id, word_id):
        session = BdInstruments.get_session()
        session.query(UserWordStatus).filter(UserWordStatus.user_word_id == word_id).delete()
        session.commit()

class BdInstruments():
    engine = sq.create_engine(settings.DSN, pool_size=40, max_overflow=0)
    def get_session():
        Session = sessionmaker(bind=BdInstruments.engine)
        session = Session()
        return session
    
    def create_tables():
        Base.metadata.create_all(BdInstruments.engine)

    def drop_tables():
        Base.metadata.drop_all(BdInstruments.engine)

    def data_add():
        session = BdInstruments.get_session()
        with open('/var/bots/education_en_ru_bot/data_for_bd/data.json', 'r') as fd:
            data = json.load(fd)

        for record in data:
            model = {
                'vocabulary': Vocabulary,
                'category_name': CategoryName,
                'status_name': StatusName
            }[record.get('model')]
            session.add(model(**record.get('fields')))
        session.commit()
