extends Node

# Keep the original bar order, anchors and font sizes. Only horizontal spacing
# and text budgets change; full translated text remains available in tooltips.
var menu: Node

static func attach(target: Node) -> void:
	var helper = load("res://jvja/menu_layout.gd").new()
	helper.menu = target
	target.add_child(helper)
	helper.configure()

func configure() -> void:
	menu._top_bar.add_theme_constant_override("separation", 8)
	menu._bottom_bar.add_theme_constant_override("separation", 6)
	for child in menu._top_bar.get_children():
		if child is Button and not child.text.is_empty():
			_padding(child, 8)
	menu._party_strip.add_theme_constant_override("separation", 4)
	var dock: PanelContainer = menu._party_strip.get_parent()
	dock.custom_minimum_size.x = 340
	var box = dock.get_theme_stylebox("panel").duplicate()
	box.content_margin_left = 6
	box.content_margin_right = 6
	dock.add_theme_stylebox_override("panel", box)
	for child in menu._bottom_bar.get_children():
		if child is Button and child != menu._mm_cancel:
			_padding(child, 8)
	menu._mm_cancel.custom_minimum_size.x = 96
	_refresh()

func _padding(button: Button, pixels: float) -> void:
	for state in ["normal", "hover", "pressed", "focus", "disabled"]:
		var style = button.get_theme_stylebox(state).duplicate()
		style.content_margin_left = pixels
		style.content_margin_right = pixels
		button.add_theme_stylebox_override(state, style)

func _bound(control: Control, limit: float) -> void:
	var text: String = control.tr(control.text)
	var key = [text, limit]
	if control.get_meta("jvja_text_budget", []) == key:
		return
	control.set_meta("jvja_text_budget", key)
	control.tooltip_text = text
	var width: float = control.get_theme_font("font").get_string_size(
		text, HORIZONTAL_ALIGNMENT_LEFT, -1, control.get_theme_font_size("font_size")).x
	if control is Button:
		var padding := 0.0
		for state in ["normal", "hover", "pressed", "disabled"]:
			padding = maxf(padding, control.get_theme_stylebox(state).get_minimum_size().x)
		width += padding
		if control.icon != null:
			width += control.get_theme_constant("icon_max_width") + control.get_theme_constant("h_separation")
	elif control is Label:
		width += control.get_theme_stylebox("normal").get_minimum_size().x
	control.clip_text = true
	control.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	control.custom_minimum_size.x = minf(ceilf(width), limit)
	control.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN

func _refresh() -> void:
	var searching: bool = menu._mm_title.visible
	_bound(menu._pc_name, 180)
	_bound(menu._pc_xp_text, 64 if searching else 80)
	_bound(menu._pc_coins, 60)
	menu._pc_xp.custom_minimum_size.x = 64 if searching else 110
	_bound(menu._mm_title, 150)
	_bound(menu._mm_label, 120)
	for child in menu._bottom_bar.get_children():
		if not child is Button or child == menu._mm_cancel:
			continue
		if child == menu._stage_btn:
			_bound(child, 150 if searching else 180)
		elif child.text.begins_with("服装："):
			_bound(child, 120 if searching else 160)
		elif child.text.begins_with("ボール："):
			_bound(child, 110 if searching else 130)
	for child in menu._party_strip.get_children():
		if child is Button and not child.text.is_empty():
			if not child.has_meta("jvja_party_padding"):
				_padding(child, 6)
				child.set_meta("jvja_party_padding", true)
			_bound(child, 130)
		elif child is Control and child.custom_minimum_size.x == 34:
			child.custom_minimum_size.x = 30

func _process(_delta: float) -> void:
	_refresh()
