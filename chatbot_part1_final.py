import pickle
import sqlite3
from bs4 import BeautifulSoup
import re
import requests
from urllib import request
import nltk
from nltk import sent_tokenize
from nltk import word_tokenize
from collections import deque

pickle_file = "filemap_nolan_final1.pickle"
robot_checks = False
robots_files_check = {}
banned_base_urls = ['facebook.com', 'twitter.com', 'instagram.com']

def check_robotstxt(url):
    """
    Check the robots.txt file for the given URL.
    :param url: URL to check for robots.txt
    :return: True if access is allowed, False otherwise
    """
    # Extract base URL

    match = re.search("^(https?://[^/]+)/.*$", url)
    if not match:
        match = re.search("^(https?://[^/]+)$", url)
    if not match:
        print("regex parse failed: '", url, "'")
        return False
    url_base = match.group(1)
    if url_base not in robots_files_check:
        r = requests.get(url_base + "/robots.txt")
        robots_files_check[url_base] = r.text
    else:
        print("robots.txt retrieved.")


    print(robots_files_check[url_base])
    print("robots.txt for url /"", url_base, " / "")
    print("base url /"", url, " / "")
    while True:
        user_in = input("Approve? y\n")
        if user_in == "y":
            return True
        if user_in == "n":
            return False
        print("'{0}' input not identified".format(user_in))



def get_raw_text(scrape_url, output_filename):
    """
    Scrape raw text content from the given URL and save it to a file.
    :param scrape_url: URL to scrape
    :param output_filename: Filename to save the scraped content
    :return: Raw text content scraped from the URL
    """

    # Perform robots.txt check if enabled   
    if robot_checks:
        if not check_robotstxt(scrape_url):
            return "NONE"
    # Request the HTML content from the URL
    try:
        html = request.urlopen(scrape_url).read().decode('utf8')
    except:
        print('Ran into Error requesting ' + scrape_url)
        raise Exception('Request error')

    soup = BeautifulSoup(html, features='html.parser')

    for script in soup(["script", "style"]):
        script.extract()
    # Extract text from paragraph tags

    paragraphs = soup.select('p')
    p_text = [p.text for p in paragraphs]
    raw_text = '\n'.join(p_text)
    # Save scraped content to a file
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(scrape_url + '\n')
        f.write(raw_text)

    return raw_text


def get_clean_text(input_filename, output_filename):
    """
    Clean raw text content and save it to a new file.
    :param input_filename: Filename containing raw text content
    :param output_filename: Filename to save the cleaned text content
    :return:
    """

    # Read raw text content from the input file

    with open(input_filename, 'r', encoding='utf-8') as f:

        url = f.readline()
        raw_lines = f.readlines()
    # Strip whitespace and remove empty lines and numeric references

    raw_lines = [line.strip() for line in raw_lines if not re.match(r'^/s*$', line)]
    raw_lines=[re.sub(r'\[[0-9]+\]', '', line) for line in raw_lines]

    cleaned_text = ' '.join(raw_lines)
    sentences = sent_tokenize(cleaned_text)

    with open(output_filename, 'w', encoding='utf-8') as f:

        f.write(url + '\n')

        for sentence in sentences:
            f.write(sentence + '\n')


