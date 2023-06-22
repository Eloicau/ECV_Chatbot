from nltk.chat.util import Chat, reflections

# Définir les paires de questions et réponses
pairs = [
    ["Mon nom est (.*)", ["Bonjour %1, comment allez-vous ?",]],
    ["(Quel est votre nom ?|Comment vous appelez-vous ?)", ["Je m'appelle Chatbot et je suis un chatbot.",]],
    ["(bonjour|salut|coucou|slt|cc)", ["Salut", "Bonjour", "Coucou",]],
    ["(comment allez-vous ?|comment vas-tu ?|comment ça va ?)", ["Je vais bien, et vous ?",]],
    ["(bien|très bien|super|cool|génial)", ["Je suis content pour vous",]],
    ["(mal|pas bien|pas super|pas cool|pas génial)", ["Je suis désolé pour vous",]],
    ["(merci|merci beaucoup|merci bcp)", ["De rien", "Je vous en prie",]],
    ["(au revoir|bye|ciao|a+|à plus|à +)", ["Au revoir", "A bientôt", "A la prochaine",]],
    ["Je suis Thomas", ["Le giga Bg ?? Je suis un grand fan !",]]
]

# Créer un objet Chat
chat = Chat(pairs, reflections)
chat.converse()