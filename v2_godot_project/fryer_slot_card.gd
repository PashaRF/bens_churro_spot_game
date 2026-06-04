extends PanelContainer

# Grab references to the child nodes we just built
@onready var status_label: Label = $MarginContainer/VBoxContainer/StatusLabel
@onready var cook_progress: ProgressBar = $MarginContainer/VBoxContainer/CookProgress
@onready var side_label: Label = $MarginContainer/VBoxContainer/SideLabel
@onready var flip_button: Button = $MarginContainer/VBoxContainer/ActionButtons/FlipButton
@onready var pull_button: Button = $MarginContainer/VBoxContainer/ActionButtons/PullButton

# Every card needs to know which fryer number it represents (1 through 8)
@export var slot_id: int = 1

# This custom signal lets the main station know a button was clicked on THIS specific card
signal card_action_triggered(action_type: String, target_slot: int)

func _ready() -> void:
	# Set up default empty state on load
	set_empty_state()

func set_empty_state() -> void:
	status_label.text = "Slot %d: Empty" % slot_id
	cook_progress.visible = false
	cook_progress.value = 0
	side_label.text = "Idle"
	pull_button.disabled = true
	
	# Turn the flip button into a "Load" button when empty!
	flip_button.disabled = false
	flip_button.text = "Load"

func update_cooking_state(shape: String, count: int, current_time: float, max_time: float, is_flipped: bool) -> void:
	status_label.text = "[%s] x%d" % [shape, count]
	cook_progress.visible = true
	cook_progress.max_value = max_time
	cook_progress.value = current_time
	
	if not is_flipped:
		side_label.text = "Side 1"
		flip_button.text = "Flip"
		flip_button.disabled = false
		pull_button.disabled = true
	else:
		side_label.text = "Side 2"
		flip_button.text = "Cooking..."
		flip_button.disabled = true
		pull_button.disabled = false
# --- Connecting the Buttons to the Signals ---
func _on_flip_button_pressed() -> void:
	card_action_triggered.emit("flip", slot_id)

func _on_pull_button_pressed() -> void:
	card_action_triggered.emit("pull", slot_id)
