import math
import os
os.system('cls')

# course = "python programing"

# # indexing sring[start:end:step]

# print(len(course))

# print(course[-2] * 10)

# # slicing
# print(course[0:6])
# print(course[:6])
# print(course[0:])
# print(course[:])
# print(course[0:6:2])  # اینطوری دو تا دو تا پیش میره
# # part 2
# message = 'study"pyrhon'
# message2 = "study \"python"
# print(message[0:])
# print(message2[0:]*2)
# # part 3
# first = "Arian"
# last = "nasrolahi"
# full = first + " " + last
# print(full)
# # string formating
# full2 = f"{first} {last} {len(last)}"
# print(full2)
# a = "ar"
# p = "pa"
# ap = f"{a} {p} {len(p)}"
# print(ap)
# # string method:
# pc = ' I hate nigger'
# print(pc.upper())
# print(pc.upper())
# print(pc.strip())
# print(pc.find('nigger'))
# print(pc.replace("i", "e"))
# numbers/ standard arithmetic operators :
# print(15+14)  # addition به خود این عمل میگن
# print(15-14)  # subtractin (-)
# print(15*14)  # multipulication
# print(15/14)  # division
# print(15//14)  # index همان تقسیم ولی به صورت
# print(15 % 14)  # modulus
# print(15**14)  # exponentiation (power)

# # agumented assigmnment :
# x = 10
# x = x + 14
# print(x)
# # math function
# print(math.ceil(2.5))
# print(math.floor(2.5))
# print(math.factorial(4))
# # برو python.math  برای بیشتر به سایت

# # تغییر داده ها
# arian = float(input("arian: "))
# po = arian + 14
# print(f"arian : {arian} , po : {po}")
birthday = input("your birthday: ")
this_year = input("this year: ")
print("____________________________________")
print(f"birth_year : {birthday[0:4]}")
print(f"birth_mounth : {birthday[5:7]}")
print(f"day_birth : {birthday[8:]}")
print(f"age: {int(this_year) - int(birthday[0:4])}")
