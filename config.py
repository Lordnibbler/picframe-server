from copy import deepcopy
import json
import os
import subprocess

from flask import Flask, render_template, request, redirect, url_for, flash
from ruamel.yaml import YAML

app = Flask(__name__)
app.secret_key = os.environ.get("PICFRAME_WEB_SECRET", "change-me")

CONFIG_FILE = "/home/pi/picframe_data/config/configuration.yaml"

yaml = YAML()
yaml.preserve_quotes = True
yaml.width = 4096
yaml.indent(mapping=2, sequence=4, offset=2)

# Full schema based on PicFrame Configuration wiki
SCHEMA = {
    "viewer": {
        "blur_amount": {
            "type": "int",
            "default": 12,
            "description": "Values larger than 12 will increase processing load considerably.",
        },
        "blur_zoom": {
            "type": "float",
            "default": 1.0,
            "description": "Must be >= 1.0. Expands the background to fill the space around the image.",
        },
        "blur_edges": {
            "type": "bool",
            "default": False,
            "description": "Use blurred version of image to fill edges; overrides fit=False behavior.",
        },
        "edge_alpha": {
            "type": "float",
            "default": 0.5,
            "description": "Background color alpha at edge. 1.0 shows reflection of image.",
        },
        "fps": {
            "type": "float",
            "default": 20.0,
            "description": "Viewer frames per second.",
        },
        "background": {
            "type": "json",
            "default": [0.2, 0.2, 0.3, 1.0],
            "description": "RGBA used to fill edges when fitting.",
        },
        "blend_type": {
            "type": "select",
            "default": "blend",
            "options": ["blend", "burn", "bump"],
            "description": "Type of blend the shader can do.",
        },
        "font_file": {
            "type": "string",
            "default": "~/picframe_data/data/fonts/NotoSans-Regular.ttf",
            "description": "Font used to display text overlay information.",
        },
        "shader": {
            "type": "string",
            "default": "~/picframe_data/data/shaders/blend_new",
            "description": "Shader path.",
        },
        "show_text_fm": {
            "type": "string",
            "default": "%b %d, %Y",
            "description": "Date format for displayed text overlay values.",
        },
        "show_text_tm": {
            "type": "float",
            "default": 20.0,
            "description": "Seconds to show text overlay information.",
        },
        "show_text_sz": {
            "type": "int",
            "default": 40,
            "description": "Text character size.",
        },
        "show_text": {
            "type": "string",
            "default": "title caption name date folder location",
            "description": 'Text overlay content. Can include any combination of "title", "caption", "name", "date", "location", "folder".',
        },
        "text_justify": {
            "type": "select",
            "default": "L",
            "options": ["L", "C", "R"],
            "description": "Text justification.",
        },
        "text_bkg_hgt": {
            "type": "float",
            "default": 0.25,
            "description": "0.0-1.0. Percentage of screen height for text background texture. 0 disables it.",
        },
        "text_opacity": {
            "type": "float",
            "default": 1.0,
            "description": "0.0-1.0 alpha value of text overlay.",
        },
        "fit": {
            "type": "bool",
            "default": False,
            "description": "Shrink to fit screen instead of cropping.",
        },
        "kenburns": {
            "type": "bool",
            "default": False,
            "description": "Ken Burns motion effect. If true, fit becomes False and blur_edges becomes False.",
        },
        "display_x": {
            "type": "int",
            "default": 0,
            "description": "Pixel offset from left of screen. Can be negative.",
        },
        "display_y": {
            "type": "int",
            "default": 0,
            "description": "Pixel offset from top of screen. Can be negative.",
        },
        "display_w": {
            "type": "nullable_int",
            "default": None,
            "description": "Width of display surface. Null uses hardware max.",
        },
        "display_h": {
            "type": "nullable_int",
            "default": None,
            "description": "Height of display surface. Null uses hardware max.",
        },
        "use_glx": {
            "type": "bool",
            "default": False,
            "description": "Set True on Linux with X server running and no hardware 3D acceleration.",
        },
        "mat_images": {
            "type": "flex",
            "default": 0.01,
            "description": "True mats all images, False mats none, numeric value mats images whose aspect ratio differs from the display by more than that value.",
        },
        "mat_type": {
            "type": "nullable_string",
            "default": None,
            "description": "Mat types to randomly choose from. Null or empty string uses all supported types.",
        },
        "outer_mat_color": {
            "type": "nullable_json",
            "default": None,
            "description": "Outer mat color as RGB list. Null auto-selects from the image.",
        },
        "inner_mat_color": {
            "type": "nullable_json",
            "default": None,
            "description": "Inner mat color as RGB list. Null auto-selects from the image.",
        },
        "outer_mat_border": {
            "type": "int",
            "default": 75,
            "description": "Minimum outer mat border in pixels.",
        },
        "inner_mat_border": {
            "type": "int",
            "default": 40,
            "description": "Minimum inner mat border in pixels for styles that use it.",
        },
        "outer_mat_use_texture": {
            "type": "bool",
            "default": True,
            "description": "True uses a texture for the outer mat. False creates a solid-color outer mat.",
        },
        "inner_mat_use_texture": {
            "type": "bool",
            "default": False,
            "description": "True uses a texture for the inner mat. False creates a solid-color inner mat.",
        },
        "mat_resource_folder": {
            "type": "string",
            "default": "~/picframe_data/data/mat",
            "description": "Folder containing mat image files.",
        },
        "show_clock": {
            "type": "bool",
            "default": False,
            "description": "Show clock overlay.",
        },
        "clock_justify": {
            "type": "select",
            "default": "R",
            "options": ["L", "C", "R"],
            "description": "Clock justification.",
        },
        "clock_text_sz": {
            "type": "int",
            "default": 120,
            "description": "Clock character size.",
        },
        "clock_format": {
            "type": "string",
            "default": "%I:%M",
            "description": "strftime format for clock string.",
        },
        "clock_opacity": {
            "type": "float",
            "default": 1.0,
            "description": "0.0-1.0 alpha value of clock overlay.",
        },
        "menu_text_sz": {
            "type": "int",
            "default": 40,
            "description": "Menu character size.",
        },
        "menu_autohide_tm": {
            "type": "float",
            "default": 10.0,
            "description": "Seconds to show menu before auto-hiding. 0 disables auto-hiding.",
        },
        "geo_suppress_list": {
            "type": "json",
            "default": [],
            "description": "Substrings to remove from the location text.",
        },
    },
    "model": {
        "pic_dir": {
            "type": "string",
            "default": "~/Pictures",
            "description": "Root folder for images.",
        },
        "deleted_pictures": {
            "type": "string",
            "default": "~/DeletedPictures",
            "description": "Move deleted pictures here.",
        },
        "no_files_img": {
            "type": "string",
            "default": "~/picframe_data/data/no_pictures.jpg",
            "description": "Image to show if none are selected.",
        },
        "subdirectory": {
            "type": "string",
            "default": "",
            "description": "Subdirectory of pic_dir. Can be changed by MQTT.",
        },
        "recent_n": {
            "type": "int",
            "default": 7,
            "description": "Recent days. When shuffling, images changed more recently than this play before the rest.",
        },
        "reshuffle_num": {
            "type": "int",
            "default": 1,
            "description": "Times through before reshuffling.",
        },
        "time_delay": {
            "type": "float",
            "default": 200.0,
            "description": "Time between consecutive slide starts. Can be changed by MQTT.",
        },
        "fade_time": {
            "type": "float",
            "default": 10.0,
            "description": "Time during which slides overlap. Can be changed by MQTT.",
        },
        "shuffle": {
            "type": "bool",
            "default": True,
            "description": "Shuffle on reloading image files. Can be changed by MQTT.",
        },
        "sort_cols": {
            "type": "string",
            "default": "fname ASC",
            "description": "Sort columns and directions, comma-separated.",
        },
        "image_attr": {
            "type": "json",
            "default": [
                "PICFRAME GPS",
                "PICFRAME LOCATION",
                "EXIF FNumber",
                "EXIF ExposureTime",
                "EXIF ISOSpeedRatings",
                "EXIF FocalLength",
                "EXIF DateTimeOriginal",
                "Image Model",
                "IPTC Caption/Abstract",
                "IPTC Object Name",
                "IPTC Keywords",
            ],
            "description": "Image attributes sent by MQTT.",
        },
        "load_geoloc": {
            "type": "bool",
            "default": False,
            "description": "Get location information from OpenStreetMap.",
        },
        "geo_key": {
            "type": "string",
            "default": "this_needs_to@be_changed",
            "description": "Must be changed to something unique to you, such as your email address.",
        },
        "locale": {
            "type": "string",
            "default": "en_US.utf8",
            "description": 'Use "locale -a" to see installed locales.',
        },
        "key_list": {
            "type": "json",
            "default": [
                ["tourism", "amenity", "isolated_dwelling"],
                ["suburb", "village"],
                ["city", "county"],
                ["region", "state", "province"],
                ["country"],
            ],
            "description": "Ordered keys used for location lookup.",
        },
        "db_file": {
            "type": "string",
            "default": "~/picframe_data/data/pictureframe.db3",
            "description": "Database used by PictureFrame.",
        },
        "portrait_pairs": {
            "type": "bool",
            "default": False,
            "description": "True displays portrait-oriented images in pairs.",
        },
        "log_level": {
            "type": "select",
            "default": "WARNING",
            "options": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            "description": "Logging level.",
        },
        "log_file": {
            "type": "string",
            "default": "",
            "description": "Optional log file path. Messages are appended indefinitely.",
        },
    },
    "mqtt": {
        "use_mqtt": {
            "type": "bool",
            "default": False,
            "description": "Enable MQTT.",
        },
        "server": {
            "type": "string",
            "default": "your_mqtt_broker",
            "description": "MQTT broker hostname.",
        },
        "port": {
            "type": "int",
            "default": 8883,
            "description": 'Usually 8883 for TLS, 1883 otherwise. If TLS is not used, tls should be "".',
        },
        "login": {
            "type": "string",
            "default": "name",
            "description": "MQTT username.",
        },
        "password": {
            "type": "string",
            "default": "your_password",
            "description": "MQTT password.",
        },
        "tls": {
            "type": "string",
            "default": "/path/to/your/ca.crt",
            "description": 'Path to CA certificate. If not used, set to "".',
        },
        "device_id": {
            "type": "string",
            "default": "picframe",
            "description": "Unique device ID. Change if more than one PictureFrame is used.",
        },
        "device_url": {
            "type": "string",
            "default": "",
            "description": "If use_http is true, set this to the PicFrame config page URL, otherwise leave blank.",
        },
    },
    "http": {
        "use_http": {
            "type": "bool",
            "default": False,
            "description": "Enable PicFrame's local HTTP server. Do not expose externally.",
        },
        "path": {
            "type": "string",
            "default": "~/picframe_data/html",
            "description": "Path where HTML files are located.",
        },
        "port": {
            "type": "int",
            "default": 9000,
            "description": "HTTP server port.",
        },
        "use_ssl": {
            "type": "bool",
            "default": False,
            "description": "Enable SSL.",
        },
        "keyfile": {
            "type": "string",
            "default": "path/to/key.pem",
            "description": "Private key path.",
        },
        "certfile": {
            "type": "string",
            "default": "path/to/cert.pem",
            "description": "Server certificate path.",
        },
    },
    "peripherals": {
        "input_type": {
            "type": "select_null",
            "default": None,
            "options": [None, "keyboard", "touch", "mouse"],
            "description": 'Valid options: null, "keyboard", "touch", "mouse".',
        },
        "buttons": {
            "type": "group",
            "description": "Per-button settings.",
            "children": {
                "pause": {
                    "enable": {
                        "type": "bool",
                        "default": True,
                        "description": "Pause or unpause the show.",
                    },
                    "label": {
                        "type": "string",
                        "default": "Pause",
                        "description": "Button label.",
                    },
                    "shortcut": {
                        "type": "string",
                        "default": " ",
                        "description": "Shortcut key.",
                    },
                },
                "display_off": {
                    "enable": {
                        "type": "bool",
                        "default": True,
                        "description": "Turn off the display.",
                    },
                    "label": {
                        "type": "string",
                        "default": "Display off",
                        "description": "Button label.",
                    },
                    "shortcut": {
                        "type": "string",
                        "default": "o",
                        "description": "Shortcut key.",
                    },
                },
                "location": {
                    "enable": {
                        "type": "bool",
                        "default": False,
                        "description": "Show or hide location information.",
                    },
                    "label": {
                        "type": "string",
                        "default": "Location",
                        "description": "Button label.",
                    },
                    "shortcut": {
                        "type": "string",
                        "default": "l",
                        "description": "Shortcut key.",
                    },
                },
                "exit": {
                    "enable": {
                        "type": "bool",
                        "default": False,
                        "description": "Exit PictureFrame.",
                    },
                    "label": {
                        "type": "string",
                        "default": "Exit",
                        "description": "Button label.",
                    },
                    "shortcut": {
                        "type": "string",
                        "default": "e",
                        "description": "Shortcut key.",
                    },
                },
                "power_down": {
                    "enable": {
                        "type": "bool",
                        "default": False,
                        "description": "Power down the device using sudo.",
                    },
                    "label": {
                        "type": "string",
                        "default": "Power down",
                        "description": "Button label.",
                    },
                    "shortcut": {
                        "type": "string",
                        "default": "p",
                        "description": "Shortcut key.",
                    },
                },
            },
        },
    },
}

