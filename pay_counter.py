'''Pay Counter Module for Ben's Churro Spot'''
import time


class PayCounter:
    """Manages the final customer hand-off, order scoring, and tip collections."""

    def __init__(self):
        self.total_tips = 0.0

    def calculate_score(self, ticket, plate):
        """
        Compares the customer's Ticket with the completed Plate.
        Returns a dictionary of scores (0-100) and the final calculated tip.
        """
        # 1. Shape & Quantity Score
        shape_score = 100 if plate.get("shape") == ticket.shape else 0

        count_difference = abs(plate.get("count", 0) - ticket.num_churros)
        quantity_score = max(0, 100 - (count_difference * 25))
        dough_score = (shape_score + quantity_score) / 2

        # 2. Cook Score (Target is 15.0 seconds per side)
        s1_diff = abs(plate.get("side1_score", 0.0) - 15.0)
        s2_diff = abs(plate.get("side2_score", 0.0) - 15.0)

        # Deduct 5 points per second away from perfect cook time
        s1_score = max(0, 100 - (s1_diff * 5))
        s2_score = max(0, 100 - (s2_diff * 5))
        cook_score = (s1_score + s2_score) / 2

        # 3. Topping Score
        topping_matches = 0
        total_items_to_check = max(
            len(plate.get("churro_details", [])), ticket.num_churros)

        for i in range(total_items_to_check):
            # Safe indexing if item counts mismatch
            p_churro = plate["churro_details"][i] if i < len(
                plate["churro_details"]) else None
            t_churro = ticket.churro_details[i] if i < len(
                ticket.churro_details) else None

            if p_churro and t_churro:
                if p_churro.get("sauce") == t_churro["sauce"]:
                    topping_matches += 1
                if p_churro.get("topping") == t_churro["topping"]:
                    topping_matches += 1

        # Total possible matches is 2 per churro (sauce + topping)
        max_possible_matches = ticket.num_churros * 2
        topping_score = (topping_matches / max_possible_matches) * \
            100 if max_possible_matches > 0 else 0

        # 4. Waiting Time Score (Speed)
        elapsed_time = time.time() - ticket.order_time
        # Perfect score if under 45 seconds, drops down gradually over 3 minutes
        if elapsed_time <= 45:
            time_score = 100
        else:
            time_score = max(0, 100 - int((elapsed_time - 45) / 1.5))

        # Overall Average Score
        final_percentage = (dough_score + cook_score +
                            topping_score + time_score) / 4

        # Base maximum tip of $10.00 scaled down by performance
        earned_tip = round((final_percentage / 100.0) * 10.00, 2)

        return {
            "dough": round(dough_score, 1),
            "cook": round(cook_score, 1),
            "topping": round(topping_score, 1),
            "time": round(time_score, 1),
            "final_percentage": round(final_percentage, 1),
            "earned_tip": earned_tip
        }


# --- Central Module Interface Hooks ---

def display_menu():
    '''Display the menu for the Pay Counter station'''
    menu_text = (
        "\n=== PAY COUNTER ===\n"
        "4. Give Customer Plate\n"
        "5. Check Tip Jar Balance\n"
        "6. Back to Main Menu"
    )
    print(menu_text)
    return menu_text


def handle_input(choice, game_state):
    '''Handle input specific to the Pay Counter station'''
    pay_counter = game_state.get('pay_counter')
    front_counter = game_state.get('front_counter')

    if not pay_counter or not front_counter:
        print("[Error] Required module instances missing from game state.")
        return None

    # Fallback initialization for the pipeline incoming list
    if "topping_to_pay_queue" not in game_state:
        game_state["topping_to_pay_queue"] = []

    if choice == "4":
        customers = front_counter.waiting_customers
        plates = game_state["topping_to_pay_queue"]

        if not customers:
            print("\nThere are no customers currently waiting in line.")
            return "no_customers"
        if not plates:
            print("\nYou don't have any plates from the Topping Station ready to serve.")
            return "no_plates"

        # Display active customers waiting for food
        print("\n--- Choose a Customer to Serve ---")
        for idx, cust in enumerate(customers, 1):
            print(
                f"{idx}. {cust.name} (Waiting for: {cust.ticket.num_churros} {cust.ticket.shape} Churros)")

        try:
            cust_choice = int(input("Select Customer Number: ")) - 1
            if not (0 <= cust_choice < len(customers)):
                print("Invalid customer selection.")
                return "invalid"

            # Display prepared dishes ready to step out
            print("\n--- Select Finished Plate to Give Them ---")
            for idx, plt in enumerate(plates, 1):
                print(
                    f"{idx}. Plate with {plt.get('count')} {plt.get('shape')} churro(s)")

            plate_choice = int(input("Select Plate Number: ")) - 1
            if not (0 <= plate_choice < len(plates)):
                print("Invalid plate selection.")
                return "invalid"

            # Pull records out of active play queues
            active_customer = customers.pop(cust_choice)
            served_plate = plates.pop(plate_choice)
            customer_ticket = active_customer.ticket

            # Clean up the ticket tracking list inside main
            if "tickets" in game_state and customer_ticket in game_state["tickets"]:
                game_state["tickets"].remove(customer_ticket)

            # Score breakdown calculation
            scores = pay_counter.calculate_score(customer_ticket, served_plate)
            pay_counter.total_tips += scores["earned_tip"]

            # Visual Score Card Output
            print("\n===============================")
            print(f"      {active_customer.name}'s SCORE CARD      ")
            print("===============================")
            print(f" Dough Shape & Amount : {scores['dough']}%")
            print(f" Cook Timing Accuracy : {scores['cook']}%")
            print(f" Toppings Alignment   : {scores['topping']}%")
            print(f" Wait-Time & Speed    : {scores['time']}%")
            print("-------------------------------")
            print(f" Total Order Score    : {scores['final_percentage']}%")
            print(f" Tip Received         : ${scores['earned_tip']:.2f}")
            print("===============================")
            print(f"New Tip Jar Total: ${pay_counter.total_tips:.2f}")

            return "served_customer"

        except ValueError:
            print("Invalid character typing. Please input numbers only.")
            return "invalid"

    elif choice == "5":
        print(
            f"\n[💰 TIP JAR] Total tips collected this shift: ${pay_counter.total_tips:.2f}")
        return "viewed_tips"

    elif choice == "6":
        print("\nLeaving Pay Counter...")
        return "exit"

    else:
        print("Invalid choice. Please select 4, 5, or 6.")
        return "invalid"
