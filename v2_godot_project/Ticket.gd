extends RefCounted
class_name Ticket

var num_churros: int = 0
var shape: String = ""
var churro_details: Array[Dictionary] = []
var order_time: float = 0.0

func _init(amt: int, shp: String, details: Array[Dictionary]):
	self.num_churros = amt
	self.shape = shp
	self.churro_details = details
	self.order_time = Time.get_unix_time_from_system()

# Replaces your Python __str__ method to return a clean summary for UI display boxes
func get_ticket_summary() -> String:
	var out = "Shape: %s\nAmount: %d Churro(s)\n" % [shape, num_churros]
	for i in range(churro_details.size()):
		var c = churro_details[i]
		out += "  - Item #%d: Sauce: %s, Topping: %s\n" % [i + 1, c.get("sauce", "None"), c.get("topping", "None")]
	return out
