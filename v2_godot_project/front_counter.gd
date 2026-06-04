extends Control

func _on_button_pressed() -> void:
	if GlobalState.waiting_at_door.is_empty():
		print("No one is at the counter right now. Listen for the bell!")
		return

	# Pop first customer out of the door line array list
	var raw_arrival = GlobalState.waiting_at_door.pop_at(0)
	var name_string = raw_arrival.get("name", "Customer")
	var customer_obj = Customer.new(name_string)

	# Generate completely random order parameters matching original script design rules
	var order_qty = randi_range(1, 6)
	var order_shape = GlobalState.SHAPES.pick_random()
	var order_sauce = GlobalState.SAUCES.pick_random()
	var order_topping = GlobalState.TOPPINGS.pick_random()

	var detail_array: Array[Dictionary] = []
	for idx in range(order_qty):
		detail_array.append({"sauce": order_sauce, "topping": order_topping})

	# Construct ticket data payload structure
	var new_ticket = Ticket.new(order_qty, order_shape, detail_array)
	customer_obj.ticket = new_ticket

	# Append tracking variables into persistent system records arrays queues
	GlobalState.waiting_customers.append(customer_obj)
	GlobalState.tickets.append(new_ticket) # Places ticket directly onto active top rail tracker view
	
	print("--> %s stepped up to the counter and ordered!" % name_string)
	print(new_ticket.get_ticket_summary())
