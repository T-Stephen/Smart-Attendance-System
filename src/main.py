from register_student import register_student
from recognize_faces import main as start_attendance


def show_menu():

    while True:

        print("\n" + "=" * 50)
        print(" SMART ATTENDANCE SYSTEM")
        print("=" * 50)
        print("1. Register Student")
        print("2. Capture Images (Coming Soon)")
        print("3. Train Model (Coming Soon)")
        print("4. Start Attendance")
        print("5. Exit")

        choice = input("\nEnter your choice: ")

        if choice == "1":
            register_student()

        elif choice == "2":
            print("\nCapture Images Module - Coming Soon")

        elif choice == "3":
            print("\nTrain Model Module - Coming Soon")

        elif choice == "4":
            start_attendance()

        elif choice == "5":
            print("\nThank you for using Smart Attendance System.")
            break

        else:
            print("\nInvalid Choice!")


if __name__ == "__main__":
    show_menu()