#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import sys
import shutil
from pathlib import Path

import yt_dlp


def clean_filename(name: str) -> str:
    """
    Fayl adını Linux/Kali üçün daha təmiz və təhlükəsiz edir.
    """
    name = name.replace("/", "-").replace("\\", "-")
    name = re.sub(r'[<>:"|?*]', "", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def check_dependencies():
    """
    Sistem asılılıqlarını yoxlayır.
    """
    missing = []

    if shutil.which("ffmpeg") is None:
        missing.append("ffmpeg")

    # yt-dlp warning-ə görə ən praktik JS runtime olaraq node yoxlayırıq
    js_runtime_exists = any(
        shutil.which(cmd) is not None
        for cmd in ["node", "deno", "bun", "qjs", "quickjs"]
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
        print("[INFO] İndi birləşdirmə/emal başlayır...")


def main():
    if len(sys.argv) != 2:
        print("İstifadə:")
        print("  python youtube.py VIDEO_ID")
        print("Misal:")
        print("  python youtube.py X-oA2ZLVswE")
        sys.exit(1)

    video_id = sys.argv[1].strip()
    if not re.fullmatch(r"[\w-]{6,20}", video_id):
        print("[XƏTA] VIDEO_ID formatı düzgün görünmür.")
        sys.exit(1)

    missing, js_runtime_exists = check_dependencies()

    if missing:
        print("[XƏTA] Aşağıdakı proqram(lar) sistemdə tapılmadı:")
        for item in missing:
            print(f"  - {item}")
        print("\nKali üçün:")
        print("  sudo apt update")
        print("  sudo apt install -y ffmpeg")
        sys.exit(2)

    if not js_runtime_exists:
        print("[XƏBƏRDARLIQ] JS runtime tapılmadı (node/deno/bun/qjs).")
        print("[XƏBƏRDARLIQ] yt-dlp işləyə bilər, amma bəzi formatlar itə bilər.")
        print("[TÖVSİYƏ] Kali üçün:")
        print("  sudo apt update")
        print("  sudo apt install -y nodejs")
        print("")

    url = f"https://www.youtube.com/watch?v={video_id}"
    output_dir = Path("downloads")
    output_dir.mkdir(parents=True, exist_ok=True)

    def format_outtmpl(info_dict):
        title = info_dict.get("title", "video")
        safe_title = clean_filename(title)
        vid = info_dict.get("id", "unknown")
        return str(output_dir / f"{safe_title} [{vid}].%(ext)s")

    ydl_opts = {
        # Ən yüksək mümkün keyfiyyət
        "format": "bv*+ba/b",
        "merge_output_format": "mp4",

        # Fayl adı
        "outtmpl": format_outtmpl,

        # Tək video
        "noplaylist": True,

        # Davam etdirmə
        "continuedl": True,

        # Progress
        "progress_hooks": [progress_hook],

        # Metadata oxuma
        "quiet": False,
        "no_warnings": False,

        # YouTube üçün extractor davranışı
        # Bu, bəzi warning-ləri və format problemlərini azaltmağa kömək edir
        "extractor_args": {
            "youtube": {
                "player_client": ["default", "tv"]
            }
        },

        # Bəzi hallarda format seçimini bir az daha yaxşılaşdırır
        "format_sort": ["res", "fps", "hdr:12", "codec:avc:m4a"],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"[INFO] Link: {url}")
            info = ydl.extract_info(url, download=False)

            title = info.get("title", "Naməlum")
            uploader = info.get("uploader", "Naməlum")
            duration = info.get("duration", "Naməlum")

            print(f"[INFO] Başlıq   : {title}")
            print(f"[INFO] Kanal    : {uploader}")
            print(f"[INFO] Müddət   : {duration} saniyə" if isinstance(duration, int) else f"[INFO] Müddət   : {duration}")
            print("[INFO] Ən yüksək keyfiyyətdə yükləmə başlayır...")

            ydl.download([url])

        print("\n[UĞURLU] Video yükləndi.")
        print(f"[QOVLUQ] {output_dir.resolve()}")

    except yt_dlp.utils.DownloadError as e:
        print(f"[XƏTA] Yükləmə xətası: {e}")
        print("\nYoxla:")
        print('  1. pip install -U "yt-dlp[default]"')
        print("  2. ffmpeg quraşdırılıb?")
        print("  3. nodejs quraşdırılıb?")
        sys.exit(3)

    except KeyboardInterrupt:
        print("\n[DAYANDIRILDI] İstifadəçi tərəfindən dayandırıldı.")
        sys.exit(130)

    except Exception as e:
        print(f"[XƏTA] Gözlənilməz problem: {e}")
        sys.exit(4)


if __name__ == "__main__":
    main()
