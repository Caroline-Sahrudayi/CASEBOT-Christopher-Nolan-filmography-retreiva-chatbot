import sqlite3
import random
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import spacy
import re
import os


# Check db
# conn = sqlite3.connect('database_final.db')
# cursor = conn.cursor()
# keyword='awards'
# results=cursor.execute("SELECT Sentence FROM keywords WHERE Keyword=?",(keyword,)).fetchall()
# print(results)
DB_filename='database_final_latest.db'
conn = sqlite3.connect(DB_filename)
cursor = conn.cursor()
NER = spacy.load("en_core_web_sm")
USER_DATA_DIR = "user_data"


def get_keywords_from_database():
    """
        Check the database for keywords.
        :return: A list of keywords found in the database
    """

    cursor.execute("SELECT DISTINCT keyword FROM keywords")
    return [row[0] for row in cursor.fetchall()]

def get_sentences_from_database(keyword):
    """
        Retrieve sentences from the database based on the provided keyword.
        :param keyword: The keyword to search for in the database
        :return: A list of sentences matching the keyword
    """
    cursor.execute("SELECT sentence FROM keywords WHERE keyword LIKE ?", (f'%{keyword}%',))
    return [row[0] for row in cursor.fetchall()]

def generate_random_response():
    """
    Generate a random response from a predefined list.
    :return: A randomly selected response
    """
    responses = [
        "I'm sorry, I didn't understand that.",
        "Could you please provide more information?",
        "Hmm, let me think about that.",
        "I'm not sure I follow. Can you rephrase?",
        "Interesting, tell me more!",
        "Let's talk about something else.",
        "I'm here to help. What can I assist you with?",
    ]
    return random.choice(responses)


def preprocess(text):
    """
        Preprocess the input text by tokenizing, lemmatizing, and removing stopwords.
        :param text: The input text to preprocess
        :return: Preprocessed text as a string
    """
    lemmatizer = WordNetLemmatizer()
    stop_words = set(stopwords.words('english'))
    tokens = word_tokenize(text.lower())
    filtered_tokens = [lemmatizer.lemmatize(token) for token in tokens if token.isalpha() and token not in stop_words]
    return ' '.join(filtered_tokens)

def calculate_cosine_similarity(user_input, sentences):
    """
        Calculate cosine similarity between the user input and sentences from the database.
        :param user_input: The user's input text
        :param sentences: List of sentences from the database
        :return: Cosine similarities as a list
    """
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([user_input] + sentences)
    cosine_similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
    return cosine_similarities

def remove_numbers_in_square_brackets(sentence):
    """
        Remove numbers within square brackets from a sentence.
        :param sentence: The sentence to process
        :return: The processed sentence
    """
    return re.sub(r'\[[0-9]+\]', '', sentence)

def respond_to_input(user_input):
    """
        Respond to user input by finding the most similar sentence from the database.
        :param user_input: The user's input text
        :return: The response based on the most similar sentence
    """
    preprocessed_input = preprocess(user_input)
    # print("preprocessed user input",preprocessed_input)
    keywords = get_keywords_from_database()
    matching_sentences = []
    try:
        # Retrieve all sentences that match each term in the user input with its corresponding keyword
        for term in preprocessed_input.split():
            if term in keywords:
                matching_sentences.extend(get_sentences_from_database(term))
        
        # Calculate cosine similarity between user input and matching sentences
        preprocessed_matching_sentences = [preprocess(sentence) for sentence in matching_sentences]
        cosine_similarities = calculate_cosine_similarity(preprocessed_input, preprocessed_matching_sentences)
        max_similarity_index = cosine_similarities.argmax()
        # print("max similarity index",max_similarity_index)
        # print("sentence with max similarity",matching_sentences[max_similarity_index])
        return remove_numbers_in_square_brackets(matching_sentences[max_similarity_index])
    except ValueError as e:
        response=generate_random_response()
        return response
    
def get_user_name(name_input_text):
    """
        Extract the user's name from the input text.
        :param name_input_text: The input text containing the user's name
        :return: The extracted name as a string
    """
    name=""
    tagged_input=NER(name_input_text)
    for item in tagged_input:
        if item.pos=="PROPN":
            name+=item.text+""
    name=name[:-1]
    return name

 
