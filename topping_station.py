'''Topping Station Module for Ben's Churro Spot'''

# --- Configuration Constants ---
SAUCES = ["None", "Chocolate", "Caramel", "Condensed Milk", "Dulce de Leche"]
TOPPINGS = ["None", "Cinnamon Sugar", "Sprinkles", "Crushed Oreos", "Chopped Nuts"]


class ToppingStation:
    """Manages plating and decorating churros before serving."""

    def __init__(self):
        # Holds plates that are currently being worked on at the station
        self.active_plates = []

    def display_active_plates(self):
        """Helper method to print the plates currently on the counter."""
        if not self.active_plates:
            print("\n[!] No active plates on the counter.")
            return False

        print("\n--- Active Plates on Counter ---")
        for idx, plate in enumerate(self.active_plates, 1):
            print(f"{idx}. Plate with {plate['count']} {plate['shape']} Churro(s)")
            for c_idx, details in enumerate(plate['churro_details'], 1):
                print(f"   - Churro #{c_idx}: Topping: {details['topping']} | Sauce: {details['sauce']}")
        return True


# --- Central Module Interface Hooks ---

def display_menu():
    '''Display the menu for the Topping Station'''
    menu_text = (
        "\n=== TOPPING STATION ===\n"
        "4. Plate Churros (Pull from Fryer queue)\n"
        "5. Add Toppings\n"
        "6. Add a Sauce\n"
        "7. Move Plate to Pay Counter\n"
        "8. Back to Main Menu"
    )
    print(menu_text)
    return menu_text


