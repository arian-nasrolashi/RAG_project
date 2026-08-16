import time
import threading
import os

os.system("cls")

results = []


def worker(name, start_num, end_num):
    total = 0

    for i in range(start_num, end_num + 1):
        total += i

    print(f"{name}: Sum from {start_num} to {end_num} = {total}")

    results.append(total)


start = time.time()

t1 = threading.Thread(target=worker, args=("Thread 1", 1, 250))
t2 = threading.Thread(target=worker, args=("Thread 2", 251, 500))
t3 = threading.Thread(target=worker, args=("Thread 3", 501, 750))
t4 = threading.Thread(target=worker, args=("Thread 4", 751, 1000))

t1.start()
t2.start()
t3.start()
t4.start()

t1.join()
t2.join()
t3.join()
t4.join()

end = time.time()

print(f"Total Sum = {sum(results)}")
print(f"Execution Time = {end - start:.6f} seconds")
print("Finished")
