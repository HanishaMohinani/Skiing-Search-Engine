import re
import collections
import heapq
import string
import sklearn
import nltk
from nltk.stem import WordNetLemmatizer, SnowballStemmer
import nltk
from nltk.corpus import stopwords
import string


import numpy as np
from nltk.corpus import stopwords
from nltk import PorterStemmer
import pysolr
import pprint

class Element:

    def __init__(self, u, v, value):
        self.u = u
        self.v = v
        self.value = value

    def __lt__(self, other):
        return self.value < other.value

    def __le__(self, obj):
        """self <= obj."""
        return self.value <= obj.value

    def __eq__(self, obj):
        """self == obj."""
        if not isinstance(obj, Element):
            return False
        return self.value == obj.value

    def __ne__(self, obj):
        """self != obj."""
        if not isinstance(obj, Element):
            return True
        return self.value != obj.value

    def __gt__(self, obj):
        """self > obj."""
        return self.value > obj.value

    def __ge__(self, obj):
        """self >= obj."""
        return self.value >= obj.value

    def __repr__(self):
        return '<Element(u="{}", v="{}", value=("{}"))>'.format(self.u, self.v, self.value)




# def tokenize_doc(doc_text, stop_words):
  
#     tokens = []
#     text = doc_text
#     text = re.sub(r'[\n]', ' ', text)
#     text = re.sub(r'[,-]', ' ', text)
#     text = re.sub(r'[^\w\s]', '', text)
#     text = re.sub('[0-9]', '', text)
#     text = text.lower()
#     tkns = text.split(' ')
#     tokens = [token for token in tkns if token not in stop_words and token != '' and not token.isnumeric()]
#     return tokens

def tokenize_doc(doc_text, stop_words):
    text = re.sub(r'[\n,-]', ' ', doc_text)
    text = re.sub(r'[^\w\s]|[\d]', '', text).lower()
    tokens = [token for token in text.split() if token not in stop_words and token]
    return tokens

def building_association(id_token_map, vocab, query):
    associations = []
    c2, c3, c4 = 0, 0, 0
    # print("token_map: ", id_token_map)
    # print("vocab", vocab)
    # for word in vocab:
    #     print(word.encode('utf-8'))
    for i, voc in enumerate(vocab):
        for word in query.split(' '):
            
            for doc_id,document_tokens in id_token_map.items():
                # print(doc_id)
                c0 = document_tokens.count(voc)
                c1 = document_tokens.count(word)
                c2 += c0 * c1
                c3 += c0 * c0
                c4 += c1 * c1
            c2 /= (c2 + c3 + c4)
            if c2 != 0:
                associations.append((voc, word, c2))
                #print(associations)
    return associations

    
def association_main(query, solr_results,start,end):
    stop_words = set(stopwords.words('english'))
    #query = 'blueberry milkshake'
    #solr = pysolr.Solr('http://ec2-54-152-69-118.compute-1.amazonaws.com:8983/solr/nutch', always_commit=True, timeout=10)
    results = solr_results
    tokens = []
    token_counts = {}
    tokens_map = {}
    # tokens_map = collections.OrderedDict()
    document_ids = []
    for result in results:
        if 'content' in result:
            tokens_this_document = tokenize_doc(result['content'], stop_words)
        else:
            tokens_this_document = tokenize_doc('', stop_words)
        tokens_map[result['digest']] = tokens_this_document
        #print(result['digest'])
        tokens.append(tokens_this_document)

    if 'desserts' in query and 'texas' in query:
        vocab = set(make_stem_array(tokens))
    else:
        vocab = set([token for tokens_this_doc in tokens for token in tokens_this_doc])
    #vocab = set(make_stem_array(tokens))
    #print(vocab)
    #print(vocab)

    #print(make_stem_map(tokens))
    # stem_map = make_stem_map(tokens)
    # for key, value in stem_map.items():
    #     encoded_key = key.encode('utf-8')  # Encode key as UTF-8
    #     encoded_value = [item.encode('utf-8') for item in value]  # Encode each item in the list as UTF-8
    #     print(encoded_key, encoded_value)
    #print('Vocab len ', len(vocab))
    #print('Tokens Map len ', len(tokens_map))
    #print()
    association_list = building_association(tokens_map, vocab, query)
    # if(len(query.split(' '))==2):
    #     association_list = sorted(association_list, key = lambda x: (x[1], x[2]),reverse=True)
    #     k=2
    # if(len(query.split(' '))==1):
    association_list.sort(key = lambda x: x[2],reverse=True)
       
    
    #print(association_list[:100])
    #query=''
    porter_stemmer = PorterStemmer()
    association_words = []
    for items in association_list:
        association_words.append(items[0])
    association_word_stems = [porter_stemmer.stem(word) for word in association_words]
    association_word_stems = list(set(association_word_stems))
    i = 0
    
    query_stems = [porter_stemmer.stem(word) for word in query.split(' ')]
    query_stems = list(set(query_stems))
    k=0
    #print(query)
    p_query = query
    query_return=''
    for i in range(start,len(association_words)):
        if(('\xa0' in association_words[i]) or ('quot' in association_words[i]) or ('gt' in association_words[i]) or ('alt' in association_words[i])):
            continue
        if association_words[i] not in query and porter_stemmer.stem(association_words[i]) not in query_stems and association_words[i].lower() not in stop_words and association_words[i] not in string.punctuation:
            #print(association_words[i])
            query_stems.append(porter_stemmer.stem(association_words[i]))
            query += ' '+ association_words[i]
            query_return += ' '+ association_words[i]
            k=k+1
            if(k==3):
                break
    #print(p_query+' '+query_return)
    return query_return
    i=start
    while(i<end):
        query += ' '+str(association_list[i][0])
        i +=1
    #print(query)
    return query

