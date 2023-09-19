import flet as ft
from time import sleep
from glob import glob
import os
from functools import partial
import pandas as pd
import csv

def main(page):
    page.title = "Patch labeling interface"

    def transform_components(to_remove=None, to_add=None):
        page_layout = page.session.get("page_layout")

        if to_remove is not None:
            for key in to_remove:
                page_layout[key] = None
            
        if to_add is not None:
            for key, value in to_add.items():
                page_layout[key] = value
        
        controls_list = []
        for key, value in page_layout.items():
            if value is not None:
                controls_list.append(value)
        
        page.session.set("page_layout", page_layout)
        page.controls = controls_list
        page.update()

    def get_directory_files(fp_control, e):
        fp_control.value = e.path if e.path else "Cancelled!"
        fp_control.update()

        if e.path:
            page.session.set("imgs", sorted(
                glob(os.path.join(e.path, '*.png')) + glob(os.path.join(e.path, '*.jpg')) + glob(os.path.join(e.path, '*.jpeg')) + glob(os.path.join(e.path, '*.tif'))
                ))
            if len(page.session.get("imgs")) > 0:
                page.session.set("current_idx", 0)
                page.session.set("labels", {})

                img_canvas = ft.Image(
                    src=page.session.get("imgs")[0],
                    width=500,
                    height=500,
                    fit=ft.ImageFit.CONTAIN)

                anno_field = ft.TextField(label=None, read_only=False, autofocus=True, hint_text="Enter annotations", value=None)

                pb_text = ft.Text(value=f"Progress: {page.session.get('current_idx')} / {len(page.session.get('imgs'))}")
                pb_bar = ft.ProgressBar(width=400, height=17, value=page.session.get("current_idx"))

                save_txt = ft.Text()
                save_file_dialog = ft.FilePicker(on_result=lambda e: save_file_result(save_txt, e))
                page.overlay.append(save_file_dialog)

                save_btn = ft.ElevatedButton(
                    "Save results",
                    icon=ft.icons.SIM_CARD_DOWNLOAD,
                    on_click=lambda _: save_file_dialog.save_file() # .get_directory_path()
                )

                transform_components(to_remove=["intro_text"], to_add={
                    'img_canvas': img_canvas,
                    'anno_field': anno_field,
                    'pb_text': pb_text,
                    'pb_bar': pb_bar,
                    'save_btn': save_btn,
                    'save_txt': save_txt,
                })

            page.update()

    def textbox_changed(tb_control, e):
        tb_control.value = e.tb_control.value
        page.update()
    
    def save_file_result(save_control, e):
        save_control.value = f"Saved to <{e.path}>" if e.path else "Cancelled!"
        save_control.update()
        save_results(e.path)

    def save_results(fpath):
        timestamp = pd.Timestamp.now().strftime("%Y%m%d-%H%M%S")
        parent_folder = os.path.basename(os.path.dirname(page.session.get("imgs")[0]))
        result = pd.DataFrame(page.session.get("labels").items(), columns=["Filename", "Label"]).astype({"Filename":"string", "Label":"string"})
        result.to_csv(fpath, index=False, quoting=csv.QUOTE_ALL)

    def window_event(e):
        if e.data == "close":
            page.dialog = confirm_dialog
            confirm_dialog.open = True
            page.update()

    def on_keyboard(e):
        if (e.key == "Arrow Right" or e.key == "Arrow Left") and len(page.session.get("imgs")) > 0:

            anno_field_control = page.session.get("page_layout")["anno_field"]
            img_canvas_control = page.session.get("page_layout")["img_canvas"]
            pb_text_control = page.session.get("page_layout")["pb_text"]
            pb_bar_control = page.session.get("page_layout")["pb_bar"]
            labels = page.session.get("labels")
            
            # set autofocus
            if anno_field_control is not None: anno_field_control.focus()

            # save label if not empty
            if anno_field_control.value is not None and anno_field_control.value.strip():
                labels[page.session.get("imgs")[page.session.get("current_idx")]] = anno_field_control.value
            page.session.set("labels", labels)

            if e.key == "Arrow Right" and page.session.get("current_idx") < len(page.session.get("imgs")) - 1:               
                img_canvas_control.src = page.session.get("imgs")[page.session.get("current_idx") + 1]
                page.session.set("current_idx", page.session.get("current_idx") + 1)
                anno_field_control.value = page.session.get("labels").get(page.session.get("imgs")[page.session.get("current_idx")])

            elif e.key == "Arrow Left" and page.session.get("current_idx") > 0:
                img_canvas_control.src = page.session.get("imgs")[page.session.get("current_idx") - 1]
                page.session.set("current_idx", page.session.get("current_idx") - 1)
                anno_field_control.value = page.session.get("labels").get(page.session.get("imgs")[page.session.get("current_idx")])
            
            if pb_bar_control is not None and pb_text_control is not None:
                pb_text_control.value = f"Image index: {page.session.get('current_idx') + 1} / {len(page.session.get('imgs'))}"
                pb_bar_control.value = len(page.session.get("labels").keys()) / len(page.session.get("imgs"))

            page.update()

    def yes_click(e):
        page.window_destroy()

    def no_click(e):
        confirm_dialog.open = False
        page.update()

    confirm_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Please confirm"),
        content=ft.Text("Do you really want to exit this app?"),
        actions=[
            ft.ElevatedButton("Yes", on_click=yes_click),
            ft.OutlinedButton("No", on_click=no_click),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    ### Page setup
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = page.window_max_width = page.window_max_width = 550
    page.window_height = page.window_max_height = page.window_min_height = 1050

    page.window_prevent_close = True
    page.on_window_event = window_event

    ### Components
    intro_text = ft.Text(value="Choose folder to label:", color="white", size=30)

    directory_path = ft.TextField(label="Selected folder", read_only=True, value=None, )
    get_directory_dialog = ft.FilePicker(on_result=lambda e: get_directory_files(directory_path, e))
    page.overlay.append(get_directory_dialog)

    open_dir_btn = ft.ElevatedButton(
            "Open directory",
            icon=ft.icons.FOLDER_OPEN,
            on_click=lambda _: get_directory_dialog.get_directory_path())

    page_layout = {
        "intro_text": intro_text,
        "open_dir_btn": open_dir_btn,
        "directory_path": directory_path,
        "img_canvas": None,
        "anno_field": None,
        "pb_text": None,
        "pb_bar": None,
        "save_btn": None,
        "save_txt": None,
    }

    ### Vars
    page.session.set("page_layout", page_layout)
    page.session.set("current_idx", 0)
    page.session.set("imgs", [])
    page.session.set("labels", {})

    page.on_keyboard_event = on_keyboard
    
    # init page add
    page.add(
        intro_text,
        open_dir_btn,
        directory_path,
    )
    page.update()

ft.app(target=main)