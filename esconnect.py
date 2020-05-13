from elasticsearch import Elasticsearch
from elasticsearch import helpers

server = 'http://es-arques.com:9200/'

# # elasticsearch connect
es = Elasticsearch(server)
es.info()

def connect():
    es = Elasticsearch(server)
    es.info()

    return es

def make_index(es, index_name):
    if es.indices.exists(index=index_name):
        es.indices.delte(index=index_name)
    print(es.indices.create(index=index_name))


index_name = 'test'
make_index(es, index_name)


# 데이터를 저장한다
doc1 = {'goods_name': '삼성 노트북 9',    'price': 1000000}
doc2 = {'goods_name': '엘지 노트북 그램', 'price': 2000000}
doc3 = {'goods_name': '애플 맥북 프로',   'price': 3000000}
es.index(index=index_name, doc_type='string', body=doc1)
es.index(index=index_name, doc_type='string', body=doc2)
es.index(index=index_name, doc_type='string', body=doc3)
es.indices.refresh(index=index_name)

# 상품명에 '노트북'을 검색한다
results = es.search(index=index_name, body={'from':0, 'size':10, 'query':{'match':{'goods_name':'노트북'}}})
for result in results['hits']['hits']:
    print('score:', result['_score'], 'source:', result['_source'])


