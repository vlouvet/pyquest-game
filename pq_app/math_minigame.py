import random

def generate_formula(correct_answer_count=0, formula_type="addition"):
    if formula_type == "addition":
        var_x = random.randrange(1, 50)
        var_y = random.randrange(1, 50)
        var_z = var_x + var_y
        print(f"What is the answer to X ({var_x})+ Y({var_y})?")
        answer_list = [random.randrange(1, 100), random.randrange(1, 100), var_z]
        answer_list = random.sample(answer_list, len(answer_list))
        answers = {"a": answer_list[0], "b": answer_list[1], "c": answer_list[2]}
        user_input = input(f"A:{answers['a']}\nB:{answers['b']}\nC:{answers['c']}\n\n")
        if user_input == "a":
            if answers["a"] == var_z:
                correct_answer_count +=1
                print("you chose the right answer!")
                generate_formula(correct_answer_count, formula_type="addition")
            else:
                print("wrong answer!")
        elif user_input == "b":
            if answers["b"] == var_z:
                correct_answer_count +=1
                print("you chose the right answer!")
                generate_formula(correct_answer_count, formula_type="addition")
            else:
                print("wrong answer!")
        elif user_input == "c":
            if answers["c"] == var_z:
                correct_answer_count +=1
                print("you chose the right answer!")
                generate_formula(correct_answer_count, formula_type="addition")
            else:
                print("wrong answer!")
        elif user_input == "exit":
            print(f"You got {correct_answer_count} answers correct!")
            exit()
        else:
            print("incorrect input")


generate_formula(0, "addition")