SECTION_TITLES = {
    "viewer": "Viewer",
    "model": "Model",
    "mqtt": "MQTT",
    "http": "HTTP",
    "peripherals": "Peripherals",
}


def read_config(file_path):
    if not os.path.exists(file_path):
        return {}
    with open(file_path, "r") as file:
        data = yaml.load(file) or {}
        return data


def write_config(file_path, data):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w") as file:
        yaml.dump(data, file)


def restart_picframe():
    result = subprocess.run(
        ["systemctl", "--user", "restart", "picframe.service"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Failed to restart picframe.service")


def build_field(path, name, schema, value):
    return {
        "path": path,
        "name": name,
        "label": name.replace("_", " ").title(),
        "type": schema.get("type", "string"),
        "value": serialize_for_form(value, schema.get("type", "string")),
        "raw_value": value,
        "default": schema.get("default"),
        "description": schema.get("description", ""),
        "options": schema.get("options", []),
    }


def merge_schema_with_config(schema, config):
    result = {}

    for section_name, section_schema in schema.items():
        section_cfg = config.get(section_name, {}) or {}
        result[section_name] = {
            "_title": SECTION_TITLES.get(section_name, section_name.title()),
            "_fields": [],
        }

        for field_name, field_schema in section_schema.items():
            if field_schema.get("type") == "group":
                group_cfg = section_cfg.get(field_name, {}) or {}
                group_entry = {
                    "name": field_name,
                    "label": field_name.replace("_", " ").title(),
                    "type": "group",
                    "description": field_schema.get("description", ""),
                    "children": [],
                }

                for child_name, child_schema in field_schema["children"].items():
                    child_cfg = group_cfg.get(child_name, {}) or {}
                    child_entry = {
                        "name": child_name,
                        "label": child_name.replace("_", " ").title(),
                        "type": "subgroup",
                        "fields": [],
                    }

                    for grandchild_name, grandchild_schema in child_schema.items():
                        value = child_cfg.get(grandchild_name, grandchild_schema.get("default"))
                        child_entry["fields"].append(
                            build_field(
                                f"{section_name}.{field_name}.{child_name}.{grandchild_name}",
                                grandchild_name,
                                grandchild_schema,
                                value,
                            )
                        )

                    group_entry["children"].append(child_entry)

                result[section_name]["_fields"].append(group_entry)
            else:
                value = section_cfg.get(field_name, field_schema.get("default"))
                result[section_name]["_fields"].append(
                    build_field(f"{section_name}.{field_name}", field_name, field_schema, value)
                )

    return result


def serialize_for_form(value, field_type):
    if field_type in {"json", "nullable_json"}:
        return "" if value is None else json.dumps(value)
    if field_type == "select_null":
        return "__NULL__" if value is None else str(value)
    if field_type == "bool":
        return bool(value)
    if value is None:
        return ""
    return str(value)


def parse_value(raw, field_type):
    if field_type == "string":
        return raw
    if field_type == "nullable_string":
        return None if raw == "" else raw
    if field_type == "int":
        return int(raw)
    if field_type == "nullable_int":
        return None if raw == "" else int(raw)
    if field_type == "float":
        return float(raw)
    if field_type == "bool":
        return raw == "true"
    if field_type == "json":
        return json.loads(raw)
    if field_type == "nullable_json":
        return None if raw.strip() == "" else json.loads(raw)
    if field_type == "select":
        return raw
    if field_type == "select_null":
        return None if raw == "__NULL__" else raw
    if field_type == "flex":
        lowered = raw.strip().lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
        if lowered in {"null", "none", ""}:
            return None
        try:
            if "." in raw:
                return float(raw)
            return int(raw)
        except ValueError:
            return raw
    return raw


def set_nested_value(data, dotted_path, value):
    keys = dotted_path.split(".")
    current = data
    for key in keys[:-1]:
        if key not in current or current[key] is None:
            current[key] = {}
        current = current[key]
    current[keys[-1]] = value


def build_updated_config_from_form(form):
    updated = {}

    for section_name, section_schema in SCHEMA.items():
        for field_name, field_schema in section_schema.items():
            if field_schema.get("type") == "group":
                for child_name, child_schema in field_schema["children"].items():
                    for grandchild_name, grandchild_schema in child_schema.items():
                        path = f"{section_name}.{field_name}.{child_name}.{grandchild_name}"
                        raw = form.get(path, "")
                        value = parse_value(raw, grandchild_schema["type"])
                        set_nested_value(updated, path, value)
            else:
                path = f"{section_name}.{field_name}"
                raw = form.get(path, "")
                value = parse_value(raw, field_schema["type"])
                set_nested_value(updated, path, value)

    return updated


def deep_merge(base, updates):
    if not isinstance(base, dict) or not isinstance(updates, dict):
        return deepcopy(updates)
    merged = deepcopy(base)
    for key, value in updates.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged


@app.route("/")
def index():
    config = read_config(CONFIG_FILE)
    ui_config = merge_schema_with_config(SCHEMA, config)
    return render_template(
        "index.html",
        config=ui_config,
        config_file=CONFIG_FILE,
    )


@app.route("/update", methods=["POST"])
def update():
    try:
        existing_config = read_config(CONFIG_FILE)
        updated_from_form = build_updated_config_from_form(request.form)
        final_config = deep_merge(existing_config, updated_from_form)
        write_config(CONFIG_FILE, final_config)
        restart_picframe()
        flash("Configuration saved and PicFrame restarted.", "success")
    except Exception as exc:
        flash(f"Failed to save configuration: {exc}", "danger")

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
