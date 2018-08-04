
# coding: utf-8

# In[2]:


#!/home/ubuntu/anaconda3/bin//python
'''
MIT License

Copyright (c) 2018 Riya Dulepet <riyadulepet123@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Thanks to the entire Columbia INCITE team for suggestions/recommendations,
collaboration, critic, advice, and mentoring. This code was generated as part
of summer internship @INCITE Columbia.
'''


# In[9]:
'''
The main objective of this code is to detect near duplicates/similarities
between course descriptions based on the college (grid_name) and year
the course is offered and field_name

The process of duplicates implements following algorithm:
    STEP 1: It runs the LSH algorithm to find super fast "likely candidate"
            similar pairs on very large datasets, in this case a dataset is defined
            by all course description that have same GRID NAME,FIELD NAME, YEAR.
    STEP 2: Take all course descriptions and generate TF-IDF [as in statistically significant word phrases
            [could be NLP-based, or N-GRAM (unigram/bigram/trigram..) to extract features] that are rare across corpus
            but significant on that particular course description. Remarkably, the top 10 words seems to describe the
            most unique words of the course description, creating a signature
    STEP 3: Take the candidate pairs from STEP 1, and use the reduced statistically significant signature
            (rather than entire course text since that contains ton of templated text) from STEP 2,
            and run FUZZY match (distance based algo) to come up with accuracy score of those
            candidate matches from step 1 ranking of these matches by probability/ranking score
            gives you the right results that is trustworthy

we use POSTGRES SQL database as the transactional database to retrieve and store records
    created a database called litindex where I restored the original JSON files with
    syllabi description and associated meta data(separate code)
    Created two tables in that database:
        1) open_syllabi that contains all fields from the original JSON files (seperate script)
             1.1) the fields relevant for this exercise of duplicates are (focused only on US records):
                 1.1.1) id, grid_country_code=US, grid_name, field_name, year, and text field (contains course description)
        2) similar_syllabi that contains results of processing duplicates (the current script focus)
            2.1) this contains fields:
                grid_name - college name
                field_name - course subject area
                year - course was offered
                id1 - duplicates are pairs, so this is the id of the first record
                id2 - duplicates are pairs, so this is the id of the second record
                id1_top_10_significant_words - contains top 10 most significant words for first record
                id2_top_10_significant_words - contains top 10 most significant words for second record
                accuracy_score - confidence of match for the two records
    Each of the tables has several indices to make the process of retrieval speedy
    Database Stats:
        open_syllabi has 5,800,477 (5.8M) records, and 2,755,745 (2.75M) US records
'''    

'''
Results Summary
===============
similar_syllabi (results of this exercise) has 21,097,972 (21M) potential duplicate pairs
    out of the 21M pairs:
        15.5M pairs have accuracy score of atleast 97% confidence
        13.5M pairs have accuracy score of 100%
        18.8M pairs of accuracy score of 90%
I would trust 97%+ results based on some QA, but 90% seem to be pretty to be good
PROCEED WITH CAUTION: requires further Quality Control
We can take this a step further (but not part of current code to get to final step):
    1) the query "select count(distinct id1) from similar_syllabi where accuracy_score >= 97" yields
        784,537 records, in other words there are so many ids of records in original database with high
        probability of duplicates with other records
    2) the query "select id1,count(*) as cnt from similar_syllabi where accuracy_score >= 97 group by id1 order by cnt desc;"
        yields records with most duplicates of high confidence
    3) the query "select id1,array_agg(id2) from similar_syllabi where accuracy_score >= 97 group by id1;" yields
        each record and its list of corresponding duplicate record IDs

Room for code improvement
=========================
    1) lot of tasks are highly parallelizable using Spark
    2) better use of Python idioms that might have led to improved use of multicore machine
    3) better factoring or modularization of code
    4) producing confusion matrix for QA
    5) test harness or unit testing code
    
Running the code
================
    1) it assumes a Postgres database with course description records (uploading data is separate script)
    2) python findAllDuplicatesInLitIndex2.py
        2.1) but since this is computationally intensive, would recommend running as background process
'''

import glob
import pandas as pd
import psycopg2
import sys
import json
import pandas as pd
import numpy as np
import itertools
from psycopg2.extras import execute_values
import math
import random
from fuzzywuzzy import fuzz
import string
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer

from lsh import cache, minhash # https://github.com/mattilyra/lsh
stop = stopwords.words('english')


# In[10]:


# a pure python shingling function that will be used in comparing
# LSH to true Jaccard similarities
def shingles(text, char_ngram=5):
    return set(text[head:head + char_ngram] for head in range(0, len(text) - char_ngram))


def jaccard(set_a, set_b):
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union)


