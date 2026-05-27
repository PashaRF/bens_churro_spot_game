'''Fry Station Module for Churro Chef Game'''
import time

def display_menu(game_state):
    '''Display the menu for the Fry Station'''
    menu_text = (
        "\n=== FRY STATION ===\n"
        "4. Check Fryers (View all 8)\n"
        "5. Check Specific Fryer\n"
        "6. Add Churro to Fryer\n"
        "7. Remove Churro (Move to Topping Station queue)\n"
        "8. Flip Churro(s)\n"
        "9. Back to Main Menu"
    )
    print(menu_text)
    return menu_text


def handle_input(choice, game_state):
    '''Handle input specific to the Fry Station'''
    # Extract the FryStation instance from the central game state
    station = game_state.get('fry_station')

    if not station:
        print("[Error] Fry Station instance not found in game state.")
        return None

    # Ensure intermediate data queues exist in game_state
    if "pastry_to_fry_queue" not in game_state:
        game_state["pastry_to_fry_queue"] = []
    if "fry_to_topping_queue" not in game_state:
        game_state["fry_to_topping_queue"] = []

    if choice == "4":
        station.display_all_fryers()
        return "checked_all"

    elif choice == "5":
        try:
            num = int(input("Enter Fryer Number (1-8): "))
            station.display_specific_fryer(num)
        except ValueError:
            print("Please enter a valid number.")
        return "checked_specific"

    elif choice == "6":
        if not game_state["pastry_to_fry_queue"]:
            print("\n[!] No churro dough available from the Pastry Station! Go pipe some first.")
            return "no_dough"

        print(f"\nAvailable Dough Shapes in Queue: {game_state['pastry_to_fry_queue']}")
        chosen_shape = input("Type dough shape to load (or press enter to cancel): ").strip().title()

        if chosen_shape in game_state["pastry_to_fry_queue"]:
            try:
                f_num = int(input("Choose an empty Fryer (1-8): "))
                if f_num in station.fryers and station.fryers[f_num].count == 0:
                    qty = int(input("How many to drop? (1 or 2): "))
                    if qty in [1, 2]:
                        available_count = game_state["pastry_to_fry_queue"].count(chosen_shape)
                        if available_count >= qty:
                            # Remove dough from the pastry queue
                            for _ in range(qty):
                                game_state["pastry_to_fry_queue"].remove(chosen_shape)
                            # Load the fryer
                            station.fryers[f_num].add_churros(chosen_shape, qty)
                            print(f"\nDropped {qty} {chosen_shape} churro(s) into Fryer #{f_num}!")
                        else:
                            print(f"You don't have {qty} units of {chosen_shape} ready.")
                    else:
                        print("Invalid quantity. Max capacity is 2.")
                else:
                    print(f"Fryer #{f_num} is busy or invalid.")
            except ValueError:
                print("Invalid numerical entry.")
        elif chosen_shape != "":
            print("That shape isn't sitting in the pastry queue.")

        return "added_churro"

    elif choice == "7":
        try:
            f_num = int(input("Remove churros from which Fryer? (1-8): "))
            if f_num in station.fryers:
                fryer = station.fryers[f_num]
                if fryer.count > 0:
                    side1, side2 = fryer.get_cook_times()

                    # Package cooked churro data
                    fried_package = {
                        "shape": fryer.shape,
                        "count": fryer.count,
                        "side1_score": side1,
                        "side2_score": side2
                    }

                    # Move to station waiting list and game_state queue for topping station
                    station.fry_waiting_list.append(fried_package)
                    game_state["fry_to_topping_queue"].append(fried_package)

                    print(f"\nPulled {fryer.count} {fryer.shape} churro(s) from Fryer #{f_num}!")
                    print(f"Final Cook Profile -> Side 1: {side1}s, Side 2: {side2}s")
                    fryer.clear()
                else:
                    print("That fryer is already empty.")
            else:
                print("Invalid Fryer choice.")
        except ValueError:
            print("Please input valid numbers.")

        return "removed_churro"

    elif choice == "8":
        try:
            f_num = int(input("Flip churros in which Fryer? (1-8): "))
            if f_num in station.fryers:
                success = station.fryers[f_num].flip()
                if success:
                    print(f"\n[🔄] Flipped churros in Fryer #{f_num}!")
                else:
                    print("Could not flip. Fryer might be empty or already flipped.")
            else:
                print("Invalid Fryer choice.")
        except ValueError:
            print("Please input valid numbers.")

        return "flipped_churro"

    elif choice == "9":
        print("\nLeaving Fry Station...")
        return "exit"

    else:
        print("Invalid choice. Please select an option between 4 and 9.")
        return "invalid"

