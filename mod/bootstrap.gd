extends RefCounted

static func install() -> void:
	var font := FontFile.new()
	font.data = FileAccess.get_file_as_bytes("res://jvja/JVVolleyballJP-SemiBold.ttf")
	font.allow_system_fallback = false
	var bold := FontFile.new()
	bold.data = FileAccess.get_file_as_bytes("res://jvja/JVVolleyballJP-ExtraBold.ttf")
	bold.allow_system_fallback = false
	var retained_fonts: Array[Font] = [font, bold]
	var paths := [
		"res://game/fonts/Nunito/Nunito-Black.ttf",
		"res://game/fonts/Nunito/Nunito-Bold.ttf",
		"res://game/fonts/Nunito/Nunito-ExtraBold.ttf",
		"res://game/fonts/Nunito/Nunito-SemiBold.ttf",
		"res://game/fonts/Nunito/Nunito-SemiBoldItalic.ttf",
		"res://game/fonts/PublicPixel/PublicPixel.ttf",
		"res://game/fonts/VarsityTeam-Bold.otf",
	]
	for path in paths:
		var original := load(path) as FontFile
		if original != null:
			var japanese: FontFile = bold if original.get_font_weight() >= 700 else font
			var fallbacks := original.fallbacks
			fallbacks.append(japanese)
			original.fallbacks = fallbacks
			retained_fonts.append(japanese)
			retained_fonts.append(original)
	# ResourceLoader's cache uses weak references. Keep all modified fonts alive
	# until UI themes load, including fonts that were not already preloaded.
	(Engine.get_main_loop() as SceneTree).root.set_meta("jvja_fonts", retained_fonts)
	var messages = JSON.parse_string(FileAccess.get_file_as_string("res://jvja/messages.json"))
	var translation := Translation.new()
	translation.locale = "ja"
	var count := 0
	for context in messages:
		for source in messages[context]:
			translation.add_message(source, messages[context][source], StringName(context))
			count += 1
	TranslationServer.add_translation(translation)
	TranslationServer.set_locale("ja")
	print("[JVJA] Japanese translation loaded: ", count, " messages; Japanese font fallback ready")