def tf_ids(filename_list):
    """
    Calculate the TF-IDF scores for each term in the given list of files.
    :param filename_list: List of filenames to process
    :return: List of terms sorted by TF-IDF score
    """

    stopwords = nltk.corpus.stopwords.words('english')
    dict_of_dict = {}

   
    for filename in filename_list:
        counts_dict = {}

        with open(filename, 'r', encoding='utf-8') as f:
            u = f.readline()
            text = f.read().lower().replace('\n', ' ')

        tokens = word_tokenize(text)
        tokens = [t for t in tokens if t.isalpha() and t not in stopwords]
        for t in tokens:
            if t in counts_dict:
                counts_dict[t] += 1
            else:
                counts_dict[t] = 1

        dict_of_dict[filename] = counts_dict

    if_dict_dict = {}
    for filename in dict_of_dict:
        total = 0
        for word in dict_of_dict[filename]:
            total += dict_of_dict[filename][word]
        if_dict = {}
        for word in dict_of_dict[filename]:
            if_dict[word] = dict_of_dict[filename][word] / total
        if_dict_dict[filename] = if_dict

    if_total_dict = {}
    for filename in if_dict_dict:
        for word in if_dict_dict[filename]:
            if word in if_total_dict:
                if_total_dict[word] += if_dict_dict[filename][word]
            else:
                if_total_dict[word] = if_dict_dict[filename][word]

    word_doc_count = {}
    for instance in if_dict_dict:
        for word in if_dict_dict[instance]:
            if word in word_doc_count:
                word_doc_count[word] += 1
            else:
                word_doc_count[word] = 1
    doc_count = len(if_dict_dict)
    idf = {}
    for word in word_doc_count:
        idf[word] = doc_count / word_doc_count[word]

    if_ids_dict = {}
    for word in idf:
        if_ids_dict[word] = idf[word] * if_total_dict[word]

    occurrences = sorted(if_ids_dict.items(), key=lambda x: x[1], reverse=True)
    for i, occurrence in enumerate(occurrences[:25]):
        print(str(i + 1) + ': ' + str(occurrence))

    return [occurrence[0] for occurrence in occurrences]


def get_tfidf(files):
    """
    Calculate the TF-IDF scores for each term in the given list of files.
    :param files: List of filenames to process
    :return: List of top 150 terms sorted by term frequency
    """
    stopwords = nltk.corpus.stopwords.words('english')
    non_keywords = ['jonathan','original','scenes','american','script','television','first','city','war','murphy','next','office','year','three','another','box','wanted','characters','wrote','july','effects','united','decade','gave','around','sound','los','seen','place','third','weekend','mm','much','tv','life','part','behind','day','opening','last','something','since','see','four','films','took','look','new','would','also', 'said', 'like', 'privacy', 'policy','coo' 'terms', 'one', 'use', 'information','million','best','new','released','made','warner','people','two','series','work','imax','years','many','way','man','black','could','used','us','make','well','received','including','making','second','get','based','even','later','shot']
    # stopwords=list(stopwords).extend(['also','said','like','privacy','policy','terms','one'])
    counts_dict = {}

    for item in files:
        with open(item, 'r', encoding='utf-8') as f:
            u = f.readline()
            text = f.read().lower().replace('\n', ' ')

        tokens = word_tokenize(text)
        # tags=nltk.pos_tag(tokens)
        tokens = [t for t in tokens if t.isalpha() and t not in stopwords and t not in non_keywords]
        for t in tokens:
            if t in counts_dict:
                counts_dict[t] += 1
            else:
                counts_dict[t] = 1

    counts = sorted(counts_dict.items(), key=lambda x: x[1], reverse=True)
    print('Most frequent words by count')
    for i, word in enumerate(counts[:150]):
        print(str(i + 1) + ': ' + str(word))

    return [count[0] for count in counts]


def create_database(db_name, files, keyword_list):
    """
    Create an SQLite database containing relevant sentences and keywords.
    :param db_name: Name of the database file
    :param files: List of files containing cleaned text content
    :param keyword_list: List of keywords identifying relevant sentences
    :return:
    """
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    connection.execute("PRAGMA foreign_keys = 1")
    cursor.execute("DROP TABLE IF EXISTS keywords")
    cursor.execute("DROP TABLE IF EXISTS facts")
    connection.commit()
    # Create tables for storing facts (sentences,URLS) and keywords(sentence,keyword)

    cursor.execute("CREATE TABLE IF NOT EXISTS facts ( "
                   "sentence TEXT NOT NULL, "
                   "source TEXT, "
                   "PRIMARY KEY (sentence))")
    cursor.execute("CREATE TABLE IF NOT EXISTS keywords ("
                   "sentence TEXT NOT NULL, "
                   "keyword TEXT NOT NULL, "
                   "FOREIGN KEY (sentence) REFERENCES facts(sentence) ON DELETE CASCADE)")
    connection.commit()


    for file_from_set in files:
        f = open(file_from_set, 'r', encoding='utf-8')
        url = f.readline()
        lines = f.readlines()
        f.close()

        for line in lines:
            for keyword in keyword_list:
                if keyword.lower() in line.lower():
                    query = cursor.execute("SELECT * FROM facts WHERE sentence=?", (line,)).fetchall()
                    if not query:
                        cursor.execute("INSERT INTO facts VALUES (?, ?)", (line, url,))
                        connection.commit()
                    cursor.execute("INSERT INTO keywords VALUES (?, ?)", (line, keyword))
                    connection.commit()

    cursor.close()
    connection.close()


