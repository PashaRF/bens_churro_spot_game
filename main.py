'''Main game loop'''

import os
import time
import random
import threading

# Import the other station modules
# Ensure these files are in the same directory and have appropriate functions!
import front_counter
import pastry_station
import fry_station
import topping_station
import pay_counter

# --- Game State ---
game_state = {
    "is_running": True,
    "character_name": "",
    "current_station": "Front Counter",
    "tickets": [],
    "start_time": 0,

    # ADD THIS LINE TO FIX THE ERROR:
    "front_counter": front_counter.FrontCounter(),
    "fry_station": fry_station.FryStation()
}

stations = [
    "Front Counter",
    "Pastry Station",
    "Fry Station",
    "Topping Station",
    "Pay Counter"
]

# --- Helper Functions ---


def check_save_file():
    """Checks if a mock save file exists."""
    return os.path.exists("savegame.txt")


def start_new_game():
    """Initializes a new game and prints the intro."""
    print("\n--- Welcome to Ben's Churro Spot! ---")
    game_state["character_name"] = input("Enter your character's name: ")

    print(f"\nWelcome aboard, {game_state['character_name']}!")
    print("Here is how it works: You will take orders at the Front Counter,")
    print("pipe the dough at the Pastry Station, fry them up at the Fry Station,")
    print("add delicious toppings at the Topping Station, and cash them out")
    print("at the Pay Counter. Keep an eye on your tickets and the clock!")

    input("\nPress ENTER to start your shift...")


def load_game():
    """Mock function to load an old save."""
    print("Loading previous save data...")
    # Add your actual file reading logic here
    game_state["character_name"] = "Returning Employee"
    print("Save loaded successfully!\n")


def format_time(seconds):
    """Formats elapsed seconds into MM:SS format."""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"

# --- Background Threads ---


def customer_timer():
    """Runs in the background, adding a customer every 45-120 seconds."""
    while game_state["is_running"]:
        # Wait a random amount of time between 45 and 120 seconds
        wait_time = random.randint(45, 120)

        # Sleep in small increments so the thread can exit cleanly if the game closes
        for _ in range(wait_time):
            if not game_state["is_running"]:
                return
            time.sleep(1)

        # Add customer and ring bell
        new_ticket = {
            "name": f"Customer_{random.randint(100, 999)}",
            "order": "Pending Order details..."
        }
        game_state["tickets"].append(new_ticket)

        # Print bell sound (the \r clears the current input line momentarily to print this)
        print(
            "\n\r[🛎️ DING! A new customer has arrived at the Front Counter!] \n> ", end="")

# --- Main Game Loop ---


def main():
    '''Main function to run the game loop.'''
    # 1. Boot up and Save Check
    if check_save_file():
        choice = input("Old save found! Would you like to (C)ontinue "
                       "or start a (N)ew game? [C/N]: ").strip().upper()
        if choice == 'C':
            load_game()
        else:
            start_new_game()
    else:
        start_new_game()

    # 2. Start Clock & Customer Timer
    game_state["start_time"] = time.time()

    customer_thread = threading.Thread(target=customer_timer, daemon=True)
    customer_thread.start()

    # 3. Game Tick (Do-While equivalent)
    while game_state["is_running"]:
        elapsed_time = time.time() - game_state["start_time"]

        print(f"\n{'='*40}")
        print(f"🕒 Shift Time: {format_time(elapsed_time)}")
        print(f"📍 Current Station: {game_state['current_station']}")
        print(f"{'='*40}")

        # Display Standard Menu
        print("1. Change Station")
        print("2. Check ticket total")
        print("3. Check ticket")

        # Call specific station menus dynamically based on location
        print("\n--- Station Options ---")
        if game_state["current_station"] == "Front Counter":
            front_counter.display_menu(game_state)
        elif game_state["current_station"] == "Pastry Station":
            pastry_station.display_menu(game_state)
        elif game_state["current_station"] == "Fry Station":
            fry_station.display_menu(game_state)
        elif game_state["current_station"] == "Topping Station":
            topping_station.display_menu(game_state)
        elif game_state["current_station"] == "Pay Counter":
            pay_counter.display_menu(game_state)

        print("Q. Quit Game")
        print("-" * 40)

        # Wait for user input
        choice = input("Select an option: ").strip().upper()

        # Process Main Menu Inputs
        if choice == '1':
            print("\nAvailable Stations:")
            for i, station in enumerate(stations):
                if station != game_state["current_station"]:
                    print(f"- {station}")

            new_station = input(
                "Type the name of the station to move to: ").strip().title()
            if new_station in stations and new_station != game_state["current_station"]:
                game_state["current_station"] = new_station
                print(f"Walking to {new_station}...")
            else:
                print("Invalid station name or you are already there.")

        elif choice == '2':
            print(f"\nTotal active tickets: {len(game_state['tickets'])}")

        elif choice == '3':
            if not game_state['tickets']:
                print("\nYou have no active tickets.")
            else:
                print("\n--- Active Tickets ---")
                for i, ticket in enumerate(game_state['tickets']):
                    # Check if it's a Ticket object or a background thread dictionary
                    if hasattr(ticket, 'shape'):
                        print(
                            f"Ticket {i+1}: {ticket.num_churros} {ticket.shape} Churros")
                    else:
                        print(
                            f"Ticket {i+1}: {ticket['name']} (Waiting at Door)")

                t_choice = input(
                    "Enter ticket number to view details (or press enter to cancel): ")
                if t_choice.isdigit() and 1 <= int(t_choice) <= len(game_state['tickets']):
                    selected = game_state['tickets'][int(t_choice)-1]
                    print(f"\n[ Ticket Details ]")

                    # Print dynamically based on data structure type
                    if hasattr(selected, 'shape'):
                        # This safely calls the __str__ definition inside front_counter.py
                        print(selected)
                    else:
                        print(f"Name: {selected['name']}")
                        print(f"Order: {selected['order']}")
                else:
                    print("Returning to menu.")
        elif choice == 'Q':
            print("Packing up for the day! Goodbye.")
            # We can put save logic here later
            game_state["is_running"] = False

        else:
            # If it's not a main menu option, pass the input to the active station
            if game_state["current_station"] == "Front Counter":
                front_counter.handle_input(choice, game_state)
            elif game_state["current_station"] == "Pastry Station":
                pastry_station.handle_input(choice, game_state)
            elif game_state["current_station"] == "Fry Station":
                fry_station.handle_input(choice, game_state)
            elif game_state["current_station"] == "Topping Station":
                topping_station.handle_input(choice, game_state)
            elif game_state["current_station"] == "Pay Counter":
                pay_counter.handle_input(choice, game_state)


if __name__ == "__main__":
    main()
