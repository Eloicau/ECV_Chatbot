import random
import json
import pickle
import numpy as np
import mysql.connector
import nltk
import re
from fuzzywuzzy import fuzz
import difflib

from nltk.stem import WordNetLemmatizer
from tensorflow.keras.models import load_model

lemmatizer = WordNetLemmatizer()
intents = json.loads(open("intents.json", encoding='utf-8').read())

words = pickle.load(open("words.pkl", "rb"))
classes = pickle.load(open("classes.pkl", "rb"))
model = load_model('chatbot_model.h5')

# Charger les données du fichier parameters.json
with open('parameters.json', 'r') as f:
    parameters = json.load(f)

# Accéder aux valeurs spécifiques
chatbot_name = parameters['chatbot_name']
description = parameters['description']

nltk.download('averaged_perceptron_tagger')
nltk.download('punkt')

def clean_up_sentence(sentence):
    sentence_words = nltk.word_tokenize(sentence)
    sentence_words = [lemmatizer.lemmatize(word.lower()) for word in sentence_words]
    return sentence_words

def bag_of_words(sentence):
    sentence_words = clean_up_sentence(sentence)
    bag = [0] * len(words)
    for w in sentence_words:
        for i, word in enumerate(words):
            if word == w:
                bag[i] = 1
    return np.array(bag)

def predict_class(sentence):
    bow = bag_of_words(sentence)
    res = model.predict(np.array([bow]))[0]
    ERROR_THRESHOLD = 0.25
    results = [[i, r] for i, r in enumerate(res) if r > ERROR_THRESHOLD]

    results.sort(key=lambda x: x[1], reverse=True)
    return_list = []
    for r in results:
        return_list.append({"intent": classes[r[0]], "probability": str(r[1])})
    return return_list

def establish_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="chatbot_V2"
    )

def get_figurine_info(figurine_name):
    connection = establish_db_connection()
    cursor = connection.cursor()

    query = "SELECT figurine.*, licence.Name FROM figurine JOIN licence ON figurine.LicenceID = licence.LicenceID WHERE figurine.Name = %s"
    values = (figurine_name,)

    cursor.execute(query, values)
    result = cursor.fetchone()

    cursor.close()
    connection.close()

    return result

def get_figurines_per_licence(licence_name):
    connection = establish_db_connection()

    cursor = connection.cursor()

    query = "SELECT Name, LicenceID FROM figurine WHERE LicenceID IN (SELECT LicenceID FROM licence WHERE Name = %s)"
    values = (licence_name,)

    cursor.execute(query, values)
    result = cursor.fetchall()

    cursor.close()
    connection.close()

    return result

def get_licence_info(licence_name):
    connection = establish_db_connection()

    cursor = connection.cursor()

    query = "SELECT licence.Name, licence.Description, COUNT(*) FROM licence JOIN figurine ON licence.LicenceID = figurine.LicenceID WHERE licence.Name = %s"
    values = (licence_name,)

    cursor.execute(query, values)
    result = cursor.fetchone()

    cursor.close()
    connection.close()

    return result

def extract_variables(message, patterns):
    variables = {}
    for pattern in patterns:
        matches = re.findall(r"\$(\w+)", pattern)
        for match in matches:
            variable_value = re.search(pattern.replace(f"${match}", r"(.+)"), message, re.IGNORECASE)
            if variable_value:
                variables[match] = variable_value.group(1).strip()
                break
        if variables:
            break

    if not variables:
        # Recherche de correspondances partielles
        message_words = clean_up_sentence(message)
        for pattern in patterns:
            pattern_words = clean_up_sentence(pattern)
            similarity = difflib.SequenceMatcher(None, message_words, pattern_words).ratio()
            if similarity >= 0.7:
                matches = re.findall(r"\$(\w+)", pattern)
                for match in matches:
                    variable_value = re.search(pattern.replace(f"${match}", r"(.+)"), message, re.IGNORECASE)
                    if variable_value:
                        variables[match] = variable_value.group(1).strip()
                        break
                if variables:
                    break

    return variables

def get_response(intents_list, intents_json, message):
    tag = intents_list[0]["intent"]
    list_of_intents = intents_json["intents"]
    for intent in list_of_intents:
        if intent["tag"] == tag:
            result = random.choice(intent["responses"])

            if tag == "figurine_info":
                extracted_variables = extract_variables(message, intent["patterns"])
                if extracted_variables:
                    figurine_name = extracted_variables.get("figurine_name")
                    figurine_info = get_figurine_info(figurine_name)
                    if figurine_info:
                        result = result.replace('$figurine_name', figurine_info[1])
                        result = result.replace('$figurine_price', str(figurine_info[3]))
                        result = result.replace('$licence_name', str(figurine_info[7]))
                        result = result.replace('$figurine_brand', figurine_info[5])
                        result = result.replace('$figurine_number', str(figurine_info[6]))
                    else:
                        result = "Je suis désolé, je n'ai pas d'informations sur ce produit."

            elif tag == "figurines_per_licence":
                extracted_variables = extract_variables(message, intent["patterns"])
                if extracted_variables:
                    licence_name = extracted_variables.get("licence_name")
                    figurines = get_figurines_per_licence(licence_name)
                    if figurines:
                        figurine_list = ", ".join([f[0] for f in figurines])
                        result = result.replace('$licence_name', str(licence_name))
                        result = result + "\n" + figurine_list
                    else:
                        result = "Je suis désolé, je n'ai pas de figurines pour cette licence."

            elif tag == "licence_info":
                extracted_variables = extract_variables(message, intent["patterns"])
                if extracted_variables:
                    licence_name = extracted_variables.get("licence_name")
                    licence_info = get_licence_info(licence_name)
                    if licence_info:
                        result = result.replace('$licence_name', licence_name)
                        result = result.replace('$licence_description', licence_info[1])
                        result = result.replace('$licence_figurines_count', str(licence_info[2]))
                    else:
                        result = "Je suis désolé, je n'ai pas d'informations sur cette licence."

            result = result.replace('$chatbot_name', chatbot_name)
            result = result.replace('$description', description)
            break
    return result

print("Go! Le chatbot est actif!")

while True:
    message = input("")
    ints = predict_class(message)
    res = get_response(ints, intents, message)
    print(res)