def getfilesdict(url_list):
    """
    Create a dictionary of URL to file mappings.
    :param url_list: List of URLs to scrape and generate files
    :return: Dictionary mapping URLs to their corresponding file names
    """
    url_files_dict = {}

    count = 0
    for url in url_list:
        print("URL", url)
        raw_filename = 'raw_text_' + str(count) + '.txt'
        clean_filename = 'clean_text' + str(count) + '.txt'

        try:
            if get_raw_text(url, raw_filename) == "NONE":
                print("Scraping failed for {}.".format(url))
                continue
            get_clean_text(raw_filename, clean_filename)
        except:
            continue

        url_files_dict[url] = (raw_filename, clean_filename)
        count += 1

    return url_files_dict

def has_keywords(text, keyword_list):
    """
    Check if the given text contains any of the specified keywords.
    :param text: Text to search for keywords
    :param keyword_list: List of keywords to search for
    :return: True if any keyword is found in the text, False otherwise
    """
    for key in keyword_list:
        if text and key in text.lower():
            return True
    return False

def not_banned_url(url,check):
    match = re.search("^https?:(//[^/]+)/.*$", url)

    if not match:
        match = re.search("^https?:(//[^/]+)$", url)

    if not match:
        if not check:
            print("Rejected url as base address not found for {0}".format(url))
        return False


    base_url = match.group(1)

    if base_url in banned_base_urls:
        if not check:
            print("Rejected url {0}".format(url))
        return False
    return True
def collect_urls(starting_url, keyword_list, filters):
    """
    Collect URLs from the given starting URL based on keywords and filters.
    :param starting_url: Starting URL to collect URLs from
    :param keyword_list: List of keywords to filter URLs
    :param filters: List of keywords to filter out URLs
    :return: List of collected URLs
    """

    try:
        r = requests.get(starting_url)
        data = r.text
        soup = BeautifulSoup(data, features='html.parser')
        url_list = []
        for link in soup.find_all('a'):
            url = link.get('href')
            url_list.append(url)

        
        url_list = list(set(url_list))

       
        if len(keyword_list) > 0:
            url_list = [url for url in url_list if has_keywords(url, keyword_list)]

      
        if len(filters) > 0:
            url_list = [url for url in url_list if not has_keywords(url, filters)]
        url_list=[url for url in url_list if not_banned_url(url,False)]

        print('URLs gathered')
        with open('crawl_Final_urls_2_latest.txt', 'a') as f:
            print("Gathered URLs for",starting_url)
            f.write('Starting URL:'+str(starting_url) + '\n')
            f.write('-----------------------------------'+'\n')
            for unique_url in url_list:
                print(unique_url)
                f.write(str(unique_url) + '\n')
            return url_list
    except requests.exceptions.ConnectionError as e:
        print("Connection error occured",e)



