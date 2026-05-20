[group("Meta")]
[doc("List available recipes")]
_default:
	@just --list

[group("Start App")]
[doc("Start the Textual app")]
run:
	uv run main

[group("Start App")]
[doc("Add YT channel based on provided YT url")]
add:
	uv run ./src/youtube.py
