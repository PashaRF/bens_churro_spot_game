'''Pastry Station Module for Churro Chef Game'''

# --- Configuration Constants ---
SHAPES = ["Straight", "Loop", "Spiral"]


class PastryStation:
    """Manages the creation and cutting of churro dough."""

    def __init__(self):
        # Keeps track of the total dough processed in this session
        self.total_dough_cut = 0

    def cut_churros(self, shape: str, amount: int, game_state: dict):
        """Creates churro dough and moves it to the fry station queue."""
        # Ensure the receiving queue exists in the global game state
        if "pastry_to_fry_queue" not in game_state:
            game_state["pastry_to_fry_queue"] = []

        # Add the raw dough to the pipeline
        for _ in range(amount):
            game_state["pastry_to_fry_queue"].append(shape)

        self.total_dough_cut += amount

        print(f"\n[🎨 PASTRY STATION] Success! Cut {amount} {shape} churro(s).")
        print("--> Moved to the Fry Station waiting queue.")


# --- Central Module Interface Hooks ---

def display_menu():
    '''Display the menu for the Pastry Station'''
    menu_text = (
        "\n=== PASTRY STATION ===\n"
        "4. Cut Churros\n"
        "5. Check Dough Queue\n"
        "6. Back to Main Menu"
    )
    print(menu_text)
    return menu_text


def handle_input(choice, game_state):
    '''Handle input specific to the Pastry Station'''
    # Extract the PastryStation instance from your central game state
    station = game_state.get('pastry_station')

    if not station:
        print("[Error] Pastry Station instance not found in game state.")
        return None

    if choice == "4":
        print("\n--- Select Churro Shape ---")
        for idx, shape in enumerate(SHAPES, 1):
            print(f"{idx}. {shape}")

        try:
            shape_choice = int(input("Enter choice (1-3): "))
            if 1 <= shape_choice <= len(SHAPES):
                chosen_shape = SHAPES[shape_choice - 1]

                print("\n--- Select Quantity ---")
                num_churros = int(input("How many churros to cut? (1-6): "))

                if 1 <= num_churros <= 6:
                    # Pass to the class method to process
                    station.cut_churros(chosen_shape, num_churros, game_state)
                    return "cut_churros"
                else:
                    print("Invalid amount! You can only cut between 1 and 6 churros at a time.")
            else:
                print("Invalid shape selection.")

        except ValueError:
            print("Invalid input typing. Please use numbers only.")

        return "invalid"

    elif choice == "5":
        # Check what is currently waiting for the fryer
        queue = game_state.get('pastry_to_fry_queue', [])
        print("\n--- Current Dough Pipeline ---")
        if not queue:
            print("The Fry Station waiting line is currently empty.")
        else:
            print(f"Dough units ready to drop: {queue}")
        return "view_queue"

    elif choice == "6":
        print("\nLeaving Pastry Station...")
        return "exit"

    else:
        print("Invalid choice. Please select 4, 5, or 6.")
        return "invalid"
