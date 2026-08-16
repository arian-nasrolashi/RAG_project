import os
import random
os.system('cls')
choices = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

player_score = 0
robot = random.choice(choices)

for round in range(1, 4):

    player = int(input("choose a number 1 to 10: "))
    if player == robot:
        player_score += 1
        print("player win!")
        print(f"you found the number on: {round}")
        break
    elif player < robot:
        print("go higher")
    elif player > robot:
        print("go lower")
if player_score == 0:
    print("robot win the match")
