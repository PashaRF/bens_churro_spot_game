extends Node2D

@onready var ticket_rail_bar: HBoxContainer = $CanvasLayer/MainControlLayout/TicketRailBar
@onready var workspace: PanelContainer =$CanvasLayer/MainControlLayout/StationWorkspaceContainer
@onready var shift_timer: Timer = $ScreenTimer
@onready var spawn_timer: Timer = $CustomerSpawnTimer
var is_first_customer: bool = true

func _calculate_next_spawn_interval() -> void:
	# Matches python random choice limits: 5-10s first, 90-140s subsequent loops
	var next_wait = randf_range(5.0, 10.0) if is_first_customer else randf_range(90.0, 140.0)
	is_first_customer = false
	spawn_timer.wait_time = next_wait
	spawn_timer.start()

func _on_customer_spawn_trigger() -> void:
	# Compile active names list across all arrays to check shop capacity thresholds
	var active_names: Array[String] = []
	for p in GlobalState.waiting_at_door:
		active_names.append(p["name"])
	for c in GlobalState.waiting_customers:
		active_names.append(c.name)
		
	# 🚨 CAP CHECKS: Limit to 8 customers maximum inside the shop space
	if active_names.size() >= 8:
		# Shop is full! Skip spawning this customer and reset the arrival countdown loop
		_calculate_next_spawn_interval()
		return

	# Extract unique names from availability arrays
	var available_choices = GlobalState.NAMES_POOL.filter(func(name): return not name in active_names)
	var chosen_name: String = ""
	
	if available_choices.size() > 0:
		chosen_name = available_choices.pick_random()
	else:
		chosen_name = GlobalState.NAMES_POOL.pick_random() + " II"

	var new_arrival = {
		"name": chosen_name,
		"order": "Pending Order details..."
	}
	
	# Push directly into door arrival queue list - avoiding kitchen ticket list injection!
	GlobalState.waiting_at_door.append(new_arrival)
	print("🛎️ DING! %s just walked into the shop!" % chosen_name)
	
	# Loop spawner cleanly
	_calculate_next_spawn_interval()
func _ready() -> void:
	print("READY FROM MAIN")
	print("Button is: ", $CanvasLayer/MainControlLayout/StationSwitchBar/FrontCounterBtn)
	$CanvasLayer/MainControlLayout/StationSwitchBar/FrontCounterBtn.pressed.connect(func(): switch_station_view("Front Counter"))
	$CanvasLayer/MainControlLayout/StationSwitchBar/PastryBtn.pressed.connect(func(): switch_station_view("Fry Station"))
	# 1. Configure and kick-off background clock tracking loop (Shift Timer)
	shift_timer.wait_time = 1.0
	shift_timer.autostart = true
	shift_timer.timeout.connect(_on_second_passed)
	shift_timer.start()
	$CanvasLayer/MainControlLayout/StationSwitchBar/FrontCounterBtn.pressed.connect(func(): switch_station_view("Front Counter"))
	$CanvasLayer/MainControlLayout/StationSwitchBar/FryBtn.pressed.connect(func(): switch_station_view("Fry Station"))
	# 2. Configure and kick-off the Customer Spawner (Moved from _enter_tree)
	spawn_timer.timeout.connect(_on_customer_spawn_trigger)
	_calculate_next_spawn_interval()
	
	# 3. Load default initialization view
	switch_station_view("Front Counter")

func _on_second_passed() -> void:
	if GlobalState.is_running:
		GlobalState.elapsed_shift_time += 1.0

func switch_station_view(station_name: String) -> void:
	GlobalState.current_station = station_name
	
	# Wipe old active panel view contents cleanly out of layout frame memory
	for child in workspace.get_children():
		child.queue_free()
		
	# Instantiate correct targeted node package component layout based on context
	var target_scene_path: String = ""
	match station_name:
		"Front Counter": target_scene_path = "res://FrontCounter.tscn"
		"Pastry Station": target_scene_path = "res://PastryStation.tscn"
		"Fry Station": target_scene_path = "res://FryStation.tscn"
		"Topping Station": target_scene_path = "res://ToppingStation.tscn"
		"Pay Counter": target_scene_path = "res://PayCounter.tscn" # Ensure this line matches exactly!
		
	if ResourceLoader.exists(target_scene_path):
		var scene_resource = load(target_scene_path)
		var instance = scene_resource.instantiate()
		workspace.add_child(instance)
		

func _on_front_counter_btn_pressed() -> void:
	switch_station_view("Front Counter")

func _on_pastry_btn_pressed() -> void:
	switch_station_view("Pastry Station")

func _on_fry_btn_pressed() -> void:
	switch_station_view("Fry Station")

func _on_topping_btn_pressed() -> void:
	switch_station_view("Topping Station")

func _on_pay_btn_pressed() -> void:
	switch_station_view("Pay Counter")