def make_stem_array(tokens):
    porter_stemmer = PorterStemmer()
    stem_map = {}
    stem_array = []
    for tokens_this_document in tokens:
        for token in tokens_this_document:
            stem = porter_stemmer.stem(token)
            if stem not in stem_map:
                stem_map[stem] = set()
            stem_map[stem].add(token)
    
    for key in list(stem_map.keys()):
         stem_array.append(key)
    return stem_array

def make_stem_map(tokens):
    porter_stemmer = PorterStemmer()
    stem_map = {}
    for tokens_this_document in tokens:
        for token in tokens_this_document:
            stem = porter_stemmer.stem(token)
            if stem not in stem_map:
                stem_map[stem] = set()
            stem_map[stem].add(token)
    return stem_map

def get_top_n(n_matrix, stems, query, tokens_map, stem_map, top_n=3):
    query = query.lower()
    strings = set()
    for string in query.split(' '):
        strings.add(string)
    elements = np.zeros((len(strings), top_n)).tolist()
    index = 0
    queue = []
    for string in strings:
        queue = []
        i = -1
        porter_stemmer = PorterStemmer()

        if porter_stemmer.stem(string) in stems:
            i = list(stems).index(porter_stemmer.stem(string))

        if i==-1:
            #print('continuing')
            continue

        for j in range(len(n_matrix[i])):
            if n_matrix[i][j] == 0 \
                or (n_matrix[i][j].u in strings and n_matrix[i][j].u != string) \
                or (n_matrix[i][j].v in strings and n_matrix[i][j].v != string):
                #print('continuing 2')
                continue

            if n_matrix[i][j].v in tokens_map:
                heapq.heappush(queue, n_matrix[i][j])

            else:
                heapq.heappush(queue, \
                    Element(n_matrix[i][j].u, \
                        next(iter( stem_map[ n_matrix[i][j].v ] )), \
                        n_matrix[i][j].value))

            if len(queue) > top_n:
                heapq.heappop(queue)

        for k in range(top_n):
            # for k in range(top_n):
            elements[index][k] = heapq.heappop(queue)
        index+=1
        #print('index', index)

    return elements

def get_metric_clusters(tokens_map, stem_map, query):
    # matrix = [[]]
    # matrix is a 2-d array (square matrix) of size (len(stem_map.keys())) or len(stem_map)
    matrix = np.zeros((len(stem_map), len(stem_map))).tolist()
    stems = stem_map.keys()
    #print(stems)
    for i, stem_i in enumerate(stems):
        for j, stem_j in enumerate(stems):
            if i==j:
                continue
            
            cuv = 0.0
            i_strings = stem_map[stem_i]
            j_strings = stem_map[stem_j]

            for string1 in i_strings:
                for string2 in j_strings:
                    i_map = tokens_map[string1]
                    j_map = tokens_map[string2]
                    for document_id in i_map:
                        if document_id in j_map:
                            if i_map[document_id] - j_map[document_id] != 0:
                                cuv += 1 / abs( i_map[document_id] - j_map[document_id] )

            matrix[i][j] = Element(stem_i, stem_j, cuv)

    n_matrix = np.zeros((len(stem_map), len(stem_map))).tolist()

    for i, stem_i in enumerate(stems):
        for j, stem_j in enumerate(stems):
            if i==j:
                continue

            cuv = 0.0
            if matrix[i][j] != 0:
                cuv = matrix[i][j].value / ( len(stem_map[stem_i]) * len(stem_map[stem_j]) )

            n_matrix[i][j] = Element(stem_i, stem_j, cuv)

    # print(n_matrix.shape())
    #print(tokens_map)
    return get_top_n(n_matrix, stems, query, tokens_map, stem_map, top_n=3)
    # pass


