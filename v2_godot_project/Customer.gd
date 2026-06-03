extends RefCounted
class_name Customer

var name: String = ""
var ticket: Ticket = null

func _init(cust_name: String):
	self.name = cust_name
