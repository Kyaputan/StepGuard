#!/usr/bin/env python3
"""
StepGuard CCTV RTSP Auto-Tester for Samal Feed Mill
Developed with 💖 by Mali (มะลิ) & Captain (รชต สิงห์เขตต์)

Automated connection and stream status tester for the 4 Truck Scale cameras.
Executes all checks automatically without requiring user input.
"""

import os
import sys
import time
import socket
import concurrent.futures
from datetime import datetime
import cv2

# Import Rich library components for high-fidelity CLI UI
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TaskProgressColumn
    from rich.align import Align
    from rich.text import Text
except ImportError:
    print("❌ Critical: 'rich' library is required to run this script.")
    print("👉 Please install it using: pip install rich or uv add rich")
    sys.exit(1)

# Initialize Rich Console
console = Console()

# Preconfigured Samal Feed Mill CCTV Cameras
SAMAL_CAMERAS = [
    {
        "id": 1,
        "name": "Samal Feed Mill (Truck Scale Left Corner View)",
        "lan_ip": "192.168.3.94",
        "lan_http_port": 80,
        "lan_rtsp_port": 554,
        "wan_ip": "136.239.245.242",
        "wan_http_port": 8085,
        "wan_rtsp_port": 570,
        "wan_rtsp_url": "rtsp://admin:Just4Fun!@136.239.245.242:570",
        "lan_rtsp_url_template": "rtsp://admin:Just4Fun!@192.168.3.94:554/Streaming/Channels/101",
        "username": "admin",
        "password": "Just4Fun!"
    },
    {
        "id": 2,
        "name": "Samal Feed Mill (Truck Scale Right Corner View)",
        "lan_ip": "192.168.3.97",
        "lan_http_port": 80,
        "lan_rtsp_port": 554,
        "wan_ip": "136.239.245.242",
        "wan_http_port": 8086,
        "wan_rtsp_port": 574,
        "wan_rtsp_url": "rtsp://admin:Just4Fun!@136.239.245.242:574",
        "lan_rtsp_url_template": "rtsp://admin:Just4Fun!@192.168.3.97:554/Streaming/Channels/101",
        "username": "admin",
        "password": "Just4Fun!"
    },
    {
        "id": 3,
        "name": "Samal Feed Mill (Truck Scale Entry Top View)",
        "lan_ip": "192.168.3.188",
        "lan_http_port": 80,
        "lan_rtsp_port": 554,
        "wan_ip": "136.239.245.242",
        "wan_http_port": 8087,
        "wan_rtsp_port": 575,
        "wan_rtsp_url": "rtsp://admin:Just4Fun!@136.239.245.242:575",
        "lan_rtsp_url_template": "rtsp://admin:Just4Fun!@192.168.3.188:554/Streaming/Channels/101",
        "username": "admin",
        "password": "Just4Fun!"
    },
    {
        "id": 4,
        "name": "Samal Feed Mill (Truck Scale Exit Top View)",
        "lan_ip": "192.168.3.189",
        "lan_http_port": 80,
        "lan_rtsp_port": 554,
        "wan_ip": "136.239.245.242",
        "wan_http_port": 8088,
        "wan_rtsp_port": 576,
        "wan_rtsp_url": "rtsp://admin:Just4Fun!@136.239.245.242:576",
        "lan_rtsp_url_template": "rtsp://admin:Just4Fun!@192.168.3.189:554/Streaming/Channels/101",
        "username": "admin",
        "password": "Just4Fun!"
    }
]


