extends "res://game/ui/menu.gd"

# Exercise the original constructors in an isolated user directory.
func _settle() -> void:
	for i in range(12):
		await get_tree().process_frame

func _sample(label: String) -> Dictionary:
	var p = _cfg_panels[0]
	var body = p.get_node("Stack/Body")
	var rows := {}
	for key in ["profile", "device", "actions"]:
		var row = p._rows[key]
		rows[key] = {"width": row.size.x, "right_from_card": row.get_global_rect().end.x - p.global_position.x}
	return {"case": label, "viewport_width": get_viewport().get_visible_rect().size.x,
		"card_width": p.size.x, "card_minimum": p.get_combined_minimum_size().x,
		"body_width": body.size.x, "body_minimum": body.get_combined_minimum_size().x,
		"header_minimum": p._head.get_combined_minimum_size().x,
		"status_text": p._status.text, "status_width": p._status.size.x,
		"host_width": p._crown.size.x, "clip_contents": p.clip_contents, "rows": rows}

func _ready() -> void:
	Engine.max_fps = 0
	ProfileStore.active().name = "Player"
	_root = Control.new()
	_root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	$Ui.add_child(_root)
	_configs = _page()
	_build_configs()
	await _settle()
	_refresh_configs()
	await _settle()
	var samples: Array = [_sample("original-layout")]
	# Causal checks change only the header; the lower rows are untouched.
	_cfg_panels[0]._status.text = ""
	await _settle()
	samples.append(_sample("status-empty"))
	_cfg_panels[0]._status.text = "party leader"
	_cfg_panels[0]._status.clip_text = true
	_cfg_panels[0]._status.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	_cfg_panels[0]._status.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	await _settle()
	samples.append(_sample("status-ellipsis"))
	print("CONFIG_LAYOUT_JSON ", JSON.stringify({"locale": TranslationServer.get_locale(), "samples": samples}))
	get_tree().quit()
