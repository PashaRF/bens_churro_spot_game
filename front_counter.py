"""Front counter"""
import random
import time


def display_menu(game_state):
    '''Display the menu for the Front Counter station'''
    menu_text = (
        "\n=== BEN'S CHURRO SPOT - FRONT COUNTER ===\n"
        "1. View waiting customer list\n"
        "2. Check for new customers\n"
        "3. Go to Next Station / Back to Main Menu"
    )
    print(menu_text)
    return menu_text


def handle_input(choice, game_state):
    '''Handle input specific to the Front Counter station'''
    # Extract the FrontCounter instance from your central game state
    counter = game_state.get('front_counter')
    
    if not counter:
        print("[Error] Front Counter instance not found in game state.")
        return None

    if choice == "1":
        counter.view_waiting_customers()
        return "viewed_customers"
        
    elif choice == "2":
        # Generates the ticket, prints order details, and adds customer to waiting list
        new_ticket = counter.check_for_new_customers()
        
        # If your game loop needs to instantly pass this ticket to the order queue:
        if 'order_tickets' in game_state:
            game_state['order_tickets'].append(new_ticket)
            
        return new_ticket  # Returns the ticket object so main.py can use it if needed
        
    elif choice == "3":
        print("\nLeaving Front Counter...")
        return "exit"
        
    else:
        print("Invalid choice. Please select 1, 2, or 3.")
        return "invalid"


# --- Configuration Constants ---
# You can expand these lists as you build out your game!
SAUCES = ["None", "Chocolate", "Caramel", "Condensed Milk", "Dulce de Leche"]
TOPPINGS = ["None", "Cinnamon Sugar",
            "Sprinkles", "Crushed Oreos", "Chopped Nuts"]
SHAPES = ["Straight", "Loop", "Spiral"]
NAMES_POOL = ["Papa Louie", "Wally", "Penny",
              "Cooper", "Prudence", "Taylor", "Peggy"]


class Ticket:
    """Represents the order details passed between stations."""

    def __init__(self, num_churros: int, shape: str, churro_details: list):
        self.num_churros = num_churros  # Int (1-6)
        self.shape = shape              # String (e.g., Straight, Loop)
        # List of dicts containing specific sauce/topping per churro
        self.churro_details = churro_details
        self.order_time = time.time()   # Stores the exact time the order was taken

    def __str__(self):
        details = f"\n--- TICKET DETAILS ---\nShape: {self.shape}\nAmount: {self.num_churros} Churro(s)\n"
        for i, churro in enumerate(self.churro_details, 1):
            details += f"  - Churro #{i}: Sauce: {churro['sauce']}, Topping: {churro['topping']}\n"
        return details


class Customer:
    """Represents a customer in the shop."""

    def __init__(self, name: str):
        self.name = name
        self.ticket = None  # Will hold the Ticket object once they order

    def __str__(self):
        return f"Customer: {self.name}"


class FrontCounter:
    """Manages the front counter operations: waiting lines and order taking."""

    def __init__(self):
        self.waiting_customers = []

    def view_waiting_customers(self):
        """Returns and displays the list of customers waiting for their orders."""
        if not self.waiting_customers:
            print("\n[Front Counter] No customers are currently waiting.")
            return []

        print("\n--- Waiting Customers ---")
        for idx, customer in enumerate(self.waiting_customers, 1):
            print(f"{idx}. {customer.name}")
        return self.waiting_customers

    def check_for_new_customers(self):
        """Simulates a new customer arriving and automatically takes their order."""
        print("\n[Front Counter] Checking for new customers...")

        # Create a random customer
        customer_name = random.choice(NAMES_POOL)
        new_customer = Customer(customer_name)

        # Generate random ticket details
        num_churros = random.randint(1, 6)
        chosen_shape = random.choice(SHAPES)

        churro_details = []
        for _ in range(num_churros):
            churro_details.append({
                "sauce": random.choice(SAUCES),
                "topping": random.choice(TOPPINGS)
            })

        # Create the ticket and link it to the customer
        new_ticket = Ticket(num_churros, chosen_shape, churro_details)
        new_customer.ticket = new_ticket

        # Add customer to the waiting list
        self.waiting_customers.append(new_customer)

        print(f"--> {new_customer.name} just walked in and placed an order!")
        print(new_ticket)

        # Pass the ticket forward (Returns the ticket so main.py can send it to pastry_station)
        return new_ticket