# --- Configuration Constants ---
SHAPES = ["Straight", "Loop", "Spiral"]
COOK_TIME_PER_SIDE = 15.0  # Perfect cook time per side in seconds


class Fryer:
    """Represents an individual fryer slot."""

    def __init__(self, id_num: int):
        self.id_num = id_num
        self.shape = None          # Shape of churros inside (e.g., "Straight")
        self.count = 0             # Number of churros (0, 1, or 2)

        # Cooking timestamps
        self.added_time = None
        self.flipped_time = None
        self.is_flipped = False

    def add_churros(self, shape: str, count: int):
        """Loads churros into the fryer."""
        self.shape = shape
        self.count = count
        self.added_time = time.time()
        self.flipped_time = None
        self.is_flipped = False

    def flip(self):
        """Flips the churros to cook the other side."""
        if self.count > 0 and not self.is_flipped:
            self.flipped_time = time.time()
            self.is_flipped = True
            return True
        return False

    def get_cook_times(self):
        """Calculates dynamic cook times for side 1 and side 2 based on real time."""
        if self.count == 0:
            return 0.0, 0.0

        current_time = time.time()

        if not self.is_flipped:
            side1_time = current_time - self.added_time
            side2_time = 0.0
        else:
            side1_time = self.flipped_time - self.added_time
            side2_time = current_time - self.flipped_time

        return round(side1_time, 1), round(side2_time, 1)

    def clear(self):
        """Empties the fryer."""
        self.shape = None
        self.count = 0
        self.added_time = None
        self.flipped_time = None
        self.is_flipped = False


class FryStation:
    """Manages all 8 fryers and the station's waiting lines."""

    def __init__(self):
        # Create 8 fryers (Numbered 1 to 8)
        self.fryers = {i: Fryer(i) for i in range(1, 9)}
        # Waiting list for fried churros waiting to go to the topping station
        self.fry_waiting_list = []

    def display_all_fryers(self):
        """Displays the capacity status of all 8 fryers."""
        print("\n--- Fryer Statuses ---")
        for i in range(1, 9):
            fryer = self.fryers[i]
            shape_str = f"({fryer.shape})" if fryer.shape else ""
            print(f"Fryer #{i}: [{fryer.count}/2] churros cooked {shape_str}")

    def display_specific_fryer(self, fryer_num: int):
        """Displays detailed cooking information for a targeted fryer."""
        if fryer_num not in self.fryers:
            print("Invalid fryer number.")
            return

        fryer = self.fryers[fryer_num]
        if fryer.count == 0:
            print(f"\n[Fryer #{fryer_num}] is currently empty.")
            return

        side1, side2 = fryer.get_cook_times()
        print(f"\n--- Detailed Status: Fryer #{fryer_num} ---")
        print(f"Churro Type: {fryer.shape}")
        print(f"Quantity: {fryer.count}")
        print(f"Side 1 Cooked: {side1}s / {COOK_TIME_PER_SIDE}s")
        print(f"Side 2 Cooked: {side2}s / {COOK_TIME_PER_SIDE}s")

        # Quality feedback
        if not fryer.is_flipped:
            status = "Frying Side 1 (Needs Flip!)" if side1 < COOK_TIME_PER_SIDE else "Side 1 OVERCOOKING! (FLIP NOW!)"
        else:
            status = "Frying Side 2" if side2 < COOK_TIME_PER_SIDE else "Side 2 OVERCOOKING! (PULL NOW!)"
        print(f"Current State: {status}")
