import random
import json
import pickle
import numpy as np

import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from string import punctuation
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('stopwords')

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Activation, Dropout
from tensorflow.keras.optimizers import SGD

lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('french'))

#  Prétraitement du texte
def preprocess_text(text):

    tokens = word_tokenize(text.lower())
    
    tokens = [token for token in tokens if token not in punctuation and token not in stop_words]
    
    tokens = [lemmatizer.lemmatize(token) for token in tokens]
    
    return tokens

intents = json.loads(open("intents.json").read())

# listes de mots, de classes et de documents
words = []
classes = []
documents = []
ignore_letters = ["?", "!", ".", ","]

# Parcours de intents.json pour construire les mots, classes et documents
for intent in intents["intents"]:
    for pattern in intent["patterns"]:
        word_list = preprocess_text(pattern)
        words.extend(word_list)
        documents.append((word_list, intent["tag"]))
        if intent["tag"] not in classes:
            classes.append(intent["tag"])

words = [lemmatizer.lemmatize(word) for word in words if word not in ignore_letters]
words = sorted(set(words))

classes = sorted(set(classes))

# Sauvegarde des mots et classes dans des fichiers pickle
pickle.dump(words, open("words.pkl", "wb"))
pickle.dump(classes, open("classes.pkl", "wb"))

training = []
output_empty = [0] * len(classes)

for document in documents:
    bag = []
    word_patterns = document[0]
    word_patterns = [lemmatizer.lemmatize(word.lower()) for word in word_patterns]
    for word in words:
        bag.append(1) if word in word_patterns else bag.append(0)
    
    output_row = list(output_empty)
    output_row[classes.index(document[1])] = 1
    training.append([bag, output_row])

# Gestion des données d'entrainements
random.shuffle(training)
training = np.array(training)

train_x = list(training[:, 0])
train_y = list(training[:, 1])

# Création du modèle
model = Sequential()
model.add(Dense(128, input_shape=(len(train_x[0]), ), activation="relu"))
model.add(Dropout(0.5))
model.add(Dense(64, activation="relu"))
model.add(Dropout(0.5))
model.add(Dense(len(train_y[0]), activation="softmax"))

sgd = SGD(learning_rate=0.01, momentum=0.9, nesterov=True)
model.compile(loss="categorical_crossentropy", optimizer=sgd, metrics=["accuracy"])

hist = model.fit(np.array(train_x), np.array(train_y), epochs=200, batch_size=5, verbose=1)
model.save("chatbot_model.h5", hist)
print("Done")
