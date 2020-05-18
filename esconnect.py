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
        es.indices.delete(index=index_name)
    print(es.indices.create(index=index_name))


index_name = 'crypto_price_info'
# index_name = 'test'
# make_index(es, index_name)


# # 데이터를 저장한다
# doc1 = {'goods_name': '삼성 노트북 91',    'price': 10000001}
# doc2 = {'goods_name': '엘지 노트북 그램1', 'price': 20000001}
# doc3 = {'goods_name': '애플 맥북 프로1',   'price': 30000001}
# es.index(index=index_name, doc_type='string', body=doc1)
# es.index(index=index_name, doc_type='string', body=doc2)
# es.index(index=index_name, doc_type='string', body=doc3)
# es.indices.refresh(index=index_name)

# 상품명에 '노트북'을 검색한다S
results = es.search(index=index_name, body={'from':0, 'size':10, "query": {
    "bool": {
      "must": [
        {
          "datetime": {
            "date": {
              "gte": "2020-05-18",
              "lte": "2020-05-19"
            }
          }
        },
        {
          "datetime": {
            "time": {
              "gte": "08:00:00",
              "lte": "24:00:00"
            }
          }
        }
      ]
    }
  }
  })
print(results)


# results = es.search(index=index_name, body={'from':0, 'size':10, 'query':{'match':{'goods_name':'노트북'}}})
# for result in results['hits']['hits']:
#     print('score:', result['_score'], 'source:', result['_source'])


