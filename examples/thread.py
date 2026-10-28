import threading
import time

def print_numbers():
    for i in range(1, 6):
        print(f"Number: {i}")
        time.sleep(1)

def print_letters():
    for c in "ABCDE":
        print(f"Letter: {c}")
        time.sleep(1)

# Run without threading (sequential)
print("---- Sequential ----")
print_numbers()
print_letters()



# Run with threading (concurrent)
print("\n---- With Threads ----")
t1 = threading.Thread(target=print_numbers)
t2 = threading.Thread(target=print_letters)

t1.start()
t2.start()

t1.join()
t2.join()
