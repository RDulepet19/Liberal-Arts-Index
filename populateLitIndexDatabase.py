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

# coding: utf-8

# In[91]:
'''
The main objective of this code is to parse the raw JSON files and upload to
postgres database.

ASSUMPTIONS:
    1) postgres database litindex exists
    2) open_syllabi table exists in the database (table creation not part of script)
    3) indexing only a subset of relevant data from JSON for the task

data definitions to  create desired tables for input and output:
CREATE TABLE open_syllabi (
     id BIGINT DEFAULT 0, 
     corpus VARCHAR(10000) NOT NULL DEFAULT '',
     corpus_id VARCHAR(10000) NOT NULL DEFAULT '',
     url VARCHAR(10000) NOT NULL DEFAULT '',
     source_url VARCHAR(10000) NOT NULL DEFAULT '',
     source_anchor VARCHAR(10000) NOT NULL DEFAULT '',
     retrieved VARCHAR(256) NOT NULL DEFAULT '',
     mime_type VARCHAR(256) NOT NULL DEFAULT '',
     text_md5 VARCHAR(256) NOT NULL DEFAULT '',
     syllabus_probability double precision DEFAULT 0, 
     year INTEGER DEFAULT 0, 
     field_code VARCHAR(256) NOT NULL DEFAULT '',
     field_score double precision DEFAULT 0, 
     field_name VARCHAR(256) NOT NULL DEFAULT '',
     institution_id VARCHAR(256) NOT NULL DEFAULT '',
     grid_id VARCHAR(256) NOT NULL DEFAULT '',
     grid_links text[], 
     grid_name VARCHAR(256) NOT NULL DEFAULT '',
     grid_city VARCHAR(256) NOT NULL DEFAULT '',
     grid_country_code VARCHAR(256) NOT NULL DEFAULT '',
     grid_state_code VARCHAR(256) NOT NULL DEFAULT '',
     wikidata_id VARCHAR(256) NOT NULL DEFAULT '',
     wikidata_UNITID VARCHAR(256) NOT NULL DEFAULT '',
     P856 VARCHAR(256) NOT NULL DEFAULT '',
     APPLCN double precision DEFAULT 0, 
     INSTNM VARCHAR(256) NOT NULL DEFAULT '',
     ipeds_UNITID VARCHAR(256) NOT NULL DEFAULT '',
     WEBADDR VARCHAR(256) NOT NULL DEFAULT '',
     BASIC2015 VARCHAR(256) NOT NULL DEFAULT '',
     CITY VARCHAR(256) NOT NULL DEFAULT '',
     CONTROL VARCHAR(256) NOT NULL DEFAULT '',
     HBCU BOOLEAN DEFAULT FALSE, 
     NAME VARCHAR(256) NOT NULL DEFAULT '',
     STABBR VARCHAR(256) NOT NULL DEFAULT '',
     TRIBAL BOOLEAN DEFAULT FALSE, 
     UGPROFILE2015 VARCHAR(256) NOT NULL DEFAULT '',
     carnegie_UNITID VARCHAR(256) NOT NULL DEFAULT '',
     WOMENS BOOLEAN DEFAULT FALSE, 
     extra_match_urls TEXT[],
     element VARCHAR(256) NOT NULL DEFAULT '',
     text TEXT,
     duplicate_entry BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx1 ON open_syllabi (source_anchor, grid_name, field_name);
CREATE INDEX idx2 ON open_syllabi (source_anchor, grid_name, field_name, year);
CREATE INDEX idx3 ON open_syllabi (source_anchor);
CREATE INDEX idx4 ON open_syllabi (grid_name);
CREATE INDEX idx5 ON open_syllabi (grid_name, field_name);
CREATE INDEX idx6 ON open_syllabi (duplicate_entry);
CREATE INDEX idx7 ON open_syllabi (grid_name, duplicate_entry);
CREATE INDEX idx8 ON open_syllabi (text_md5);
CREATE INDEX idx9 ON open_syllabi (id);
CREATE INDEX idx10 ON open_syllabi (grid_country_code);

CREATE TABLE similar_syllabi (
    grid_name VARCHAR(256) NOT NULL DEFAULT '',
    field_name VARCHAR(256) NOT NULL DEFAULT '',
    year INTEGER DEFAULT 0,
    id1 BIGINT DEFAULT 0,
    id2 BIGINT DEFAULT 0,
    id1_top_10_significant_words VARCHAR(4096) NOT NULL DEFAULT '',
    id2_top_10_significant_words VARCHAR(4096) NOT NULL DEFAULT '',
    accuracy_score INT DEFAULT 0 
);

CREATE INDEX idxs1 ON similar_syllabi (grid_name, field_name, year);
CREATE INDEX idxs2 ON similar_syllabi (grid_name, field_name);
CREATE INDEX idxs3 ON similar_syllabi (grid_name, year);
CREATE INDEX idxs4 ON similar_syllabi (field_name, year);
CREATE INDEX idxs5 ON similar_syllabi (id1, id2);
CREATE INDEX idxs6 ON similar_syllabi (id1);
CREATE INDEX idxs7 ON similar_syllabi (id2);
CREATE INDEX idxs8 ON similar_syllabi (accuracy_score);
CREATE INDEX idxs9 ON similar_syllabi (grid_name, field_name, year, accuracy_score);
CREATE INDEX idxs10 ON similar_syllabi (grid_name, field_name, accuracy_score);


# backup and restore of database
pg_dump  --dbname=postgresql://litindex:lit123@127.0.0.1:5432/litindex > litindex.sql
tar czvf litindex.tgz litindex.sql

tar xzvf litindex.tgz
psql -d litindex -U litindex -f litindex.sql
'''

import glob
import pandas as pd
import psycopg2
import sys
import json
from numpy import math

try:
    litindex_json_files = glob.glob("./rawdata/*.json")
    conn = psycopg2.connect("dbname='litindex' user='litindex' host='0.0.0.0' password='lit123'")
    cur = conn.cursor()

    for onefile in litindex_json_files:
        json_records = pd.read_json(onefile,  lines=True)
        for index, row in json_records.iterrows():
            print(row['id'])
            # print(row['institution_id'])
            rowId = row['id']
            if math.isnan(rowId):
                rowId = 0
                # print("NAN row_id =",rowId)
            rowInstitutionId = row['institution_id'] 
            if math.isnan(rowInstitutionId):
                rowInstitutionId = 0.0
                # print("NAN rowInstitutionId =",rowInstitutionId)
            year = row['year']
            if math.isnan(year):
                year = 0
                # print("NAN year =",year)
            cur.execute("INSERT INTO open_syllabi(id, source_url, source_anchor, syllabus_probability, year, field_name, institution_id, grid_name, grid_country_code, text_md5, text) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);",             (rowId, row['source_url'], row['source_anchor'], row['syllabus_probability'],  year, row['field_name'], rowInstitutionId, row['grid_name'], row['grid_country_code'], row['text_md5'], row['text'], ))
            conn.commit()
except Exception as e:
    if conn:
        conn.rollback()
    # print("Unexpected error:", sys.exc_info()[0]])
    print(e)
    sys.exit(1)
 
finally:   
    if conn:
        conn.close()
