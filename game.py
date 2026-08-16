import random
import os
os.system("cls")
choices = ["rock", "paper", "scissors"]
player_score = 0
robot_score = 0
for round in range(1, 6):
    player = input("choose your rock , paper , scissors: ")
    print(player)
    robot = random.choice(choices)
    print(robot)
    if player == robot:
        print("draw")
    elif player == "rock" and robot == "scissors":
        player_score += 1
        print("Player Wins!")
    elif player == 'paper' and robot == 'rock':
        player_score += 1
        print("player win")
    elif player == 'scissors' and robot == 'paper':
        player_score += 1
        print('player win')
    elif player == 'rock' and robot == 'paper':
        robot_score += 1
        print('robot win')
    elif player == 'paper' and robot == 'scissors':
        robot_score += 1
        print('robot win')
    elif player == 'scissors' and robot == 'rock':
        robot_score = + 1
        print('robot win')

print(f"robot_score: {robot_score}")
print(f"player_score: {player_score}")

if player_score == robot_score:
    print('draw')
elif player_score < robot_score:
    print('robot win the math')
elif player_score > robot_score:
    print('player win the math')