def create_user_model(user_name):
    """
        Create a user model file if it doesn't exist and provide an initial message.
        :param user_name: The user's name
        :return: A welcome message as a string
    """
    user_model_file = os.path.join(USER_DATA_DIR, f"{user_name}.txt")
    with open(user_model_file, "w") as f:
        f.write(f"Name: {user_name}\n")
    return f"CaSebot: Nice to meet you, {user_name}! As a fan bot of Nolan, I can tell you information about Christopher Nolan and his movies, famous characters, critic reviews and awards. Some of Nolan's most notable movies are Oppenheimer, Interstellar, Inception,Dark Knight Trilogy, Dunkirk, Tenet, Memento. I'd like to understand your interests first!"


def check_user_model(user_name):
    """
        Check if a user model file exists for the given user name.
        :param user_name: The user's name
        :return: 1 if the user model exists, -1 otherwise
    """
    user_model_file = os.path.join(USER_DATA_DIR, f"{user_name}.txt")
    if os.path.exists(user_model_file):
        return 1
    else:
        return -1
    
def update_user_information(user_name, key, value):
    """
        Update user information in the user model file.
        :param user_name: The user's name
        :param key: The key to update
        :param value: The value to update
    """
    user_model_file = os.path.join(USER_DATA_DIR, f"{user_name}.txt")
    with open(user_model_file, "a") as f:
        f.write(f"{key}: {value}\n")


def get_personalized_remark(user_name):
    """
        Provide a personalized remark based on the user's name and preferences.
        :param user_name: The user's name
        :return: A personalized remark as a string
    """
    user_model_file = os.path.join(USER_DATA_DIR, f"{user_name}.txt")
    likes = []
    with open(user_model_file, "r") as f:
        for line in f:
            if line.startswith("Likes:"):
                likes = line.strip().split(": ")[1].split(", ")
    if likes:
        return f"CaSebot: I see that you like {', '.join(likes)}. I can tell you more about nolan, his movies, awards and critic reviews. Ask away!"
    else:
        return f"CaSebot: As a fan bot of Nolan, I can tell you information about Christopher Nolan and his movies, famous characters, critic reviews and awards. Some of Nolan's most notable movies are Oppenheimer, Interstellar, Inception,Dark Knight Trilogy, Dunkirk, Tenet, Memento. Tell me what you'd like to know? (Make sure to use the correct spelling of relevant keywords in your input)"


def get_rule_based_response(key):
    """
        Provide a rule-based response based on the given key.
        :param key: The key to retrieve the response
        :return: The rule-based response as a string
    """
    responses_dict={'nolan_age':'Christopher Edward Nolan is 53 years','nolan':' Christopher Edward Nolan CBE (born 30 July 1970) is a British and American filmmaker. He gained widespread recognition for directing blockbusters like "Oppenheimer","Interstellar","Inception,"  and "The Dark Knight Trilogy". Nolan\'s work often explores themes of time, identity, and morality, earning him critical acclaim and a dedicated fanbase.','oppenheimer':'Oppenheimer is a 2023 epic biographical thriller film written, directed, and co-produced by Christopher Nolan, starring Cillian Murphy as J. Robert Oppenheimer, the American theoretical physicist credited with being the "father of the atomic bomb" for his role in the Manhattan Project—the World War II undertaking that developed the first nuclear weapons.','interstellar':'  Interstellar is a 2014 epic science fiction film co-written, directed, and produced by Christopher Nolan.','inception':'Inception is a 2010 science fiction action film written and directed by Christopher Nolan, who also produced the film with Emma Thomas, his wife.','dark_knight_trilogy':'The Dark Knight trilogy consists of Batman Begins (2005), The Dark Knight (2008), and The Dark Knight Rises (2012), all directed by Christopher Nolan.','batman':' Batman Begins is a 2005 superhero film directed by Christopher Nolan and written by Nolan and David S. Goyer., created by Bill Finger and Bob Kane','dunkirk':' Dunkirk is a 2017 epic historical war thriller film written, directed and co-produced by Christopher Nolan that depicts the Dunkirk evacuation of World War II from the perspectives of the land, sea and air.','tenet':'  Tenet is a 2020 science fiction action thriller film written and directed by Christopher Nolan, who also produced it with his wife Emma Thomas.','memento':'  Memento is a 2000 American neo-noir mystery psychological thriller film written and directed by Christopher Nolan, based on the short story "Memento Mori" by his brother Jonathan Nolan, which was later published in 2001.'}
    return responses_dict[key]