def candidate_duplicates(document_feed, char_ngram=5, seeds=100, bands=5, hashbytes=4):
    char_ngram = 5
    sims = []
    hasher = minhash.MinHasher(seeds=seeds, char_ngram=char_ngram, hashbytes=hashbytes)
    if seeds % bands != 0:
        raise ValueError('Seeds has to be a multiple of bands. {} % {} != 0'.format(seeds, bands))
    
    lshcache = cache.Cache(num_bands=bands, hasher=hasher)
    for line in document_feed:
        line = line.decode('utf8')
        docid, headline_text = line.split('\t', 1)
        fingerprint = hasher.fingerprint(headline_text.encode('utf8'))
        
        # in addition to storing the fingerpring store the line
        # number and document ID to help analysis later on
        lshcache.add_fingerprint(fingerprint, doc_id=docid)

    candidate_pairs = set()
    for b in lshcache.bins:
        for bucket_id in b:
            if len(b[bucket_id]) > 1:
                pairs_ = set(itertools.combinations(b[bucket_id], r=2))
                candidate_pairs.update(pairs_)
    
    return candidate_pairs


# In[11]:


def fetch_all_grid_name__year__field_names():
    try:
        conn = psycopg2.connect("dbname='litindex' user='litindex' host='0.0.0.0' password='lit123'")
        cur = conn.cursor()
        
        # consider only if valid grid_name and year
        cur.execute("""SELECT grid_name, year, field_name, count(*) as cnt from open_syllabi where grid_name != 'NaN' and year > 0 and grid_country_code='US' group by grid_name, year, field_name having count(*) > 1 order by cnt desc""")
        df_grid_name__year__field_name = pd.DataFrame(cur.fetchall(), columns=['grid_name', 'year', 'field_name', 'cnt'])
        
        return df_grid_name__year__field_name # finally block will run before this return automatically
    except Exception as e:
        if conn:
            conn.rollback()
        # print("Unexpected error:", sys.exc_info()[0]])
        print(e)
        sys.exit(1)
        # return None # finally block will run before this return automatically
    finally:   
        # Close communication with the database
        if cur:
            cur.close()
        if conn:
            conn.close()


# In[12]:


def insert_duplicate_pairs(list_duplicate_pairs):
    # insert duplicate pairs with accuracy score and associated evidence
    try:
        # connect to existing database
        conn = psycopg2.connect("dbname='litindex' user='litindex' host='0.0.0.0' password='lit123'")
        conn.autocommit = True
        
        # Open a cursor to perform database operations
        cur = conn.cursor()
        insert_query = 'insert into similar_syllabi (grid_name, field_name, year, id1, id2, id1_top_10_significant_words, id2_top_10_significant_words, accuracy_score) values %s'
        psycopg2.extras.execute_values (cur, insert_query, list_duplicate_pairs, template=None, page_size=100)
    except Exception as e:
        if conn:
            conn.rollback()
        # print("Unexpected error:", sys.exc_info()[0]])
        print(e)
        sys.exit(1)
    finally:
        # Close communication with the database
        if cur:
            cur.close()
        if conn:
            conn.close()


# In[13]:


