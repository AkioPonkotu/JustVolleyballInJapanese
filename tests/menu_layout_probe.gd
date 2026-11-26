extends "res://game/ui/menu.gd"

# Run the real bar constructors and display-state methods without entering a
# game, connecting a party, or loading the user's profile.
var samples: Array = []

func _settle() -> void:
	for i in range(6):
		await get_tree().process_frame

func _sample(label: String) -> Dictionary:
	var row := {"case": label, "available_width": get_viewport().get_visible_rect().size.x}
	for key in ["top", "bottom"]:
		var panel = _top_panel if key == "top" else _bottom_panel
		var bar = _top_bar if key == "top" else _bottom_bar
		var right := 0.0
		for child in bar.get_children():
			if child.visible:
				right = maxf(right, child.get_global_rect().end.x)
		row[key] = {"minimum_width": panel.get_combined_minimum_size().x, "last_right": right}
	return row

func _record(label: String) -> void:
	await _settle()
	samples.append(_sample(label))

func _party_fixture(mode: String) -> void:
	for child in _party_strip.get_children():
		_party_strip.remove_child(child)
		child.queue_free()
	for i in range(6):
		_party_strip.add_child(_party_empty_slot(func(): pass))
	var texts: Array = ["private", "disband"] if mode == "leader" else ["go online", "disband"]
	if mode == "regrouping":
		texts = ["in a lobby together"]
	for text in texts:
		var b := Button.new()
		b.text = text
		UiStyle.style_button(b, "tertiary", 13)
		_slim_button(b)
		_party_strip.add_child(b)

func _ready() -> void:
	Engine.max_fps = 0
	_outfit = "captain"
	_ball_skin = "school"
	_build_bars()
	_pc_name.text = "Player"
	await _record("current-selection")
	_refresh_party_strip()
	await _record("idle-party")
	for mode in ["leader", "local", "regrouping"]:
		_party_fixture(mode)
		await _record("party-" + mode)
	_pc_name.text = "非常に長いプレイヤー名".repeat(20)
	_pc_xp_text.text = "123456789 / 987654321 xp"
	_pc_coins.text = "123,456,789"
	var worst_idle: Dictionary = {"bottom": {"minimum_width": 0}}
	var worst_search: Dictionary = {"bottom": {"minimum_width": 0}}
	var combinations := 0
	for outfit in OUTFITS:
		for skin in BALL_SKINS:
			for stage_id in Stage.freeplay_ids():
				_outfit = outfit
				_ball_skin = skin
				_freeplay_stage = stage_id
				var labels: Array = Stage.tod_labels(stage_id)
				for tod in range(maxi(1, labels.size())):
					GameConfig.menu_tod = tod
					_paint_stage_btn()
					for child in _bottom_bar.get_children():
						if child is Button and child.text.begins_with("服装："):
							child.text = "服装：%s" % tr(String(OUTFIT_LABELS[outfit]))
						elif child is Button and child.text.begins_with("ボール："):
							child.text = "ボール：%s" % tr(String(BALL_LABELS[skin]))
					var label: String = "%s/%s/%s/%d" % [outfit, skin, stage_id, tod]
					_set_matchmaking(false)
					await _settle()
					var idle := _sample(label)
					if idle.bottom.minimum_width > worst_idle.bottom.minimum_width:
						worst_idle = idle
					_set_matchmaking(true)
					_mm_label.text = "非常に長い検索状態の表示".repeat(10)
					await _settle()
					var searching := _sample(label)
					if searching.bottom.minimum_width > worst_search.bottom.minimum_width:
						worst_search = searching
					combinations += 1
	samples.append(worst_idle.merged({"case": "worst-idle", "selection": worst_idle.case}, true))
	samples.append(worst_search.merged({"case": "worst-search", "selection": worst_search.case}, true))
	_stage_btn.text = "会場：" + "非常に長い会場名".repeat(20)
	await _record("long-stage-and-search")
	var tooltips_ok: bool = _pc_name.tooltip_text == _pc_name.text and _stage_btn.tooltip_text == _stage_btn.text and _mm_label.tooltip_text == _mm_label.text
	var fits := true
	for sample in samples:
		for key in ["top", "bottom"]:
			fits = fits and sample[key].minimum_width <= sample.available_width and sample[key].last_right <= sample.available_width
	print("LAYOUT_JSON ", JSON.stringify({"scale": get_tree().root.content_scale_factor, "samples": samples, "combinations": combinations, "tooltips_ok": tooltips_ok, "fits": fits}))
	get_tree().quit(0 if fits and tooltips_ok else 1)

func _apply_party_gating() -> void:
	pass
func _update_presence() -> void:
	pass
func _queue_friends_refresh(_delay: float) -> void:
	pass
func _process(_delta: float) -> void:
	pass
func _physics_process(_delta: float) -> void:
	pass
func _exit_tree() -> void:
	pass