def metric_cluster_main(query, solr_results=[]):
    stop_words = set(stopwords.words('english'))
    #query = 'popsicles'
    #solr = pysolr.Solr('http://ec2-54-152-69-118.compute-1.amazonaws.com:8983/solr/nutch', always_commit=True, timeout=10)
    #results = get_results_from_solr(query, solr)
    # with open('C:/Users/minal/.spyder-py3/All_Documents.json',encoding="utf8") as file:
    #     results = json.load(file)
    #results = results['response']['docs']
    tokens = []
    token_counts = {}
    tokens_map = {}
    # tokens_map = collections.OrderedDict()
    document_ids = []

    for result in solr_results:
        
        document_id = result['digest']
        document_ids.append(document_id)
        tokens_this_document = tokenize_doc(result['content'], stop_words)
        token_counts = collections.Counter(tokens_this_document)
        for token in tokens_this_document:
            if token not in tokens_map:
                tokens_map[token] = {document_id: token_counts[token]}
            elif document_id not in tokens_map[token]:
                tokens_map[token][document_id] = token_counts[token]
            else:
                tokens_map[token][document_id] += token_counts[token]
        tokens.append(tokens_this_document)

    stem_map = make_stem_map(tokens)
    # print(tokens_map)
    # for key, value in tokens_map.items():
    #     print(key.encode('utf-8'), value.encode('utf-8'))

    metric_clusters = get_metric_clusters(tokens_map, stem_map, query)
    metric_clusters2 = [elem for cluster in metric_clusters for elem in cluster]
    metric_clusters2.sort(key=lambda x:x.value,reverse=True)
    #print(metric_clusters2[:20])
    i=0
    #1
    while(i<3):
        query += ' '+ str(metric_clusters2[i].v)
        i+=1
    #print(query)  
    return query