if __name__ == '__main__':
    """
        Main function to interact with the user and handle responses.
    """
    wh_nolan_age_pattern=r"\bhow old( is)?( christopher)? nolan\b\?"
    wh_nolan_pattern=r"\b(?:can you|tell me( more)?)\b.*\bnolan\b"
    wh_oppenheimer_pattern=r"\b(?:can you|tell me( more)?)\b.*\boppenheimer\b"
    wh_interstellar_pattern=r"\b(?:can you|tell me( more)?)\b.*\binterstellar\b"
    wh_inception_pattern=r"\b(?:can you|tell me( more)?)\b.*\binception\b"
    wh_dark_knight_trilogy_pattern=r"\b(?:can you|tell me( more)?)\b.*\bdark knight\b"
    wh_dunkirk_pattern=r"\b(?:can you|tell me( more)?)\b.*\bdunkirk\b"
    wh_tenet_pattern=r"\b(?:can you|tell me( more)?)\b.*\btenet\b"
    wh_memento_pattern=r"\b(?:can you|tell me( more)?)\b.*\bmemento\b"
    # wh_batman_pattern=r"\b(?:can you|tell me( more)?)\b.*\bbatman\b"
        

    print("CaSebot: Hello! I'm CaSe, a Christopher Nolan fan bot!")
    print("CaSebot: Can you tell me your name?")
    user_name_input=input()
    name_result=get_user_name(user_name_input)
    if name_result == "":
        print("CaSebot: I'm unable to get your name from your input. Can you please tell me your name and just enter your name by itself?")
        name_result=input()
    #check if name already exists, if not create an entry
    check=check_user_model(name_result)
    if check ==1:
        print(f"CaSebot: Welcome back, {name_result}!" )
    elif check==-1:
        welcome_message=create_user_model(name_result)
        print(welcome_message)
        likes = input("CaSebot: What are the topics you like from the information I can provide? (Enter as comma-separated list): ").split(",")
        update_user_information(name_result, "Likes", ", ".join([like.strip() for like in likes]))
    
        # Update user's dislikes
        dislikes = input("CaSebot: What are the topics you dislike from the information I can provide? (Enter as comma-separated list) ").split(",")
        update_user_information(name_result, "Dislikes", ", ".join([dislike.strip() for dislike in dislikes]))
    print(get_personalized_remark(name_result))    

    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            break
        elif re.search(wh_nolan_pattern,user_input.lower()):
            response=get_rule_based_response('nolan')
            print("CaSebot:", response)
        elif re.search(wh_nolan_age_pattern,user_input.lower()):
            response=get_rule_based_response('nolan_age')
            print("CaSebot:", response)
        elif re.search(wh_oppenheimer_pattern,user_input.lower()):
            response=get_rule_based_response('oppenheimer')
            print("CaSebot:", response)
        elif re.search(wh_interstellar_pattern,user_input.lower()):
            response=get_rule_based_response('interstellar')
            print("CaSebot:", response)
        elif re.search(wh_inception_pattern,user_input.lower()):
            response=get_rule_based_response('inception')
            print("CaSebot:", response)
        elif re.search(wh_dark_knight_trilogy_pattern,user_input.lower()):
            response=get_rule_based_response('dark_knight_trilogy')
            print("CaSebot:", response)
        elif re.search(wh_dunkirk_pattern,user_input.lower()):
            response=get_rule_based_response('dunkirk')
            print("CaSebot:", response)
        elif re.search(wh_tenet_pattern,user_input.lower()):
            response=get_rule_based_response('tenet')
            print("CaSebot:", response)
        elif re.search(wh_memento_pattern,user_input.lower()):
            response=get_rule_based_response('memento')
            print("CaSebot:", response)
        # elif re.search(wh_batman_pattern,user_input.lower()):
        #     response=get_rule_based_response('batman')
        #     print("CaSebot:", response)
        
        else:
            response = respond_to_input(user_input)
            print("CaSebot:", response)