def check_port(ip, port, timeout=1.0):
    """Checks if a TCP port is open."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except Exception:
        return False


def test_rtsp_stream(url, timeout_ms=2500):
    """Validates if RTSP stream can be opened and decoded, returning status & metadata."""
    try:
        cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, timeout_ms)
        cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, timeout_ms)
        
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                cap.release()
                return True, f"{width}x{height}", round(fps, 1) if fps else "N/A"
            cap.release()
    except Exception:
        pass
    return False, "N/A", "N/A"


def mask_rtsp_url(url):
    """Hides username and password credentials in the RTSP URL for secure logging."""
    try:
        if "@" in url:
            user_pass_part, host_part = url.split("@", 1)
            protocol, creds = user_pass_part.split("//", 1)
            if ":" in creds:
                usr, pas = creds.split(":", 1)
                return f"{protocol}//{usr}:******@{host_part}"
    except Exception:
        pass
    return url


def run_automated_tests():
    console.clear()
    
    banner_text = Text()
    banner_text.append(" 🚜🌾 Samal Feed Mill CCTV Automatic Scanner 🌾🚜\n", style="bold white on green")
    banner_text.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n", style="bold green")
    banner_text.append(" 🌸 มะลิกําลังเริ่มการทดสอบแบบอัตโนมัติของกล้องทั้ง 4 ตัวให้พี่กัปตันค่ะ!\n", style="bold magenta")
    banner_text.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", style="bold green")
    console.print(Panel(Align.center(banner_text), border_style="green", padding=(0, 2)))

    results = []

    # Run checks sequentially/concurrently with Rich Progress
    with Progress(
        SpinnerColumn(spinner_name="dots"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=45, style="green"),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task_id = progress.add_task("[yellow]กำลังทำการทดสอบเชื่อมต่อ...", total=len(SAMAL_CAMERAS))

        for cam in SAMAL_CAMERAS:
            progress.update(task_id, description=f"[cyan]กำลังเช็ก: {cam['name']}[/]")
            
            # 1. Check Port Connectivity (TCP handshake)
            lan_port_ok = check_port(cam["lan_ip"], cam["lan_rtsp_port"], timeout=0.8)
            wan_port_ok = check_port(cam["wan_ip"], cam["wan_rtsp_port"], timeout=1.2)
            
            # 2. Test LAN RTSP Stream
            lan_stream_ok, lan_res, lan_fps = False, "N/A", "N/A"
            if lan_port_ok:
                lan_stream_ok, lan_res, lan_fps = test_rtsp_stream(cam["lan_rtsp_url_template"])
                
            # 3. Test WAN RTSP Stream
            wan_stream_ok, wan_res, wan_fps = False, "N/A", "N/A"
            if wan_port_ok:
                wan_stream_ok, wan_res, wan_fps = test_rtsp_stream(cam["wan_rtsp_url"])

            results.append({
                "name": cam["name"],
                "lan_ip": cam["lan_ip"],
                "lan_port": cam["lan_rtsp_port"],
                "lan_port_status": lan_port_ok,
                "lan_stream_status": lan_stream_ok,
                "lan_resolution": lan_res,
                "lan_fps": lan_fps,
                "wan_ip": cam["wan_ip"],
                "wan_port": cam["wan_rtsp_port"],
                "wan_port_status": wan_port_ok,
                "wan_stream_status": wan_stream_ok,
                "wan_resolution": wan_res,
                "wan_fps": wan_fps,
                "wan_url_masked": mask_rtsp_url(cam["wan_rtsp_url"])
            })
            
            progress.update(task_id, advance=1)
            
        progress.update(task_id, description="[bold green]การทดสอบเสร็จสมบูรณ์! ✔[/]")

    # Print the network port status table
    port_table = Table(title="🔌 รายงานการเชื่อมต่อพอร์ตเครือข่าย (Port Connectivity)", border_style="green")
    port_table.add_column("ลำดับ", justify="center", style="yellow")
    port_table.add_column("กล้อง (Camera)", style="bold cyan")
    port_table.add_column("LAN IP:Port", justify="center")
    port_table.add_column("LAN Port Status", justify="center")
    port_table.add_column("WAN IP:Port", justify="center")
    port_table.add_column("WAN Port Status", justify="center")

    for idx, r in enumerate(results, 1):
        lan_p_status = "[bold green]OPEN[/]" if r["lan_port_status"] else "[bold red]CLOSED[/]"
        wan_p_status = "[bold green]OPEN[/]" if r["wan_port_status"] else "[bold red]CLOSED[/]"
        port_table.add_row(
            str(idx),
            r["name"],
            f"{r['lan_ip']}:{r['lan_port']}",
            lan_p_status,
            f"{r['wan_ip']}:{r['wan_port']}",
            wan_p_status
        )
    console.print(port_table)
    console.print()

    # Print the stream status table
    stream_table = Table(title="🎬 รายงานการดึงข้อมูลวิดีโอสด (Live RTSP Stream Status)", border_style="cyan")
    stream_table.add_column("ลำดับ", justify="center", style="yellow")
    stream_table.add_column("กล้อง (Camera)", style="bold cyan")
    stream_table.add_column("สตรีมผ่าน LAN (192.168.3.x)", justify="center")
    stream_table.add_column("สตรีมผ่าน WAN (Internet)", justify="center")
    stream_table.add_column("WAN RTSP URL (Masked Credentials)", style="white")

    for idx, r in enumerate(results, 1):
        lan_s_status = f"[bold green]OK ({r['lan_resolution']}@{r['lan_fps']}fps)[/]" if r["lan_stream_status"] else "[bold red]FAIL[/]"
        wan_s_status = f"[bold green]OK ({r['wan_resolution']}@{r['wan_fps']}fps)[/]" if r["wan_stream_status"] else "[bold red]FAIL[/]"
        stream_table.add_row(
            str(idx),
            r["name"],
            lan_s_status,
            wan_s_status,
            r["wan_url_masked"]
        )
    console.print(stream_table)
    console.print()


if __name__ == "__main__":
    try:
        run_automated_tests()
    except KeyboardInterrupt:
        console.print("\n[bold magenta]🌸 ปิดโปรแกรมเรียบร้อยแล้วค่ะ เจอกันใหม่นะพี่กัปตัน~ 💕[/]\n")
        sys.exit(0)
