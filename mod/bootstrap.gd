extends RefCounted

static func install() -> void:
	var font := FontFile.new()
	font.font_data = FileAccess.get_file_as_bytes("res://jvja/NotoSansJP.ttf")
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
			var fallbacks := original.fallbacks
			fallbacks.append(font)
			original.fallbacks = fallbacks
	var messages = JSON.parse_string(FileAccess.get_file_as_string("res://jvja/messages.json"))
	var translation := Translation.new()
	translation.locale = "ja"
	for source in messages:
		translation.add_message(source, messages[source])
	TranslationServer.add_translation(translation)
	TranslationServer.set_locale("ja")
	print("[JVJA] Japanese translation loaded: ", messages.size(), " messages; font: ", font.get_font_name())
