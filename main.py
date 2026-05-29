'''Main game loop'''

import os
import time
import random
import threading
import pickle

# Import the other station modules
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

    "front_counter": front_counter.FrontCounter(),
    "fry_station": fry_station.FryStation(),
    "pastry_station": pastry_station.PastryStation(),
    "topping_station": topping_station.ToppingStation(),
    "pay_counter": pay_counter.PayCounter()
}

stations = [
    "Front Counter",
    "Pastry Station",
    "Fry Station",
    "Topping Station",
    "Pay Counter"
]

# --- Helper Functions ---

SAVE_FILE_PKL = "savegame.pkl"

def check_save_file():
    """Checks if a Pickle save file exists."""
    return os.path.exists(SAVE_FILE_PKL)

def save_game_pickle(game_state):
    """Saves the entire complex game state (objects included) using Pickle."""
    print("\nSaving game progress...")
    try:
        # Note the "wb" (write binary) mode, which pickle requires
        with open(SAVE_FILE_PKL, "wb") as file:
            pickle.dump(game_state, file)
        print("Game saved successfully!")
    except Exception as e:
        print(f"\n[!] Save Error: {e}")

def load_game(game_state):
    """Loads an old save from a Pickle file."""
    print("Loading previous save data...")
    try:
        # Note the "rb" (read binary) mode
        with open(SAVE_FILE_PKL, "rb") as file:
            saved_data = pickle.load(file)

            # Clear current state and load in the saved state completely
            game_state.clear()
            game_state.update(saved_data)

        print(f"Welcome back to the shop, {game_state.get('character_name', 'Employee')}!")
        print("Save loaded successfully!\n")
    except Exception as e:
        print(f"\n[!] Failed to load save file: {e}")

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

def format_time(seconds):
    """Formats elapsed seconds into MM:SS format."""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"

# --- Background Threads ---

def customer_timer():
    """Runs in the background, adding a customer every 45-120 seconds (first is 5-10s)."""
    # Flag to track if we are waiting for the very first customer
    is_first_customer = True

    while game_state["is_running"]:
        # Set a short timer for the first customer, standard timer for the rest
        if is_first_customer:
            wait_time = random.randint(5, 10)
            is_first_customer = False
        else:
            wait_time = random.randint(45, 120)

        # Sleep in small increments so the thread can exit cleanly if the game closes
        for _ in range(wait_time):
            if not game_state["is_running"]:
                return
            time.sleep(1)

        # --- UNIQUE NAME LOGIC ---
        # 1. Compile a set of all customer names currently active in the shop
        existing_names = set()

        # Check pending tickets waiting at the door (dictionaries)
        for ticket in game_state["tickets"]:
            if isinstance(ticket, dict) and "name" in ticket:
                existing_names.add(ticket["name"])

        # Check customers who have already ordered at the front counter
        if game_state.get("front_counter"):
            for customer in game_state["front_counter"].waiting_customers:
                existing_names.add(customer.name)

        # --- 🚨 CUSTOMER CAP LOGIC 🚨 ---
        # If there are 8 or more customers currently in the shop, cancel spawning and wait again.
        if len(existing_names) >= 8:
            continue

        # 2. Filter out names that are already taken
        available_names = [
            name for name in front_counter.NAMES_POOL if name not in existing_names]

        # 3. Determine final name choice
        if available_names:
            arrival_name = random.choice(available_names)
        else:
            # Safeguard: if the shop is so full that ALL pool names are taken, append a suffix
            arrival_name = f"{random.choice(front_counter.NAMES_POOL)} II"

        # Add customer and ring bell
        new_ticket = {
            "name": arrival_name,
            "order": "Pending Order details..."
        }
        game_state["tickets"].append(new_ticket)

        # Print bell sound with their actual name!
        print(
            f"\n\r[🛎️ DING! {arrival_name} just walked in the door!] \n> ", end="")

# --- Main Game Loop ---


def main():
    '''Main function to run the game loop.'''
    if check_save_file():
        choice = input("Old save found! Would you like to (C)ontinue "
                       "or start a (N)ew game? [C/N]: ").strip().upper()
        if choice == 'C':
            load_game(game_state)
        else:
            start_new_game()
    else:
        start_new_game()

    game_state["start_time"] = time.time()

    customer_thread = threading.Thread(target=customer_timer, daemon=True)
    customer_thread.start()

    while game_state["is_running"]:
        elapsed_time = time.time() - game_state["start_time"]

        print(f"\n{'='*40}")
        print(f"🕒 Shift Time: {format_time(elapsed_time)}")
        print(f"📍 Current Station: {game_state['current_station']}")
        print(f"{'='*40}")

        print("1. Change Station")
        print("2. Check ticket total")
        print("3. Check ticket")

        print("\n--- Station Options ---")
        if game_state["current_station"] == "Front Counter":
            front_counter.display_menu()
        elif game_state["current_station"] == "Pastry Station":
            pastry_station.display_menu()
        elif game_state["current_station"] == "Fry Station":
            fry_station.display_menu()
        elif game_state["current_station"] == "Topping Station":
            topping_station.display_menu()
        elif game_state["current_station"] == "Pay Counter":
            pay_counter.display_menu()

        print("Q. Quit Game")
        print("-" * 40)

        choice = input("Select an option: ").strip().upper()

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
                    print("\n[ Ticket Details ]")

                    if hasattr(selected, 'shape'):
                        print(selected)
                    else:
                        print(f"Name: {selected['name']}")
                        print(f"Order: {selected['order']}")
                else:
                    print("Returning to menu.")
        elif choice == 'Q':
            print("Packing up for the day! Goodbye.")
            save_game_pickle(game_state)
            game_state["is_running"] = False

        else:
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
