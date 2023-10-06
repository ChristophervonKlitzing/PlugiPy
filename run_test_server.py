from plugipy.python_service.python_service import RPCService

def main():
    from rpyc.utils.server import ThreadedServer
    # TODO: Add option for secure connection
    t = ThreadedServer(RPCService, port=4567)
    t.start()

if __name__ == "__main__":
    main()