def handle_input(choice, game_state):
    '''Handle input specific to the Topping Station'''
    station = game_state.get('topping_station')

    if not station:
        print("[Error] Topping Station instance not found in game state.")
        return None

    # Ensure pipeline queues exist
    if "fry_to_topping_queue" not in game_state:
        game_state["fry_to_topping_queue"] = []
    if "topping_to_pay_queue" not in game_state:
        game_state["topping_to_pay_queue"] = []

    if choice == "4":
        fry_queue = game_state["fry_to_topping_queue"]
        if not fry_queue:
            print("\n[!] There are no fried churros waiting from the Fry Station.")
            return "no_churros"

        print("\n--- Fried Churros Waiting to be Plated ---")
        for idx, batch in enumerate(fry_queue, 1):
            print(f"{idx}. {batch['count']}x {batch['shape']} (Cooked -> S1: {batch['side1_score']}s, S2: {batch['side2_score']}s)")

        try:
            batch_choice = int(input("Select which batch to plate: ")) - 1
            if 0 <= batch_choice < len(fry_queue):
                # Pull the batch from the fryer queue
                pulled_batch = fry_queue.pop(batch_choice)

                # Check if there are active plates to add to
                action = "1"
                if station.active_plates:
                    print("\n--- Plating Options ---")
                    print("1. Create a NEW plate")
                    print("2. Add to an EXISTING plate")
                    action = input("Select option (1 or 2): ").strip()

                if action == "2" and station.active_plates:
                    station.display_active_plates()
                    try:
                        plate_idx = int(input("\nWhich plate do you want to add these to? ")) - 1
                        if 0 <= plate_idx < len(station.active_plates):
                            target_plate = station.active_plates[plate_idx]

                            # Merge data
                            target_plate["count"] += pulled_batch["count"]

                            # Average out the cook scores for the final plate grade
                            target_plate["side1_score"] = round((target_plate["side1_score"] + pulled_batch["side1_score"]) / 2, 1)
                            target_plate["side2_score"] = round((target_plate["side2_score"] + pulled_batch["side2_score"]) / 2, 1)

                            # Add the new blank churros to the details array
                            target_plate["churro_details"].extend([{"sauce": "None", "topping": "None"} for _ in range(pulled_batch["count"])])

                            print(f"\n[🍽️] Added {pulled_batch['count']} {pulled_batch['shape']} churro(s) to Plate #{plate_idx + 1}!")
                        else:
                            print("Invalid plate selection. Creating a new plate instead.")
                            action = "1"
                    except ValueError:
                        print("Invalid input. Creating a new plate instead.")
                        action = "1"

                # If they chose 1, or if adding to an existing plate failed/was unavailable
                if action == "1":
                    # Initialize the churro_details list for the exact number of churros
                    pulled_batch["churro_details"] = [{"sauce": "None", "topping": "None"} for _ in range(pulled_batch["count"])]
                    # Add to our active workbench
                    station.active_plates.append(pulled_batch)
                    print(f"\n[🍽️] Successfully created a new plate with {pulled_batch['count']} {pulled_batch['shape']} churro(s)!")

            else:
                print("Invalid batch selection.")
        except ValueError:
            print("Please enter a valid number.")

        return "plated_churros"

    elif choice == "5":
        if not station.display_active_plates():
            return "no_active_plates"

        try:
            p_choice = int(input("\nSelect Plate Number to decorate: ")) - 1
            if 0 <= p_choice < len(station.active_plates):
                target_plate = station.active_plates[p_choice]

                # --- Menu Loop for Toppings & Ticket Checking ---
                while True:
                    print("\n--- Available Toppings ---")
                    for i, top in enumerate(TOPPINGS, 1):
                        print(f"{i}. {top}")
                    print("T. Check Active Tickets")
                    print("C. Cancel and Go Back")

                    t_input = input("Select Topping (or T/C): ").strip().upper()

                    # Handle ticket checking
                    if t_input == "T":
                        tickets = game_state.get("tickets", [])
                        if not tickets:
                            print("\nYou have no active tickets right now.")
                        else:
                            print("\n=== CURRENT ACTIVE TICKETS ===")
                            for i, ticket in enumerate(tickets, 1):
                                if hasattr(ticket, 'shape'):
                                    print(f"\n[Ticket #{i}]" + str(ticket))
                                else:
                                    print(f"\n[Ticket #{i}] Name: {ticket['name']} (Waiting at Door)")
                            print("==============================")
                        continue  # Return to the topping list display

                    # Handle cancel
                    if t_input == "C":
                        print("\nCanceling topping addition...")
                        break

                    # Handle numerical selection
                    try:
                        t_choice = int(t_input) - 1
                        if 0 <= t_choice < len(TOPPINGS):
                            selected_topping = TOPPINGS[t_choice]

                            amt = input("Select amount (Light / Normal / Heavy): ").strip().title()
                            if not amt: amt = "Normal"

                            for churro in target_plate['churro_details']:
                                churro['topping'] = selected_topping
                            print(f"\n[✨] Added a {amt} amount of {selected_topping} to churros on plate #{p_choice + 1}.")
                            break  # Break out of the loop since item was applied successfully
                        else:
                            print("Invalid topping choice.")
                    except ValueError:
                        print("Please enter a valid option (Number, T, or C).")
            else:
                print("Invalid plate selection.")
        except ValueError:
            print("Please enter valid numbers for plate selection.")

        return "added_topping"

    elif choice == "6":
        if not station.display_active_plates():
            return "no_active_plates"

        try:
            p_choice = int(input("\nSelect Plate Number to sauce: ")) - 1
            if 0 <= p_choice < len(station.active_plates):
                target_plate = station.active_plates[p_choice]
                
                # --- Menu Loop for Sauces & Ticket Checking ---
                while True:
                    print("\n--- Available Sauces ---")
                    for i, sauce in enumerate(SAUCES, 1):
                        print(f"{i}. {sauce}")
                    print("T. Check Active Tickets")
                    print("C. Cancel and Go Back")

                    s_input = input("Select Sauce (or T/C): ").strip().upper()

                    # Handle ticket checking
                    if s_input == "T":
                        tickets = game_state.get("tickets", [])
                        if not tickets:
                            print("\nYou have no active tickets right now.")
                        else:
                            print("\n=== CURRENT ACTIVE TICKETS ===")
                            for i, ticket in enumerate(tickets, 1):
                                if hasattr(ticket, 'shape'):
                                    print(f"\n[Ticket #{i}]" + str(ticket))
                                else:
                                    print(f"\n[Ticket #{i}] Name: {ticket['name']} (Waiting at Door)")
                            print("==============================")
                        continue  # Return to the sauce list display

                    # Handle cancel
                    if s_input == "C":
                        print("\nCanceling sauce addition...")
                        break

                    # Handle numerical selection
                    try:
                        s_choice = int(s_input) - 1
                        if 0 <= s_choice < len(SAUCES):
                            selected_sauce = SAUCES[s_choice]

                            style = input("Select style (Drizzled / On the Side): ").strip().title()
                            if not style: style = "Drizzled"

                            for churro in target_plate['churro_details']:
                                churro['sauce'] = selected_sauce
                            print(f"\n[🍯] Added {selected_sauce} ({style}) to churros on Plate #{p_choice + 1}.")
                            break  # Break out of the loop since item was applied successfully
                        else:
                            print("Invalid sauce choice.")
                    except ValueError:
                        print("Please enter a valid option (Number, T, or C).")
            else:
                print("Invalid plate selection.")
        except ValueError:
            print("Please enter valid numbers for plate selection.")

        return "added_sauce"

    elif choice == "7":
        if not station.display_active_plates():
            return "no_active_plates"

        try:
            p_choice = int(input("\nSelect Plate Number to send to Pay Counter: ")) - 1
            if 0 <= p_choice < len(station.active_plates):
                finished_plate = station.active_plates.pop(p_choice)
                game_state["topping_to_pay_queue"].append(finished_plate)
                print(f"\n[🛎️] Order up! Sent plate of {finished_plate['count']} {finished_plate['shape']} churro(s) to the Pay Counter.")
            else:
                print("Invalid plate selection.")
        except ValueError:
            print("Please enter a valid number.")

        return "sent_plate"

    elif choice == "8":
        print("\nLeaving Topping Station...")
        return "exit"

    else:
        print("Invalid choice. Please select an option between 4 and 8.")
        return "invalid"