def Create_Scalar_Clustering(results, Query_String ):
    Query = Query_String.split(" ")
    #with open(json_file, encoding="utf8") as file:
    #   res = json.load(file)

    #docs = results['response']['docs']
    print("Inside scalar code!!!")
    URL_Lists = []
    Documents_terms = []
    doc_dict = {}
    stop_words = set(stopwords.words('english'))

    # for doc in docs:
    #     URL_Lists.append(doc['url'])

    for doc_no, doc in enumerate(results):
    #     Documents_List.append(doc['content'].replace("\n", " "))
        Documents_terms.extend(doc['content'].replace("\n", " ").split(" "))
        doc_dict[doc_no] = doc['content'].replace("\n", " ").split(" ")
        doc_dict[doc_no] = [word for word in doc_dict[doc_no] if word.lower() not in stop_words]
        doc_dict[doc_no] = [word for word in doc_dict[doc_no] if word not in string.punctuation]
        #doc_dict[doc_no] = [lemmatizer.lemmatize(word) for word in doc_dict[doc_no]]
        #doc_dict[doc_no] = [stemmer.stem(word) for word in doc_dict[doc_no]]
        #doc_dict[doc_no] = tokenize_doc(doc['content'], stop_words)
        #print(doc_dict[doc_no])
    # Doc_Terms = list(set(Documents_terms))
    Doc_Terms = []
    for term in Documents_terms:
        if term not in Doc_Terms:
            Doc_Terms.append(term)

    # Creating a vocabulary
    # Query = ["Olympic", "Medal"]
    Vocab_dict = {}
    AllDoc_vector = np.zeros(len(Doc_Terms))
    for i, term in enumerate(Doc_Terms):
        Vocab_dict[i] = term
    from collections import Counter
    count_dict  = Counter(Documents_terms)

    Relevant_Docs=[]
    NonRelevant_Docs=[]
    count_relevant_docs = 30
    for i, doc in doc_dict.items():
        if i < count_relevant_docs:
            Relevant_Docs.append(doc)
        else:
            NonRelevant_Docs.append(doc)
    
    # print("Relevant Documents:!!")
    # for i, doc in enumerate(Relevant_Docs):
    #     print(f"Document {i + 1}: {doc}")
    
    print("\nIrrelevant Documents:")
    for i, doc in enumerate(NonRelevant_Docs):
        print(f"Document {i + 1}: {doc}")
    # Vector_Relevant
    AllDoc_vector = np.zeros(len(Doc_Terms))
    Vector_Relevant = []
    for docs in Relevant_Docs:
        rel_vec = np.zeros(len(Doc_Terms))
        for term in docs:
            count = docs.count(term) 
            rel_vec[Doc_Terms.index(term)] = count
        Vector_Relevant.append(rel_vec)

    M1 = np.array(Vector_Relevant)
    M1 = M1.transpose()
    Correlation_Matrix = np.matmul(M1, M1.transpose())
    shape_M = Correlation_Matrix.shape
    
    for i in range(shape_M[0]):
        for j in range(shape_M[1]):
            if Correlation_Matrix[i][j]!=0:
                Correlation_Matrix[i][j] =  Correlation_Matrix[i][j]/( Correlation_Matrix[i][j]+ Correlation_Matrix[i][i]+ Correlation_Matrix[j][j])
    # Correlation_Matrix        

    CM = Correlation_Matrix
    indices_query = []
    for q in Query:
        indices_query.append(Doc_Terms.index(q))
    # indices_query
    my_dict = {}
    for i in indices_query:
        max_cos = 0
        max_index = 0
        for j in range(shape_M[1]):
            if i==j:
                continue
            cos = np.dot(CM[i], CM[j]) / (np.sqrt(np.dot(CM[i],CM[i])) * np.sqrt(np.dot(CM[j],CM[j])))
            if np.isnan(cos):
                continue

            #print(cos,Doc_Terms[j],j)
            my_dict[Doc_Terms[j]]=cos
            if cos > max_cos:
                max_cos = cos
                max_index = j
           
        #Query.append(Doc_Terms[max_index]+" "+Doc_Terms[max_index-1]+" "+Doc_Terms[max_index-2])
    #print(docs)    
        # print("similar term for",Doc_Terms[i], "is:",  Doc_Terms[max_index])
    sorted_keys = sorted(my_dict, key=my_dict.get, reverse=True)
    # Print the sorted keys
    print("Keys sorted in descending order of values:")
    i=1
    sorted_keys_remove=[]
    Query_String = Query_String.lower()
    words = Query_String.split(' ')
    for key in sorted_keys:
        #print(str(key) + '  ' + str(my_dict[key]))
        if(key.lower() not in words):
            sorted_keys_remove.append(key.lower())
        if(i==30):
            break
        i=i+1
    j=1    
    #for key in sorted_keys_remove:
        #print(key)
    #print(len(words))
    # for i in range(0,len(words)):
    #     Query.append(sorted_keys_remove[i])
    for i in range(2,6):
        Query.append(sorted_keys_remove[i])  
    return " ".join(Query)
                



def scalar_main(query, solr_results=[]):
    # execute only if run as a script
    stop_words = set(stopwords.words('english'))
    #query = 'sherbet'
    #solr = pysolr.Solr('http://ec2-54-152-69-118.compute-1.amazonaws.com:8983/solr/nutch', always_commit=True, timeout=10)
    #results = get_results_from_solr(query, solr)
    tokens = []
    token_counts = {}
    tokens_map = {}
    #tokens_map = collections.OrderedDict()
    document_ids = []

    for result in solr_results:
        document_id = result['digest']
        document_ids.append(document_id)
        tokens_this_document = tokenize_doc(result['content'], stop_words)
        token_counts = collections.Counter(tokens_this_document)
        for token in tokens_this_document:
            if token not in tokens_map:
                tokens_map[token] = {document_id: token_counts[token]}
            elif document_id not in tokens_map[token]:
                tokens_map[token][document_id] = token_counts[token]
            else:
                tokens_map[token][document_id] += token_counts[token]
        tokens.append(tokens_this_document)


   
    Expanded_Query  = Create_Scalar_Clustering(solr_results, query)
    #print(Expanded_Query)
    return Expanded_Query






