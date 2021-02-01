from adapters.el_salvador_adapter import ElSalvadorAdapter
from adapters.mexico_adapter import MexicoAdapter
from adapters.adapter_tasks import AdapterThread
from queue import Queue
import time

def main():
    esa = ElSalvadorAdapter()
    ma = MexicoAdapter()
    queue = Queue()

    t1 = AdapterThread(esa, queue)
    t2 = AdapterThread(ma, queue)
    t1.start()
    t2.start()

    counter = 0

    while t1.is_alive() or t2.is_alive():
        print("T1:", t1.is_alive())
        print("T2:", t2.is_alive())
        print("Queue is", "empty" if queue.empty() else "not empty")
        if not queue.empty():
            print(queue.get())
        if counter > 10:
            counter = 0
            if t1.is_alive():
                t1.join()
            else:
                t2.join()
        counter += 1
        time.sleep(1)
        
    print("program terminated")

if __name__ == "__main__":
    main()