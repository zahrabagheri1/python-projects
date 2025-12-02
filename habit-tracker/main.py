
def load_habits():
    habits = {}
    try:
        with open("habits.txt","r") as f:
            for line in f:
                name, status = line.strip().split(",")
                habits[name] = status
    except FileNotFoundError:
        pass
    return habits

def save_habits(habits):
    with open("habits.txt", 'w')as f:
        for habit,status in habits.items():
            f.write(f"{habit},{status}\n")


def main():
    habits = load_habits()
    while True:
        print("\n1. View Habits\n2. Add Habit\n3. Mark Habit as done\n4. Exit")
        choice = input("Choose an option: ")

        if choice == "1":
            for habit, status in habits.items():
                print(f"{habit}:{'✅' if status == "done" else '❌'}")
        elif choice == "2":
            name = input("Enter your habit name: ")
            habits[name] = "Not done"
            print(f"Added '{name}' to your habit list.")
        elif choice == "3":
            name = input("Enter habit name to mark as done: ")
            if name in habits:
                habits[name] = "done" 
                print(f"Added '{name}' marked as completed!")
            else:
                print("Habit not found.")
        elif choice == "4":
            save_habits(habits)
            print("Progress saved, See you tomorrow")
            break

# calling the main function
if __name__ == "__main__":
    main()


            






