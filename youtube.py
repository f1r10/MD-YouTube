#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import sys
import shutil
from pathlib import Path

import yt_dlp


def clean_filename(name: str) -> str:
    name = name.replace("/", "-").replace("\\", "-")
    name = re.sub(r'[<>:"|?*]', "", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def check_dependencies():
    missing = []

    if shutil.which("ffmpeg") is None:
        missing.append("ffmpeg")

    js_runtime_exists = any(
        shutil.which(cmd) is not None
        for cmd in ["deno", "node", "bun", "qjs", "quickjs"]
    )

    return missing, js_runtime_exists


def progress_hook(d):
    status = d.get("status")

    if status == "downloading":
        percent = d.get("_percent_str", "").strip()
        speed = d.get("_speed_str", "Unknown")
        eta = d.get("_eta_str", "Unknown")
        filename = d.get("filename", "")
        print(f"[YÜKLƏNİR] {percent} | Sürət: {speed} | ETA: {eta} | {filename}")

    elif status == "finished":
        filename = d.get("filename", "")
        print(f"[TAMAMLANDI] Fayl endi: {filename}")
        print("[INFO] İndi birləşdirmə başlayır...")


def main():
    if len(sys.argv) != 2:
        print("İstifadə:")
        print("  python youtube.py VIDEO_ID")
        print("Misal:")
        print("  python youtube.py X-oA2ZLVswE")
        sys.exit(1)

    video_id = sys.argv[1].strip()

    if not re.fullmatch(r"[\w-]{6,20}", video_id):
        print("[XƏTA] VIDEO_ID formatı düzgün deyil.")
        sys.exit(1)

    missing, js_runtime_exists = check_dependencies()

    if missing:
        print("[XƏTA] Aşağıdakı asılılıqlar tapılmadı:")
        for item in missing:
            print(f"  - {item}")
        print("\nKali üçün quraşdır:")
        print("  sudo apt update")
        print("  sudo apt install -y ffmpeg")
        sys.exit(2)

    if not js_runtime_exists:
        print("[XƏBƏRDARLIQ] JS runtime tapılmadı.")
        print("[XƏBƏRDARLIQ] YouTube üçün bəzi formatlar itə bilər.")
        print("[TÖVSİYƏ] Deno və ya Node qur.")
        print("  sudo apt update")
        print("  sudo apt install -y nodejs npm")
        print("")

    url = f"https://www.youtube.com/watch?v={video_id}"
    output_dir = Path("downloads")
    output_dir.mkdir(parents=True, exist_ok=True)

    outtmpl = str(output_dir / "%(title)s [%(id)s].%(ext)s")

    ydl_opts = {
        "format": "bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
        "outtmpl": outtmpl,
        "restrictfilenames": False,
        "windowsfilenames": False,
        "trim_file_name": 180,
        "noplaylist": True,
        "continuedl": True,
        "progress_hooks": [progress_hook],
        "quiet": False,
        "no_warnings": False,
        "consoletitle": False,
        "paths": {"home": str(output_dir)},
        "final_ext": "mp4",
        "postprocessors": [
            {
                "key": "FFmpegVideoRemuxer",
                "preferedformat": "mp4",
            }
        ],
        "extractor_args": {
            "youtube": {
                "player_client": ["default"],
            }
        },
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"[INFO] Link: {url}")
            info = ydl.extract_info(url, download=False)

            title = clean_filename(info.get("title", "video"))
            uploader = info.get("uploader", "Naməlum")
            duration = info.get("duration", "Naməlum")

            print(f"[INFO] Başlıq   : {title}")
            print(f"[INFO] Kanal    : {uploader}")
            if isinstance(duration, int):
                print(f"[INFO] Müddət   : {duration} saniyə")
            else:
                print(f"[INFO] Müddət   : {duration}")

            print("[INFO] Ən yüksək keyfiyyətdə yükləmə başlayır...")

            # burada title təmizlənmiş formada info dict-ə yazılır ki fayl adı daha təmiz olsun
            info["title"] = title
            ydl.process_info(info)

        print("\n[UĞURLU] Video yükləndi.")
        print(f"[QOVLUQ] {output_dir.resolve()}")

    except yt_dlp.utils.DownloadError as e:
        print(f"[XƏTA] Yükləmə xətası: {e}")
        print("\nYoxla:")
        print('  pip install -U "yt-dlp[default]"')
        print("  pip install -U yt-dlp-ejs")
        print("  sudo apt install -y ffmpeg")
        print("  sudo apt install -y nodejs npm")
        sys.exit(3)

    except KeyboardInterrupt:
        print("\n[DAYANDIRILDI] İstifadəçi tərəfindən dayandırıldı.")
        sys.exit(130)

    except Exception as e:
        print(f"[XƏTA] Gözlənilməz problem: {e}")
        sys.exit(4)


if __name__ == "__main__":
    main()
