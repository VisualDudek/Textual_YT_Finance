[group("Meta")]
[doc("List available recipes")]
_default:
	@just --list

[group("Start App")]
[doc("Start the Textual app")]
app:
	uv run main

[group("Start App")]
[doc("Add YT channel based on provided YT url")]
add:
	uv run ./src/add_yt_channel.py

[group("Utils")]
[doc("Update db with latest videos from all channels")]
update:
	uv run update