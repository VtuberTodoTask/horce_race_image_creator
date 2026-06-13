"""競馬配信用画像生成ツール - メインGUI."""

import os
import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, ttk

from tkinterdnd2 import DND_FILES, TkinterDnD

from image_generator import generate_image
from scraper import fetch_shutuba
from settings import (
    AppSettings,
    BackgroundSetting,
    ParticipantSetting,
    load_settings,
    save_settings,
)

MAX_PARTICIPANTS = 6


class ParticipantRow(tk.Frame):
    """参加者1行分の入力UI."""

    def __init__(self, master: tk.Widget, index: int) -> None:
        super().__init__(master)
        self.index = index
        self.avatar_path = ""

        tk.Label(self, text=f"参加者{index + 1}:", width=10, anchor="w").pack(
            side=tk.LEFT
        )

        self.name_var = tk.StringVar()
        tk.Entry(self, textvariable=self.name_var, width=15).pack(
            side=tk.LEFT, padx=(0, 5)
        )

        self.avatar_label = tk.Label(
            self,
            text="アバター: 未選択 (D&D可)",
            width=25,
            anchor="w",
            relief="groove",
            padx=4,
            pady=2,
        )
        self.avatar_label.pack(side=tk.LEFT, padx=(0, 5))

        tk.Button(self, text="画像選択", command=self._select_avatar).pack(side=tk.LEFT)

    def _select_avatar(self) -> None:
        path = filedialog.askopenfilename(
            title="アバター画像を選択",
            filetypes=[("画像ファイル", "*.png *.jpg *.jpeg *.gif *.bmp")],
        )
        if path:
            self.avatar_path = path
            self.avatar_label.config(text=f"アバター: {os.path.basename(path)}")

    def get_name(self) -> str:
        return self.name_var.get().strip()

    def set_name(self, name: str) -> None:
        self.name_var.set(name)

    def set_avatar(self, path: str) -> None:
        self.avatar_path = path
        if path:
            self.avatar_label.config(text=f"アバター: {os.path.basename(path)}")

    def enable_drop(self) -> None:
        """ドロップターゲットとして登録する (TkinterDnD初期化後に呼ぶ)."""
        self.avatar_label.drop_target_register(DND_FILES)
        self.avatar_label.dnd_bind("<<Drop>>", self._on_drop)
        self.avatar_label.dnd_bind("<<DragEnter>>", self._on_drag_enter)
        self.avatar_label.dnd_bind("<<DragLeave>>", self._on_drag_leave)

    def _on_drop(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        path: str = event.data  # type: ignore[attr-defined]
        path = path.strip().strip("{}")
        if not path:
            return
        ext = os.path.splitext(path)[1].lower()
        if ext not in (".png", ".jpg", ".jpeg", ".gif", ".bmp"):
            return
        self.avatar_path = path
        self.avatar_label.config(
            text=f"アバター: {os.path.basename(path)}",
            bg="#e8f5e9",
        )

    def _on_drag_enter(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        self.avatar_label.config(bg="#bbdefb")

    def _on_drag_leave(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        bg = "#e8f5e9" if self.avatar_path else self.avatar_label.master.cget("bg")
        self.avatar_label.config(bg=bg)

    def get_avatar(self) -> str:
        return self.avatar_path


class App(TkinterDnD.Tk):  # type: ignore[misc]
    """メインアプリケーション."""

    def __init__(self) -> None:
        super().__init__()
        self.title("競馬配信用画像生成ツール")
        self.geometry("620x700")
        self.resizable(False, False)

        self._create_widgets()
        self._load_saved_settings()

    # ------------------------------------------------------------------
    # ウィジェット構築
    # ------------------------------------------------------------------
    def _create_widgets(self) -> None:
        # --- URL入力 ---
        url_frame = tk.LabelFrame(self, text="netkeiba 出馬表URL", padx=10, pady=5)
        url_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        self.url_var = tk.StringVar()
        tk.Entry(url_frame, textvariable=self.url_var, width=70).pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )

        # --- 参加者設定 ---
        participant_frame = tk.LabelFrame(self, text="参加者設定", padx=10, pady=5)
        participant_frame.pack(fill=tk.BOTH, padx=10, pady=5, expand=True)

        count_frame = tk.Frame(participant_frame)
        count_frame.pack(fill=tk.X, pady=(0, 5))
        tk.Label(count_frame, text="参加者数:").pack(side=tk.LEFT)
        self.participant_count = tk.IntVar(value=4)
        spin = ttk.Spinbox(
            count_frame,
            from_=0,
            to=MAX_PARTICIPANTS,
            textvariable=self.participant_count,
            width=5,
        )
        spin.pack(side=tk.LEFT, padx=5)
        tk.Button(count_frame, text="更新", command=self._update_participant_rows).pack(
            side=tk.LEFT
        )

        self.rows_frame = tk.Frame(participant_frame)
        self.rows_frame.pack(fill=tk.BOTH, expand=True)
        self.participant_rows: list[ParticipantRow] = []
        self._update_participant_rows()

        dnd_hint = tk.Label(
            participant_frame,
            text="※ アバター画像はラベルへのドラッグ＆ドロップでも設定できます",
            fg="gray",
        )
        dnd_hint.pack(anchor="w")

        # --- 背景設定 ---
        bg_frame = tk.LabelFrame(self, text="背景設定", padx=10, pady=5)
        bg_frame.pack(fill=tk.X, padx=10, pady=5)

        # 背景画像選択
        bg_path_frame = tk.Frame(bg_frame)
        bg_path_frame.pack(fill=tk.X, pady=(0, 5))
        tk.Label(bg_path_frame, text="背景画像:").pack(side=tk.LEFT)
        self.bg_path_var = tk.StringVar()
        tk.Entry(bg_path_frame, textvariable=self.bg_path_var, width=40).pack(
            side=tk.LEFT, padx=5, fill=tk.X, expand=True
        )
        tk.Button(bg_path_frame, text="選択", command=self._select_bg_image).pack(
            side=tk.LEFT
        )
        tk.Button(bg_path_frame, text="クリア", command=self._clear_bg_image).pack(
            side=tk.LEFT, padx=(5, 0)
        )

        # サイズモード
        size_frame = tk.Frame(bg_frame)
        size_frame.pack(fill=tk.X, pady=(0, 5))
        tk.Label(size_frame, text="画像サイズ:").pack(side=tk.LEFT)
        self.size_mode_var = tk.StringVar(value="auto")
        for text, val in [
            ("自動", "auto"),
            ("背景に合わせる", "background"),
            ("カスタム", "custom"),
        ]:
            tk.Radiobutton(
                size_frame,
                text=text,
                variable=self.size_mode_var,
                value=val,
                command=self._on_size_mode_change,
            ).pack(side=tk.LEFT, padx=(5, 0))

        # カスタムサイズ入力
        self.custom_size_frame = tk.Frame(bg_frame)
        self.custom_size_frame.pack(fill=tk.X)
        tk.Label(self.custom_size_frame, text="幅:").pack(side=tk.LEFT)
        self.custom_w_var = tk.StringVar(value="1280")
        self.custom_w_entry = tk.Entry(
            self.custom_size_frame, textvariable=self.custom_w_var, width=6
        )
        self.custom_w_entry.pack(side=tk.LEFT, padx=(0, 5))
        tk.Label(self.custom_size_frame, text="高さ:").pack(side=tk.LEFT)
        self.custom_h_var = tk.StringVar(value="720")
        self.custom_h_entry = tk.Entry(
            self.custom_size_frame, textvariable=self.custom_h_var, width=6
        )
        self.custom_h_entry.pack(side=tk.LEFT)

        # 背景色 / 透過設定
        color_frame = tk.Frame(bg_frame)
        color_frame.pack(fill=tk.X, pady=(5, 0))

        self.transparent_var = tk.BooleanVar(value=False)
        self.transparent_cb = tk.Checkbutton(
            color_frame,
            text="透過",
            variable=self.transparent_var,
            command=self._on_transparent_change,
        )
        self.transparent_cb.pack(side=tk.LEFT)

        tk.Label(color_frame, text="背景色:").pack(side=tk.LEFT, padx=(10, 0))
        self.bg_color_var = tk.StringVar(value="#FFFFFF")
        self.bg_color_entry = tk.Entry(
            color_frame, textvariable=self.bg_color_var, width=8
        )
        self.bg_color_entry.pack(side=tk.LEFT, padx=(0, 5))

        self.color_preview = tk.Label(
            color_frame, text="  ", bg="#FFFFFF", relief="solid", width=3
        )
        self.color_preview.pack(side=tk.LEFT, padx=(0, 5))

        self.color_pick_btn = tk.Button(
            color_frame, text="色選択", command=self._pick_color
        )
        self.color_pick_btn.pack(side=tk.LEFT)

        self.bg_color_var.trace_add("write", self._on_color_var_change)
        self._on_size_mode_change()

        # --- 出力設定 ---
        output_frame = tk.LabelFrame(self, text="出力設定", padx=10, pady=5)
        output_frame.pack(fill=tk.X, padx=10, pady=5)

        self.output_var = tk.StringVar(value="output.png")
        tk.Entry(output_frame, textvariable=self.output_var, width=50).pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )
        tk.Button(output_frame, text="保存先を選択", command=self._select_output).pack(
            side=tk.LEFT, padx=(5, 0)
        )

        # --- ボタン行 ---
        btn_frame = tk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=10, pady=(5, 0))

        self.generate_btn = tk.Button(
            btn_frame,
            text="画像を生成",
            command=self._generate,
            height=2,
            bg="#4CAF50",
            fg="white",
        )
        self.generate_btn.pack(fill=tk.X)

        # 設定保存/読み込みボタン
        settings_frame = tk.Frame(self)
        settings_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Button(
            settings_frame,
            text="設定を保存",
            command=self._save_settings,
        ).pack(side=tk.LEFT, padx=(0, 5))
        tk.Button(
            settings_frame,
            text="設定を読み込み",
            command=self._load_settings_from_dialog,
        ).pack(side=tk.LEFT)

        self.status_var = tk.StringVar(
            value="URLを入力して「画像を生成」を押してください"
        )
        tk.Label(self, textvariable=self.status_var, anchor="w").pack(
            fill=tk.X, padx=10, pady=(0, 5)
        )

    # ------------------------------------------------------------------
    # 背景設定
    # ------------------------------------------------------------------
    def _select_bg_image(self) -> None:
        path = filedialog.askopenfilename(
            title="背景画像を選択",
            filetypes=[("画像ファイル", "*.png *.jpg *.jpeg *.gif *.bmp")],
        )
        if path:
            self.bg_path_var.set(path)

    def _clear_bg_image(self) -> None:
        self.bg_path_var.set("")

    def _pick_color(self) -> None:
        color = colorchooser.askcolor(
            initialcolor=self.bg_color_var.get(), title="背景色を選択"
        )
        if color[1]:
            self.bg_color_var.set(color[1])

    def _on_color_var_change(self, *_args: str) -> None:
        color = self.bg_color_var.get().strip()
        if len(color) == 7 and color.startswith("#"):
            try:
                int(color[1:], 16)
                self.color_preview.config(bg=color)
            except ValueError:
                pass

    def _on_transparent_change(self) -> None:
        is_transparent = self.transparent_var.get()
        state = tk.DISABLED if is_transparent else tk.NORMAL
        self.bg_color_entry.config(state=state)
        self.color_pick_btn.config(state=state)

    def _on_size_mode_change(self) -> None:
        mode = self.size_mode_var.get()
        is_bg_mode = mode == "background"
        custom_state = tk.NORMAL if mode == "custom" else tk.DISABLED
        self.custom_w_entry.config(state=custom_state)
        self.custom_h_entry.config(state=custom_state)

        # 背景色/透過は auto/custom 時のみ有効
        color_state = tk.DISABLED if is_bg_mode else tk.NORMAL
        self.transparent_cb.config(state=color_state)
        if is_bg_mode:
            self.bg_color_entry.config(state=tk.DISABLED)
            self.color_pick_btn.config(state=tk.DISABLED)
        else:
            self._on_transparent_change()

    # ------------------------------------------------------------------
    # 参加者行の更新
    # ------------------------------------------------------------------
    def _update_participant_rows(self) -> None:
        for row in self.participant_rows:
            row.destroy()
        self.participant_rows.clear()

        count = self.participant_count.get()
        for i in range(count):
            row = ParticipantRow(self.rows_frame, i)
            row.pack(fill=tk.X, pady=2)
            row.enable_drop()
            self.participant_rows.append(row)

    # ------------------------------------------------------------------
    # 設定の保存 / 読み込み
    # ------------------------------------------------------------------
    def _collect_settings(self) -> AppSettings:
        participants = [
            ParticipantSetting(name=r.get_name(), avatar_path=r.get_avatar())
            for r in self.participant_rows
        ]
        try:
            cw = int(self.custom_w_var.get())
        except ValueError:
            cw = 1280
        try:
            ch = int(self.custom_h_var.get())
        except ValueError:
            ch = 720

        return AppSettings(
            participant_count=self.participant_count.get(),
            participants=participants,
            output_path=self.output_var.get(),
            background=BackgroundSetting(
                image_path=self.bg_path_var.get(),
                size_mode=self.size_mode_var.get(),
                custom_width=cw,
                custom_height=ch,
                bg_color=self.bg_color_var.get(),
                transparent=self.transparent_var.get(),
            ),
        )

    def _apply_settings(self, settings: AppSettings) -> None:
        self.participant_count.set(settings.participant_count)
        self._update_participant_rows()

        for i, row in enumerate(self.participant_rows):
            if i < len(settings.participants):
                row.set_name(settings.participants[i].name)
                row.set_avatar(settings.participants[i].avatar_path)

        self.output_var.set(settings.output_path)

        self.bg_path_var.set(settings.background.image_path)
        self.size_mode_var.set(settings.background.size_mode)
        self.custom_w_var.set(str(settings.background.custom_width))
        self.custom_h_var.set(str(settings.background.custom_height))
        self.bg_color_var.set(settings.background.bg_color)
        self.transparent_var.set(settings.background.transparent)
        self._on_size_mode_change()
        self._on_transparent_change()

    def _save_settings(self) -> None:
        settings = self._collect_settings()
        save_settings(settings)
        self.status_var.set("設定を保存しました")

    def _load_saved_settings(self) -> None:
        """起動時に設定ファイルが存在すれば自動読み込み."""
        settings = load_settings()
        self._apply_settings(settings)

    def _load_settings_from_dialog(self) -> None:
        path = filedialog.askopenfilename(
            title="設定ファイルを選択",
            filetypes=[("JSON", "*.json")],
        )
        if path:
            settings = load_settings(path)
            self._apply_settings(settings)
            self.status_var.set(f"設定を読み込みました: {os.path.basename(path)}")

    # ------------------------------------------------------------------
    # 出力
    # ------------------------------------------------------------------
    def _select_output(self) -> None:
        path = filedialog.asksaveasfilename(
            title="保存先を選択",
            defaultextension=".png",
            filetypes=[("PNG画像", "*.png")],
        )
        if path:
            self.output_var.set(path)

    def _generate(self) -> None:
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("入力エラー", "URLを入力してください。")
            return

        if "race.netkeiba.com" not in url:
            messagebox.showwarning(
                "入力エラー", "netkeibaの出馬表URLを入力してください。"
            )
            return

        output_path = self.output_var.get().strip()
        if not output_path:
            messagebox.showwarning("入力エラー", "出力ファイルパスを指定してください。")
            return

        self.generate_btn.config(state=tk.DISABLED)
        self.status_var.set("データを取得中...")
        self.update()

        try:
            race_name, entries = fetch_shutuba(url)
            if not entries:
                messagebox.showerror(
                    "エラー", "馬データを取得できませんでした。URLを確認してください。"
                )
                return

            self.status_var.set(f"「{race_name}」{len(entries)}頭 - 画像生成中...")
            self.update()

            names = [r.get_name() for r in self.participant_rows]
            avatars = [r.get_avatar() for r in self.participant_rows]

            try:
                cw = int(self.custom_w_var.get())
            except ValueError:
                cw = 1280
            try:
                ch = int(self.custom_h_var.get())
            except ValueError:
                ch = 720

            result = generate_image(
                entries=entries,
                participant_names=names,
                avatar_paths=avatars,
                output_path=output_path,
                background_path=self.bg_path_var.get(),
                size_mode=self.size_mode_var.get(),
                custom_width=cw,
                custom_height=ch,
                bg_color=self.bg_color_var.get(),
                transparent=self.transparent_var.get(),
            )

            # 生成時に設定も自動保存
            self._save_settings()

            self.status_var.set(f"画像を保存しました: {result}")
            messagebox.showinfo("完了", f"画像を保存しました:\n{result}")

        except Exception as e:
            messagebox.showerror("エラー", f"エラーが発生しました:\n{e}")
            self.status_var.set("エラーが発生しました")
        finally:
            self.generate_btn.config(state=tk.NORMAL)


def main() -> None:
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
