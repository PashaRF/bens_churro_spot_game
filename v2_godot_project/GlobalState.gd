
extends Node

# --- Core Metrics & Configurations ---
var character_name: String = ""
var current_station: String = "Front Counter"
var is_running: bool = true
var elapsed_shift_time: float = 0.0

# --- Live Shift Data Queues ---
var waiting_at_door: Array[Dictionary] = []  # Customers waiting to place an order
var tickets: Array[Ticket] = []              # Active structural kitchen order tickets
var waiting_customers: Array[Customer] = []   # Customers who have ordered, waiting for food

# --- Inter-Station Production Assembly Lines ---
var pastry_to_fry_queue: Array[String] = []       # Uncooked dough shapes ("Straight", "Loop", etc.)
var fry_to_topping_queue: Array[Dictionary] = []  # Fried churros waiting for plates
var topping_to_pay_queue: Array[Dictionary] = []   # Completed plates waiting to be cashed out

# --- Product Constant Pools ---
const SAUCES = ["None", "Chocolate", "Caramel", "Condensed Milk", "Dulce de Leche"]
const TOPPINGS = ["None", "Cinnamon Sugar", "Sprinkles", "Crushed Oreos", "Chopped Nuts"]
const SHAPES = ["Straight", "Loop", "Spiral"]
const NAMES_POOL = ["Papa Louie", "Wally", "Penny", "Cooper", "Prudence", "Taylor", "Peggy"]

# Safe alternative to Python's binary Pickle system - saves via clean JSON string
func save_game_json() -> void:
	var save_data = {
		"character_name": character_name,
		"elapsed_shift_time": elapsed_shift_time,
		"pastry_queue": pastry_to_fry_queue,
		"fry_queue": fry_to_topping_queue
	}
	var file = FileAccess.open("user://savegame.json", FileAccess.WRITE)
	if file:
		file.store_string(JSON.stringify(save_data))
		print("Shift details auto-saved cleanly to user data folder!")
