extends Control

# Ideal cooking targets set inside the Fry Station rules
const IDEAL_COOK_TARGET: float = 50.0

@onready var customer_list_ui: ItemList = $MainLayout/SelectionSplits/CustomerSection/CustomerList
@onready var plate_list_ui: ItemList = $MainLayout/SelectionSplits/PlateSection/PlateList
@onready var results_label: Label = $MainLayout/ActionArea/ResultsLabel
@onready var serve_button: Button = $MainLayout/ActionArea/ServeButton

func _ready() -> void:
	# Inject some dummy debug test items into global memory if testing this room completely empty
	_inject_test_data_if_empty()
	
	# Connect the serve button to our scoring calculation function
	serve_button.pressed.connect(_on_serve_button_pressed)
	
	# Update lists right on room entry
	render_lists_ui()

func _inject_test_data_if_empty() -> void:
	if GlobalState.waiting_customers.is_empty():
		var mock_ticket = Ticket.new(1, "Straight", [{"sauce": "Chocolate", "topping": "Sprinkles"}])
		var mock_cust = Customer.new("Papa Louie")
		mock_cust.ticket = mock_ticket
		GlobalState.waiting_customers.append(mock_cust)
		
	if GlobalState.topping_to_pay_queue.is_empty():
		var mock_plate = {
			"shape": "Straight",
			"count": 1,
			"side1_score": 51.5,
			"side2_score": 49.0,
			"churro_details": [{"sauce": "Chocolate", "topping": "Sprinkles"}]
		}
		GlobalState.topping_to_pay_queue.append(mock_plate)

func render_lists_ui() -> void:
	customer_list_ui.clear()
	plate_list_ui.clear()
	
	# 1. Render all active customers waiting in the dining area
	for cust in GlobalState.waiting_customers:
		var summary = "%s (Wants %dx %s)" % [cust.name, cust.ticket.num_churros, cust.ticket.shape]
		customer_list_ui.add_item(summary)
		
	# 2. Render all finished plates sitting under the heat lamps
	for idx in range(GlobalState.topping_to_pay_queue.size()):
		var plate = GlobalState.topping_to_pay_queue[idx]
		var details = "Plate #%d: [%s] x%d" % [idx + 1, plate.get("shape"), plate.get("count")]
		plate_list_ui.add_item(details)

func _on_serve_button_pressed() -> void:
	var selected_cust_indexes = customer_list_ui.get_selected_items()
	var selected_plate_indexes = plate_list_ui.get_selected_items()
	
	# Validation Check: Ensure the player selected one item from BOTH lists
	if selected_cust_indexes.is_empty() or selected_plate_indexes.is_empty():
		results_label.text = "⚠️ You must highlight a Customer AND a Plate first!"
		return
		
	var cust_idx = selected_cust_indexes[0]
	var plate_idx = selected_plate_indexes[0]
	
	# Pull the actual data structures out of our background Global State arrays
	var target_customer = GlobalState.waiting_customers[cust_idx]
	var target_plate = GlobalState.topping_to_pay_queue[plate_idx]
	
	# Run the calculations
	var final_grade = process_and_score_order(target_customer, target_plate)
	
	# Display visual results directly to screen
	results_label.text = "🎉 Served %s!\nFinal Quality Score: %d%%" % [target_customer.name, int(final_grade)]
	
	# Wipe them completely out of active game arrays (Clean memory cleanup)
	GlobalState.waiting_customers.remove_at(cust_idx)
	GlobalState.topping_to_pay_queue.remove_at(plate_idx)
	
	# Redraw the list items on screen to show they are gone
	render_lists_ui()

func process_and_score_order(customer_obj: Customer, plate_obj: Dictionary) -> float:
	var ticket_obj = customer_obj.ticket
	
	# --- CRITERIA 1: Shape Match Check ---
	if plate_obj.get("shape") != ticket_obj.shape:
		return 0.0 # Instant total fail penalty if you hand them the wrong shape entirely!

	# --- CRITERIA 2: Cook Time Accuracy Math ---
	var side1_delta = abs(plate_obj.get("side1_score", 0.0) - IDEAL_COOK_TARGET)
	var side2_delta = abs(plate_obj.get("side2_score", 0.0) - IDEAL_COOK_TARGET)
	
	# Deduct 5 percentage points off a base score of 100 for every single second away from 50s
	var s1_score = max(0.0, 100.0 - (side1_delta * 5.0))
	var s2_score = max(0.0, 100.0 - (side2_delta * 5.0))
	var final_cook_score = (s1_score + s2_score) / 2.0

	# --- CRITERIA 3: Toppings & Sauces Matching Loop ---
	var component_matches: int = 0
	var plate_details = plate_obj.get("churro_details", [])
	var ticket_details = ticket_obj.churro_details
	
	# Check array elements one by one safely against each other
	var total_items_checked = max(plate_details.size(), ticket_obj.num_churros)
	
	for idx in range(total_items_checked):
		var p_item = plate_details[idx] if idx < plate_details.size() else null
		var t_item = ticket_details[idx] if idx < ticket_details.size() else null
		
		if p_item and t_item:
			if p_item.get("sauce") == t_item.get("sauce"):
				component_matches += 1
			if p_item.get("topping") == t_item.get("topping"):
				component_matches += 1

	var max_possible_points = total_items_checked * 2
	var topping_score = (float(component_matches) / float(max_possible_points)) * 100.0

	# Combine parameters together for an aggregate mean percentage score
	var shift_quality_rating = (final_cook_score + topping_score) / 2.0
	return shift_quality_rating
