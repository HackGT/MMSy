NUM_WORKERS = 5

def convert(picture):
    # TODO send request
    pass

def worker(q):
    while True:
        picture = q.get()
        convert(picture)
