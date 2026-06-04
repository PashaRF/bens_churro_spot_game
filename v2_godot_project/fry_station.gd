extends Control

# Data structure class tracking backend variables away from visual layers
class FrySlotData:
	var shape: String = ""
	var count: int = 1
	var side1_time: float = 0.0
	var side2_time: float = 0.0
	var is_flipped: bool = false

const OPTIMAL_COOK_TIME: float = 50.0 # 50 seconds matching original Python logic

var vats: Dictionary = {}         # Holds internal data slots 1-8
var visual_cards: Dictionary = {}  # Holds references to visual layout nodes 1-8

@onready var dough_list_ui: ItemList = $HBoxContainer/LeftSidebar/DoughItemList

func _ready() -> void:
	# Force-populate some mock placeholder dough into the queue if testing empty
	if GlobalState.pastry_to_fry_queue.is_empty():
		GlobalState.pastry_to_fry_queue.append("Straight")
		GlobalState.pastry_to_fry_queue.append("Loop")
		GlobalState.pastry_to_fry_queue.append("Spiral")

	# Initialize backend structures and map visual cards
	for i in range(1, 9):
		vats[i] = FrySlotData.new()
		
		# Locate node dynamically using string manipulation
		var path = "HBoxContainer/MainKitchenArea/FryerGrid/FryerSlotCard%d" % i
		var card_node = get_node(path)
		
		if card_node:
			visual_cards[i] = card_node
			card_node.slot_id = i
			
			# Wire card button signals up to our central dispatcher
			card_node.card_action_triggered.connect(_on_slot_action_triggered)
	
	update_dough_bin_ui()

# Refresh the sidebar bin to accurately mirror GlobalState array values
func update_dough_bin_ui() -> void:
	dough_list_ui.clear()
	for dough_shape in GlobalState.pastry_to_fry_queue:
		dough_list_ui.add_item(dough_shape + " Dough")

# Continuous frame processing engine calculations loop
func _process(delta: float) -> void:
	for i in range(1, 9):
		var data = vats[i]
		var card = visual_cards[i]
		
		if data.count > 0 and data.shape != "":
			# Tick active countdown timers upward based on active state position
			if not data.is_flipped:
				data.side1_time += delta
				card.update_cooking_state(data.shape, data.count, data.side1_time, OPTIMAL_COOK_TIME, false)
			else:
				data.side2_time += delta
				card.update_cooking_state(data.shape, data.count, data.side2_time, OPTIMAL_COOK_TIME, true)
		else:
			card.set_empty_state()

# The Central Signal Dispatcher Router
func _on_slot_action_triggered(action: String, slot_num: int) -> void:
	match action:
		"flip":
			# If the slot is blank, "Flip" acts as a Load button
			if vats[slot_num].shape == "":
				handle_load_action(slot_num)
			else:
				handle_flip_action(slot_num)
		"pull":
			handle_pull_action(slot_num)

func handle_load_action(slot_num: int) -> void:
	# Ensure the player highlighted an item inside the sidebar list box
	var selected_indexes = dough_list_ui.get_selected_items()
	if selected_indexes.is_empty():
		print("⚠️ Select a dough shape from the left sidebar bin first!")
		return
		
	var selected_idx = selected_indexes[0]
	
	# Extract the shape from the raw data pipeline queue array
	var chosen_shape = GlobalState.pastry_to_fry_queue.pop_at(selected_idx)
	
	# Assign parameters to slot backend memory
	var data = vats[slot_num]
	data.shape = chosen_shape
	data.count = randi_range(2, 4) # Spawns a small structural batch size
	data.side1_time = 0.0
	data.side2_time = 0.0
	data.is_flipped = false
	
	print("🧺 Loaded %d %s dough bundles into Vat #%d!" % [data.count, chosen_shape, slot_num])
	update_dough_bin_ui()

func handle_flip_action(slot_num: int) -> void:
	var data = vats[slot_num]
	if not data.is_flipped:
		data.is_flipped = true
		print("🔄 Flipped Vat #%d! Side 1 finished cooking at: %d seconds." % [slot_num, int(data.side1_time)])

func handle_pull_action(slot_num: int) -> void:
	var data = vats[slot_num]
	
	# Package item metrics context dictionary array to pass downstream to the next room
	var cooked_batch = {
		"shape": data.shape,
		"count": data.count,
		"side1_score": data.side1_time,
		"side2_score": data.side2_time,
		"churro_details": [] # Will receive sugar additions in the Topping Station room
	}
	
	# Append directly into assembly collection array pipelines
	GlobalState.fry_to_topping_queue.append(cooked_batch)
	print("🛎️ Pulled Vat #%d! Sent to Topping Station. (S1: %ds, S2: %ds)" % [slot_num, int(data.side1_time), int(data.side2_time)])
	
	# Wipe slot properties back to clean initialization status parameters
	data.shape = ""
	data.count = 0