def find_and_store_duplicate_syllabi(grid_name, year, field_name):
    global stop
    try:
        # connect to existing database
        conn = psycopg2.connect("dbname='litindex' user='litindex' host='0.0.0.0' password='lit123'")
        # Open a cursor to perform database operations
        cur = conn.cursor()

        param_list = [grid_name, year, field_name]
        select_query = "SELECT id, text_md5, text from open_syllabi where grid_name='{}' and year='{}' and field_name='{}'".format(*param_list) #unpack the list
        cur.execute(select_query)
        df = pd.DataFrame(cur.fetchall(), columns=['id', 'text_md5', 'text'])
        print("\tNO OF RECORDS = {}", len(df))

        punctuation_translator = str.maketrans('', '', string.punctuation)


        # PRE-PROCESSING REQUIRED:
        # normalize by lowering the case, removing punctuations, removing numbers and english stop words
        df['text_lower_case_words'] = df['text'].apply(lambda x: ' '.join([word for word in x.lower().translate(punctuation_translator).split() if not word.isdigit() and word not in stop]))
        # the following pre-processing is required to improve quality of LSH results
        # especially considering highly templated text in course descriptions
        df['text_unique_words'] = df['text'].apply(lambda x: ' '.join([word for word in list(set(x.lower().translate(punctuation_translator).split())) if not word.isdigit() and word not in stop]))
        common_words_series = pd.Series(' '.join(df['text_unique_words']).lower().strip(string.punctuation).split()).value_counts()
        most_common_words_series = common_words_series[common_words_series > (0.5 * len(df))].dropna()
        most_common_words_list = most_common_words_series.index.tolist()
        df['text_without_common_words'] = df['text'].apply(lambda x: ' '.join([word for word in x.lower().translate(punctuation_translator).split() if word not in (most_common_words_list) and word not in stop]))
        
        # STEP 1: use LSH algorithm to find candidate duplicates
        # find duplicates
        # run through adding documents to the LSH cache
        hasher = minhash.MinHasher(seeds=100, char_ngram=5, hashbytes=4)
        lshcache = cache.Cache(bands=10, hasher=hasher)
        
        for idx in range(0, (len(df) - 1)):
            lshcache.add_fingerprint(hasher.fingerprint(df.loc[idx, 'text_without_common_words']), df.loc[idx, 'id'])
        
        # for every bucket in the LSH cache get the candidate duplicates
        # note this fast way to get candidate pairs with reasonable accuracy, that will be filtered later
        candidate_pairs = set()
        for b in lshcache.bins:
            for bucket_id in b:
                if len(b[bucket_id]) > 1: # if the bucket contains more than a single document
                    pairs_ = set(itertools.combinations(b[bucket_id], r=2))
                    candidate_pairs.update(pairs_)
        list_candidate_pairs = list(candidate_pairs)
        tsl = []
        # df = df.set_index('id')
        print("\tcandidate pairs found = {}", len(list_candidate_pairs))
        
        # STEP 2: use TFIDF to process the records associated with the candidate duplicates and generate signature text
        tf = TfidfVectorizer(analyzer='word', ngram_range=(1,1), min_df = 0, stop_words = 'english')
        tfidf_matrix =  tf.fit_transform(df['text_lower_case_words'])
        feature_names = tf.get_feature_names()
        dense = tfidf_matrix.todense()

        for item in list_candidate_pairs:
            idx1 = df.index[df['id'] == int(item[0])]
            idx2 = df.index[df['id'] == int(item[1])]
            episode1 = dense[idx1].tolist()[0]
            episode2 = dense[idx2].tolist()[0]
            phrase_scores1 = [pair for pair in zip(range(0, len(episode1)), episode1) if pair[1] > 0]
            sorted_phrase_scores1 = sorted(phrase_scores1, key=lambda t: t[1] * -1)
            phrase_scores2 = [pair for pair in zip(range(0, len(episode2)), episode2) if pair[1] > 0]
            sorted_phrase_scores2 = sorted(phrase_scores2, key=lambda t: t[1] * -1)
            list_summarized_text1 = []
            list_summarized_text2 = []
            for phrase, score in [(feature_names[word_id], score) for (word_id, score) in sorted_phrase_scores1][:10]:
                # print('{0: <20} {1}'.format(phrase, score))
                list_summarized_text1.append(phrase)
            for phrase, score in [(feature_names[word_id], score) for (word_id, score) in sorted_phrase_scores2][:10]:
                # print('{0: <20} {1}'.format(phrase, score))
                list_summarized_text2.append(phrase)
            
            summarized_text1 = ' '.join(list_summarized_text1)
            summarized_text2 = ' '.join(list_summarized_text2)
            # STEP 3: apply fuzzy match for the two signature texts to generate accuracy score
            fuzz_ratio = fuzz.token_set_ratio(summarized_text1, summarized_text2)
            tsl.append((grid_name, field_name, int(year), int(item[0]), int(item[1]), summarized_text1, summarized_text2, fuzz_ratio))
        # for item in list_candidate_pairs:
        insert_duplicate_pairs(tsl)
        
        df = df.set_index('id')
        return df
    except Exception as e:
        if conn:
            conn.rollback()
        # print("Unexpected error:", sys.exc_info()[0]])
        print(e)
        sys.exit(1)
    finally:
        # Close communication with the database
        if cur:
            cur.close()
        if conn:
            conn.close()


# In[ ]:


'''
# sample test
%%time
row = {'grid_name':"University of Michigan–Ann Arbor", \
      'year':2011, \
      'field_name':"Social Work."}
df = find_and_store_duplicate_syllabi(row['grid_name'], row['year'], row['field_name'])
'''


# In[12]:


# main program
def main():
    print("START")
    # df_completed = pd.read_csv("./completed_triplets.csv", sep="\t")
    # iterate through database records
    df_grid_name__year__field_name = fetch_all_grid_name__year__field_names()
    print("NO OF COMBOS = {}", len(df_grid_name__year__field_name))
    for index, row in df_grid_name__year__field_name.iterrows():
        # check if we already processed this
        '''
        df_exists = df_completed[(df_completed["grid_name"] == row['grid_name']) & \
                                 (df_completed["field_name"] == row['field_name']) & \
                                 (df_completed["year"] == row['year'])]
        if 0 == len(df_exists):
        '''
        # wasn't processed before
        print("PROCESSING GRID_NAME = ", row['grid_name'], \
              ", YEAR = ", str(row['year']), \
              ", FIELD_NAME = ", row['field_name'])
        find_and_store_duplicate_syllabi(row['grid_name'], row['year'], row['field_name'])
    print("END")

if __name__== "__main__":
    main()
