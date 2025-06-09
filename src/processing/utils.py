# from Connection import Connection



# client=Connection.get_elasticsearch()


def put_to_index(doc,client=None):
    
    if not client:
        
        
        from Connection import Connection
        
        try:
            client = Connection.get_elasticsearch()
        except Exception as e:
            raise Exception(f"Error connecting to Elasticsearch: {str(e)}")
      
      
    try:  
        client.index(
            index="row",
            document=doc,
        )
    except Exception as e:
        raise Exception(f"Error indexing document: {str(e)}")    