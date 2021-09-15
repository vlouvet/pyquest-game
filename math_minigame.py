import random

correctAnswerCount = 0
def generateFormula(correctAnswerCount, formulaType="addition"):
    if formulaType == "addition":
        x = random.randrange(1, 50)
        y = random.randrange(1, 50)
        z = x + y
        print(f"What is the answer to X ({x})+ Y({y})?")
        answer_list = [random.randrange(1, 100), random.randrange(1, 100), z]
        answer_list = random.sample(answer_list, len(answer_list))
        answers = {"a": answer_list[0], "b": answer_list[1], "c": answer_list[2]}
        userInput = input(f"A:{answers['a']}\nB:{answers['b']}\nC:{answers['c']}\n\n")
        if userInput == "a":
            if answers["a"] == z:
                correctAnswerCount +=1
                print("you chose the right answer!")
                generateFormula(correctAnswerCount, formulaType="addition")
            else:
                print("wrong answer!")
        elif userInput == "b":
            if answers["b"] == z:
                correctAnswerCount +=1
                print("you chose the right answer!")
                generateFormula(correctAnswerCount, formulaType="addition")
            else:
                print("wrong answer!")
        elif userInput == "c":
            if answers["c"] == z:
                correctAnswerCount +=1
                print("you chose the right answer!")
                generateFormula(correctAnswerCount, formulaType="addition")
            else:
                print("wrong answer!")
        elif userInput == "exit":
            print(f"You got {correctAnswerCount} answers correct!")
            exit()
        else:
            print("incorrect input")


generateFormula(correctAnswerCount, "addition")
