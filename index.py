import os
import telebot
import pprint
import hashlib
import rsa
from dotenv import load_dotenv, find_dotenv
from pymongo import MongoClient

load_dotenv(find_dotenv())

BOT_TOKEN = os.environ.get('BOT_TOKEN')

bot = telebot.TeleBot(BOT_TOKEN)

password = os.environ.get('MONGODB_PWD')

connection_string = f"mongodb+srv://Oleksa:{password}@cluster0.bjdsloy.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(connection_string)

dbs = client.list_database_names()
accounts_db = client.Accounts
collections = accounts_db.list_collection_names()
acc_collection = accounts_db.Accounts

PUBLIC_KEY_PATH = 'public_key.pem'
PRIVATE_KEY_PATH = 'private_key.pem'

# Load or generate the encryption keys
if os.path.exists(PUBLIC_KEY_PATH) and os.path.exists(PRIVATE_KEY_PATH):
    with open(PUBLIC_KEY_PATH, 'rb') as f:
        publicKey = rsa.PublicKey.load_pkcs1(f.read())
    with open(PRIVATE_KEY_PATH, 'rb') as f:
        privateKey = rsa.PrivateKey.load_pkcs1(f.read())
else:
    (publicKey, privateKey) = rsa.newkeys(512)
    with open(PUBLIC_KEY_PATH, 'wb') as f:
        f.write(publicKey.save_pkcs1())
    with open(PRIVATE_KEY_PATH, 'wb') as f:
        f.write(privateKey.save_pkcs1())


def encrypt_text(text):
    encMessage = rsa.encrypt(text.encode(), publicKey)
    return encMessage

def decrypt_text(text):
    decMessage = rsa.decrypt(text, privateKey).decode()
    return decMessage

def insert_into_doc(user_data_doc):
    collection = accounts_db.Accounts
    inserted_id = collection.insert_one(user_data_doc).inserted_id
    
#insert_into_doc()

printer = pprint.PrettyPrinter()
def find_all_people():
    people = acc_collection.find()
    for person in people:
        printer.pprint(person)

#find_all_people()

def find_person(pib):
    results = acc_collection.find({"pib":pib})
    return results

#find_person("Andriienko Oleksa Yuriivna")

current_person = [
    ["name", " ", " "],
    ["Surname", " ", " "],
    ["patronimic", " ", " "],
    ["birthdate", " "],
    ["location", " "],
    ["gender", " "],
    ["pib", " "]
]

@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    bot.reply_to(message, "Ласкаво просимо")


def end_send(message):
    a = encrypt_text(message.text)
    current_person[5][1] = a
    current_person[6][1] = current_person[1][2] + " " + current_person[0][2] + " " + current_person[2][2]
    person_data = {
        "name" : current_person[0][1],
        "Surname" : current_person[1][1],
        "patronimic" : current_person[2][1],
        "birthdate" : current_person[3][1],
        "location" : current_person[4][1],
        "gender" : current_person[5][1],
        "pib" : current_person[6][1]
    }
    insert_into_doc(person_data)
    bot.send_message(message.chat.id, "Дані успішно додано до бази")

def gender_handler(message):
    a = encrypt_text(message.text)
    current_person[4][1] = a
    text = "Тепер введіть вашу стать"
    sent_msg = bot.send_message(
        message.chat.id, text, parse_mode="Markdown")
    bot.register_next_step_handler(sent_msg, end_send)

def location_handler(message):
    a = encrypt_text(message.text)
    current_person[3][1] = a
    text = "Тепер введіть ваше місце проживання"
    sent_msg = bot.send_message(
        message.chat.id, text, parse_mode="Markdown")
    bot.register_next_step_handler(sent_msg, gender_handler)

def date_handler(message):
    str = message.text
    result = hashlib.sha1(str.encode())
    current_person[2][2] = result.hexdigest()
    a = encrypt_text(message.text)
    current_person[2][1] = a
    text = "Тепер введіть вашу дату народження"
    sent_msg = bot.send_message(
        message.chat.id, text, parse_mode="Markdown")
    bot.register_next_step_handler(sent_msg, location_handler)

def patronimic_handler(message):
    str = message.text
    result = hashlib.sha1(str.encode())
    current_person[1][2] = result.hexdigest()
    a = encrypt_text(message.text)
    current_person[1][1] = a
    text = "Тепер введіть ваше ім'я по-батькові"
    sent_msg = bot.send_message(
        message.chat.id, text, parse_mode="Markdown")
    bot.register_next_step_handler(sent_msg, date_handler)

def surname_handler(message):
    str = message.text
    result = hashlib.sha1(str.encode())
    current_person[0][2] = result.hexdigest()
    a = encrypt_text(message.text)
    current_person[0][1] = a
    text = "Тепер введіть ваше прізвище"
    sent_msg = bot.send_message(
        message.chat.id, text, parse_mode="Markdown")
    bot.register_next_step_handler(sent_msg, patronimic_handler)

@bot.message_handler(commands=['register'])
def name_handler(message):
    text = "**Для реєстрації необхідні такі дані, як:**\n__Ваші ім'я, прізвище, по-батькові, дата народження, місце проживання, стать__\nДля початку введіть ваше ім'я"
    sent_msg = bot.send_message(message.chat.id, text, parse_mode="Markdown")
    bot.register_next_step_handler(sent_msg, surname_handler)
    
def search_handler(message):
    pib = message.text
    pib = pib.split()
    pib1 = ""
    for name in pib:
        a = hashlib.sha1(name.encode())
        b = a.hexdigest()
        pib1 = pib1 + " " + b
    results = find_person(pib1.strip())
    text = "Результати пошуку:"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")
    for result in results:
        text1 = "Прізвище: " + decrypt_text(result['Surname']) + "\n" + "Ім'я: " + decrypt_text(result['name']) + "\n" + "По-батькові: " + decrypt_text(result['patronimic']) + "\n" + "Дата народження: " + decrypt_text(result['birthdate']) + "\n" + "Стать: " + decrypt_text(result['gender']) + "\n" + "Місце проживання: " + decrypt_text(result['location']) 
        bot.send_message(message.chat.id, text1, parse_mode="Markdown")
    bot.send_message(message.chat.id, "Пошук завершено", parse_mode="Markdown")
    
@bot.message_handler(commands=['find'])
def search_text_handler(message):
    text = "Пошук можливий лише по ПІБ\nВведіть ПІБ людини, яку необхідно знайти"
    sent_msg = bot.send_message(message.chat.id, text, parse_mode="Markdown")
    bot.register_next_step_handler(sent_msg, search_handler)
bot.infinity_polling()