"""競馬配信用画像生成ツール - メインGUI."""

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from image_generator import generate_image
from scraper import fetch_shutuba

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
            self, text="アバター: 未選択", width=20, anchor="w"
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

    def get_avatar(self) -> str:
        return self.avatar_path


class App(tk.Tk):
    """メインアプリケーション."""

    def __init__(self) -> None:
        super().__init__()
        self.title("競馬配信用画像生成ツール")
        self.geometry("600x500")
        self.resizable(False, False)

        self._create_widgets()

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

        # --- 生成ボタン ---
        btn_frame = tk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        self.generate_btn = tk.Button(
            btn_frame,
            text="画像を生成",
            command=self._generate,
            height=2,
            bg="#4CAF50",
            fg="white",
        )
        self.generate_btn.pack(fill=tk.X)

        self.status_var = tk.StringVar(
            value="URLを入力して「画像を生成」を押してください"
        )
        tk.Label(self, textvariable=self.status_var, anchor="w").pack(
            fill=tk.X, padx=10, pady=(0, 5)
        )

    def _update_participant_rows(self) -> None:
        for row in self.participant_rows:
            row.destroy()
        self.participant_rows.clear()

        count = self.participant_count.get()
        for i in range(count):
            row = ParticipantRow(self.rows_frame, i)
            row.pack(fill=tk.X, pady=2)
            self.participant_rows.append(row)

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

            result = generate_image(
                entries=entries,
                participant_names=names,
                avatar_paths=avatars,
                output_path=output_path,
            )

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
