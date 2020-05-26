from socket_data.base.socket_data import socket_data
import time

class bitmex_data(socket_data):
    name = ""
    data = {}
    timestamp = int(round(time.time() * 1000))
    orderbooks = []

    def __init__(self, dic):
        self.name = dic['name']
        self.data = dic['data']


    def datamining(self):
        # dic = {}

        _data = self.data['data']
        # print(self.data)
        
        if self.data['action'] == 'partial':            
            self.set_orderbooks(self.name, _data)            
        elif self.data['action'] == 'update':            
            # print(self.data['action'], _data)
            self.update_orderbooks(self.name, _data)
        elif self.data['action'] == 'insert':            
            # print(self.data['action'], _data)
            self.insert_orderbooks(self.name, _data)
        elif self.data['action'] == 'delete':            
            # print(self.data['action'], _data)
            self.delete_orderbooks(self.name, _data)

        # # 제대로 되어 있는지 확인
        # for i in range(len(self.orderbooks)):
        #     print(self.orderbooks[i])

        return self.orderbooks

    @classmethod
    def set_orderbooks(self, name, data):
        self.orderbooks = []

        exchange_type = "futures"
        exchange_name = name       

         

        for i in range(len(data)):
            
            if data[i]['side'] == 'Sell':
                kind = "asks"
            else:
                kind = "bids"
                        
            data[i]["exchange_type"] = exchange_type
            data[i]["exchange_name"] = exchange_name            
            data[i]["symbol"] = "BTC/USD"
            data[i]["kind"] = kind
            data[i]["timestamp"] = self.timestamp

            if "side" in data[i]:
                del data[i]['side']
            if "size" in data[i]:
                data[i]["volume"] = data[i]["size"]
                del data[i]["size"]


            self.orderbooks.append(data[i])


    @classmethod
    def insert_orderbooks(self, name, data):
        exchange_type = "futures"
        exchange_name = name        

        for i in range(len(data)):
            
            if data[i]['side'] == 'Sell':
                kind = "asks"
            else:
                kind = "bids"
            
            data[i]["exchange_type"] = exchange_type
            data[i]["exchange_name"] = exchange_name  
            data[i]["symbol"] = "BTC/USD"          
            data[i]["kind"] = kind
            data[i]["timestamp"] = self.timestamp

            if "side" in data[i]:
                del data[i]['side']
            if "size" in data[i]:
                data[i]["volume"] = data[i]["size"]
                del data[i]["size"]


            self.orderbooks.append(data[i])        

    @classmethod
    def update_orderbooks(self, name, data):
        for i in range(len(data)):
            id = data[i]["id"]            

            orderbook, idx = self.search_orderbook("id", id)

            if "size" in data[i]:
                orderbook["volume"] = data[i]["size"]
            if "price" in data[i]:
                orderbook["price"] = data[i]["price"]

            orderbook["timestamp"] = self.timestamp

            
    @classmethod
    def search_orderbook(self, key, value):
        for i in range(len(self.orderbooks)):
            if self.orderbooks[i][key] == value:
                return self.orderbooks[i], i        

    @classmethod
    def delete_orderbooks(self, name, data):
        for i in range(len(data)):
            id = data[i]["id"]    

            orderbook, idx = self.search_orderbook("id", id)       

            del self.orderbooks[idx]






        


