"""PyInstallerでexeファイルをビルドするスクリプト."""

import subprocess
import sys
from pathlib import Path


def main() -> None:
    """PyInstallerを実行してexeを生成する."""
    root_dir = Path(__file__).parent

    # tkinterdnd2のデータファイルを収集するためのhidden-importとデータ指定
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name",
        "HorceRaceImageCreator",
        # tkinterdnd2のパッケージデータを含める
        "--collect-data",
        "tkinterdnd2",
        # hidden imports
        "--hidden-import",
        "tkinterdnd2",
        "--hidden-import",
        "PIL",
        "--hidden-import",
        "requests",
        "--hidden-import",
        "bs4",
        "--hidden-import",
        "lxml",
        # メインスクリプト
        str(root_dir / "main.py"),
    ]

    print("Building exe...")
    print(f"Command: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(root_dir))

    if result.returncode == 0:
        dist_dir = root_dir / "dist" / "HorceRaceImageCreator"
        print("\nBuild successful!")
        print(f"Output: {dist_dir}")
        if sys.platform == "win32":
            print(f"Exe: {dist_dir / 'HorceRaceImageCreator.exe'}")
    else:
        print("\nBuild failed!", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