def get_wiki_urls(start_url):
    """
    Collect relevant URLs from the given Wikipedia starting URL within the starting domain .
    :param start_url: Wikipedia starting URL
    :return: List of collected Wikipedia URLs
    """
    filter_words_positive = ['christopher nolan','imdb']
    movies_keywords=['following','memento','insomnia','batman begins','the prestige','the dark knight','inception','the dark knight rises','interstellar','dunkirk','tenet','oppenheimer',"batman","knight"]
    filter_words_negative = ['robert','steven','wikimedia','archive','interview','avclub','pictures','twitter','reddit','linkedin','flipboard','facebook','pinterest','wikiquote','tumblr','.jpg','whatsapp','api','guardian','.pdf','.fr','#comments','robert oppenheimer','robert']
    wiki_keywords=['/wiki']

    url_list=[]
    try:
        r = requests.get(start_url)
        data = r.text   
        soup = BeautifulSoup(data, features='html.parser')

 
        for link in soup.find_all('a'):
            #print(soup.find_all('a'))
            url = link.get('href')
            url_list.append(url)

        
        url_list = list(set(url_list))
        print("url_list",url_list)
        url_list1=[]
        for url in url_list:
            if has_keywords(url,wiki_keywords):
                if has_keywords(url, movies_keywords):
                    print("wiki url",url)
                    url_list1.append(url)
        url_list1 = [url for url in url_list1 if not has_keywords(url, filter_words_negative)]
        # Only save urls that have one of the keywords
        with open('wikipedia_scrape_test_urls.txt','w') as f:
            for url in url_list1:
                f.write("https://en.wikipedia.org"+str(url) + '\n')
    except requests.exceptions.ConnectionError as e:
        print(e,"A connection error occurred")


def crawl(url, filter_pos, filter_neg):
    """
    Crawl URLs from the starting URL based on positive and negative filters.
    :param url: Starting URL to crawl from
    :param filter_pos: List of positive filters (keywords)
    :param filter_neg: List of negative filters (keywords)
    :return: List of collected URLs
    """

    try:
        url_queue = deque([url])
        visited_urls = set()
        collected_urls = []

        while len(collected_urls) < 25 and url_queue:
            current_url = url_queue.popleft()
            if current_url in visited_urls:
                continue

            scraped_urls = collect_urls(current_url, filter_pos, filter_neg)

            # Check if scraped_urls is None to handle ConnectionError
            if scraped_urls is None:
                print("Error occurred while scraping URLs. Returning an empty list.")
                return []

            url_queue.extend(scraped_urls)

            collected_urls.append(current_url)

            visited_urls.add(current_url)

            if len(collected_urls) == 25:
                break

        return collected_urls
    except Exception as e:
        print("An error occurred during URL crawling:", e)
        return []




if __name__ == '__main__':
    """
    Entry point for the web crawler.
    """
    urls_files_dict={}
    print("Starting the web crawler")
    start_url = 'https://en.wikipedia.org/wiki/Christopher_Nolan'
    # Define the starting URL and collect Wikipedia URLs related to Christopher Nolan
    wiki_urls=get_wiki_urls(start_url)
    # Define positive and negative filters for URL collection
    filter_words_positive_crawler = ["christopher nolan","christopher","nolan","biography",'following','memento','insomnia','batman begins','the prestige','the dark knight','inception','the dark knight rises','interstellar','dunkirk','tenet','oppenheimer',"batman","knight"]
    filter_words_negative_crawler = ['wikimedia', 'wikipedia', 'archive', 'interview', 'avclub', 'pictures', 'twitter','reddit', 'linkedin', 'flipboard', 'facebook', 'pinterest', 'wikiquote', 'tumblr', '.jpg', 'whatsapp', 'api', 'guardian', '.pdf', '.fr', '#comments',"jonathan"]
    # Crawl URLs based on positive and negative filters 
    url_list_crawler = crawl(start_url, filter_words_positive_crawler, filter_words_negative_crawler)
    # Combine Wikipedia URLs and crawled URLs
    final_urls_list = wiki_urls + url_list_crawler
    # Get file paths for the collected URLs
    urls_files_dict=getfilesdict(final_urls_list)
    #Pickle the dictionary
    # with open(pickle_file,'wb') as file1:
    #     pickle.dump(urls_files_dict,file1)

    with open(pickle_file, 'rb') as file:
        urls_files_dict = pickle.load(file)
    url_file_list = [urls_files_dict[file][1] for file in urls_files_dict]
    print(url_file_list)
    tfidf_results = get_tfidf(url_file_list)
    keywords = tfidf_results[:50]
    # print("printing key words")
    # for keyword in keywords:
    #     print(keyword)
    create_database('database_final_latest.db', url_file_list, keywords)
    print("database created")


























