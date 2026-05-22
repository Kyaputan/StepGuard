#!/usr/bin/env python3
"""
StepGuard CCTV RTSP Finder & Scanner (v2.0)
Developed with 💖 by Mali (มะลิ) & Captain (รชต สิงห์เขตต์)

A premium, interactive CLI utility to scan, discover, validate, and preview 
CCTV camera RTSP feeds with ultra-fast multi-threading and an elegant Rich TUI.
"""

import os
import sys
import time
import socket
import json
import threading
import ipaddress
import concurrent.futures
from datetime import datetime
import cv2

# Import Rich library components for high-fidelity CLI UI
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TaskProgressColumn
    from rich.prompt import Prompt, IntPrompt, Confirm
    from rich.align import Align
    from rich.status import Status
    from rich.text import Text
except ImportError:
    print("❌ Critical: 'rich' library is required to run this script.")
    print("👉 Please install it using: pip install rich or uv add rich")
    sys.exit(1)

# Initialize Rich Console
console = Console()

# Configuration File Name
CONFIG_FILE = "cctv_config.json"

DEFAULT_CONFIG = {
    "user": "Rachata",
    "password": "password123",
    "ip": "192.168.1.100",
    "ports_to_test": [554, 556, 8554, 80, 8080],
    "rtsp_suffixes": [
        # Standard channels
        "/stream1",
        "/stream2",
        "/live/stream1",
        "/live/stream2",
        "/h264/ch1/main/av_stream",
        "/h264/ch1/sub/av_stream",
        "/live1.sdp",
        "/live2.sdp",
        "/1",
        "/2",
        "/channel1",
        "/media/video1",
        # Hikvision typical formats
        "/Streaming/Channels/101",
        "/Streaming/Channels/102",
        "/Streaming/Channels/1",
        "/Streaming/Channels/2",
        # Dahua typical formats
        "/cam/realmonitor?channel=1&subtype=0",
        "/cam/realmonitor?channel=1&subtype=1",
        # Generic & Custom VLC targets
        "/onvif1",
        "/onvif2",
        "/video",
        "/",
    ]
}


class ConfigManager:
    """Manages reading and writing CCTV scanner configuration persistently."""
    
    @staticmethod
    def load():
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # Merge loaded keys to ensure no keys are missing
                    config = DEFAULT_CONFIG.copy()
                    config.update(loaded)
                    return config
            except Exception as e:
                console.print(f"[bold red]⚠ Cannot read config file: {e}. Using defaults.[/]")
        return DEFAULT_CONFIG.copy()

    @staticmethod
    def save(config):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            console.print(f"[bold red]❌ Cannot save config file: {e}[/]")
            return False


class NetworkScanner:
    """Discovers devices in the local network with open RTSP/HTTP ports concurrently."""

    @staticmethod
    def get_local_ip():
        """Obtains the primary local IP address of this machine."""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # Connect to a public IP to trigger routing (no actual packet is sent)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        except Exception:
            ip = "127.0.0.1"
        finally:
            s.close()
        return ip

    @staticmethod
    def get_default_subnet(ip):
        """Calculates standard /24 subnet from an IP address."""
        try:
            parts = ip.split('.')
            if len(parts) == 4:
                return f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
        except Exception:
            pass
        return "192.168.1.0/24"

    @staticmethod
    def check_port(ip, port, timeout=0.6):
        """Quickly checks if a specific port is open on an IP address using raw TCP socket."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, port))
            sock.close()
            return result == 0
        except Exception:
            return False

    @classmethod
    def scan_subnet(cls, subnet_str, ports, progress_bar):
        """Scans all hosts in a /24 subnet for open target ports in parallel threads."""
        try:
            net = ipaddress.ip_network(subnet_str, strict=False)
            hosts = [str(ip) for ip in net.hosts()]
        except Exception:
            # Fallback in case IP address library raises an exception
            parts = subnet_str.split('.')
            base = f"{parts[0]}.{parts[1]}.{parts[2]}"
            hosts = [f"{base}.{i}" for i in range(1, 255)]

        found_devices = {}
        lock = threading.Lock()
        
        # Calculate total tasks
        total_tasks = len(hosts) * len(ports)
        task_id = progress_bar.add_task("[cyan]Scanning Subnet...", total=total_tasks)

        def worker(ip, port):
            if cls.check_port(ip, port):
                with lock:
                    if ip not in found_devices:
                        found_devices[ip] = []
                    found_devices[ip].append(port)
            progress_bar.update(task_id, advance=1)

        # Use concurrent ThreadPoolExecutor for rapid asynchronous port scanning
        with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
            futures = []
            for ip in hosts:
                for port in ports:
                    futures.append(executor.submit(worker, ip, port))
            concurrent.futures.wait(futures)

        return found_devices


class RTSPValidator:
    """Validates RTSP paths and credentials on a specific IP in parallel."""

    @staticmethod
    def test_single_url(ip, user, password, suffix, timeout_open=1500, timeout_read=1000):
        """Tests connection to a single RTSP stream, returning metadata if successful."""
        # Clean suffix (must start with / or :)
        if not suffix.startswith('/') and not suffix.startswith(':'):
            suffix = '/' + suffix

        # Handle port specifications in suffix (e.g., ':556/stream1')
        if suffix.startswith(':'):
            raw_url = f"rtsp://{user}:{password}@{ip}{suffix}"
            masked_url = f"rtsp://{user}:******@{ip}{suffix}"
        else:
            raw_url = f"rtsp://{user}:{password}@{ip}:554{suffix}"
            masked_url = f"rtsp://{user}:******@{ip}:554{suffix}"

        try:
            # Instantiate OpenCV VideoCapture
            cap = cv2.VideoCapture(raw_url, cv2.CAP_FFMPEG)
            
            # Apply optimized timeouts to prevent long hanging blocks
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, timeout_open)
            cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, timeout_read)

            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    if fps is None or fps <= 0:
                        fps = 25.0
                    cap.release()
                    return {
                        "success": True,
                        "url": raw_url,
                        "masked_url": masked_url,
                        "suffix": suffix,
                        "resolution": f"{width}x{height}",
                        "fps": round(fps, 2)
                    }
                cap.release()
        except Exception:
            pass
        
        return {"success": False, "url": raw_url, "masked_url": masked_url, "suffix": suffix}

    @classmethod
    def scan_credentials_and_paths(cls, ip, user, password, suffixes, progress_bar):
        """Validates dozens of potential RTSP suffixes concurrently using a ThreadPool."""
        successful_streams = []
        lock = threading.Lock()
        
        total = len(suffixes)
        task_id = progress_bar.add_task("[yellow]Testing RTSP Suffixes...", total=total)

        def worker(suffix):
            res = cls.test_single_url(ip, user, password, suffix)
            if res["success"]:
                with lock:
                    successful_streams.append(res)
            progress_bar.update(task_id, advance=1)

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(worker, suffix) for suffix in suffixes]
            concurrent.futures.wait(futures)

        return successful_streams


class VideoStreamReader:
    """Asynchronously reads frames from an RTSP stream in a background thread to prevent UI lag."""
    
    def __init__(self, rtsp_url):
        self.rtsp_url = rtsp_url
        self.cap = None
        self.frame = None
        self.ret = False
        self.running = False
        self.thread = None
        self.lock = threading.Lock()

    def start(self):
        self.cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 2500)
        
        if not self.cap.isOpened():
            return False

        self.running = True
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()
        return True

    def _update(self):
        while self.running:
            if self.cap and self.cap.isOpened():
                ret, frame = self.cap.read()
                with self.lock:
                    self.ret = ret
                    if ret:
                        self.frame = frame
            else:
                with self.lock:
                    self.ret = False
                break
            time.sleep(0.005) # Prevent high CPU utilization

    def read(self):
        with self.lock:
            if self.ret and self.frame is not None:
                return True, self.frame.copy()
            return False, None

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        if self.cap:
            self.cap.release()


class StreamPreviewer:
    """Opens a high-performance live CCTV stream preview in OpenCV with beautiful telemetry overlays."""

    @staticmethod
    def preview(raw_url, masked_url):
        console.print(f"\n[bold yellow]🎬 Initiating connection to preview stream...[/]")
        console.print(f"[cyan]RTSP:[/] {masked_url}")
        
        reader = VideoStreamReader(raw_url)
        
        with Status("[bold cyan]Connecting to video stream feed...", spinner="dots") as status:
            success = reader.start()
            if not success:
                console.print("[bold red]❌ Failed to connect to stream. Make sure the camera is online.[/]")
                return

        console.print("[bold green]✔ Stream loaded successfully! Opening preview window...[/]")
        console.print("[bold white]💡 Keyboard Controls: [green]'S'[/] to Capture Snapshot | [red]'Q'[/] or [red]'ESC'[/] to Close Preview Window[/]\n")

        fps_start_time = time.time()
        fps_counter = 0
        fps_display = "Calculating..."
        
        # Create preview directory if it doesn't exist
        os.makedirs("snapshots", exist_ok=True)

        # Set OpenCV Window property to handle high DPI displays nicely
        window_title = f"StepGuard CCTV Stream: {masked_url.split('@')[-1]}"
        cv2.namedWindow(window_title, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_title, 960, 540)

        try:
            while True:
                ret, frame = reader.read()
                if not ret or frame is None:
                    # Render placeholder if a frame is dropped temporarily
                    time.sleep(0.01)
                    continue

                # Calculate real-time FPS
                fps_counter += 1
                elapsed = time.time() - fps_start_time
                if elapsed >= 1.0:
                    fps_display = f"{round(fps_counter / elapsed, 1)} FPS"
                    fps_counter = 0
                    fps_start_time = time.time()

                # Get dimensions
                h, w, _ = frame.shape

                # 🎨 Overlay Telemetry UI on Frame (Darker top bar)
                cv2.rectangle(frame, (0, 0), (w, 45), (15, 15, 15), -1)
                
                # Add elegant visual status lights and telemetry labels
                cv2.circle(frame, (20, 22), 8, (0, 255, 0), -1) # Green heartbeat status
                
                text_info = f"LIVE | Res: {w}x{h} | {fps_display} | [S] Capture | [Q] Close"
                cv2.putText(frame, text_info, (40, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
                cv2.putText(frame, f"Cam: {masked_url.split('/')[-1]}", (w - 280, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1, cv2.LINE_AA)

                # Show frame in OpenCV GUI window
                cv2.imshow(window_title, frame)

                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27: # 'q' or ESC to exit
                    break
                elif key == ord('s') or key == ord('S'): # 's' to take snapshot
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"snapshots/cctv_capture_{timestamp}.jpg"
                    # Capture raw frame without overlays
                    _, raw_frame = reader.read()
                    if raw_frame is not None:
                        cv2.imwrite(filename, raw_frame)
                        console.print(f"[bold green]📸 Snapshot captured and saved to: {filename}[/]")
                        
                        # Briefly flash a success alert directly on the preview window
                        flash_frame = frame.copy()
                        cv2.rectangle(flash_frame, (0, h // 2 - 30), (w, h // 2 + 30), (0, 200, 0), -1)
                        cv2.putText(flash_frame, "SNAPSHOT SAVED!", (w // 2 - 120, h // 2 + 10), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2, cv2.LINE_AA)
                        cv2.imshow(window_title, flash_frame)
                        cv2.waitKey(400)

        finally:
            reader.stop()
            cv2.destroyAllWindows()
            console.print("[bold green]✔ Preview stream closed successfully.[/]")


class InteractiveTUI:
    """The central User Interface Coordinator class rendering the TUI and driving the logic flow."""

    def __init__(self):
        self.config = ConfigManager.load()
        self.console = console

    def display_banner(self):
        """Displays a gorgeous gradient colored StepGuard banner and configuration info."""
        self.console.clear()
        
        banner_text = Text()
        banner_text.append(" 📱🚫 StepGuard CCTV Scanner & Finder v2.0 \n", style="bold white on blue")
        banner_text.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n", style="bold blue")
        banner_text.append(" 🌸 มะลิยินดีต้อนรับพี่กัปตัน! พร้อมบริการแล้วค่ะ\n", style="bold magenta")
        
        # We append styled segments correctly instead of raw bracket tags inside Text.append
        banner_text.append(" ⚙ Config: User=", style="italic gray")
        banner_text.append(str(self.config['user']), style="bold yellow")
        banner_text.append(" | IP=", style="italic gray")
        banner_text.append(str(self.config['ip']), style="bold yellow")
        banner_text.append(" | Ports=", style="italic gray")
        banner_text.append(str(self.config['ports_to_test']), style="bold yellow")
        banner_text.append("\n", style="italic gray")
        
        banner_text.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", style="bold blue")

        self.console.print(Panel(Align.center(banner_text), border_style="blue", padding=(0, 2)))

    def show_menu(self):
        """Displays interactive menu choices for the user."""
        table = Table(box=None, show_header=False, padding=(0, 2))
        table.add_column("Key", style="bold cyan")
        table.add_column("Description", style="white")

        table.add_row("[1]", "🌐 สแกนหา CCTV ในเครือข่ายภายในบ้าน/สำนักงาน (Auto-Discover Network)")
        table.add_row("[2]", "🔍 ทดสอบหา RTSP URL และรหัสผ่านของกล้องเฉพาะเจาะาะจง (Credential & Path Scan)")
        table.add_row("[3]", "🎬 เปิดหน้าต่างพรีวิวดูวิดีโอสด (Live Video Stream Previewer)")
        table.add_row("[4]", "⚙ ตั้งค่าสแกนเนอร์ (Modify Credentials, IPs & Target Ports)")
        table.add_row("[5]", "❌ ออกจากโปรแกรม (Exit)")

        self.console.print(Panel(table, title="[bold yellow]📌 เมนูหลัก (Main Menu)[/]", border_style="yellow"))

    def run(self):
        while True:
            self.display_banner()
            self.show_menu()
            
            choice = Prompt.ask("👉 เลือกทำรายการ (1-5)", choices=["1", "2", "3", "4", "5"], default="2")
            
            if choice == "1":
                self.run_network_discovery()
            elif choice == "2":
                self.run_rtsp_deep_scan()
            elif choice == "3":
                self.run_direct_preview()
            elif choice == "4":
                self.run_config_editor()
            elif choice == "5":
                self.console.print("\n[bold magenta]🌸 ขอบคุณพี่กัปตันที่ไว้วางใจให้มะลิช่วยทำงานนะคะ! ขอให้เป็นวันที่ดีค่ะ! บ๊ายบายค่ะ~ 💕[/]\n")
                break
                
            input("\n👉 กด [Enter] เพื่อกลับสู่เมนูหลัก...")

    def run_network_discovery(self):
        """Allows discovery of CCTV cameras on local subnet using quick multithreaded port scan."""
        self.console.print("\n[bold cyan]🌐 ค้นหากล้องวงจรปิดอัตโนมัติในเครือข่าย (Auto-Discovery Mode)[/]")
        
        local_ip = NetworkScanner.get_local_ip()
        default_subnet = NetworkScanner.get_default_subnet(local_ip)
        
        self.console.print(f"📡 IP ของเครื่องคอมพิวเตอร์ปัจจุบัน: [bold yellow]{local_ip}[/]")
        
        subnet_input = Prompt.ask("🖥 ระบุ Subnet ที่ต้องการสแกน", default=default_subnet)
        
        # Verify valid subnet format
        try:
            ipaddress.ip_network(subnet_input, strict=False)
        except Exception:
            self.console.print("[bold red]❌ รูปแบบ Subnet ไม่ถูกต้อง! ตัวอย่างรูปแบบที่ควรใช้: 192.168.1.0/24[/]")
            return

        ports = self.config["ports_to_test"]
        self.console.print(f"⚡ กำลังเริ่มสแกนพอร์ต [yellow]{ports}[/] บนช่วงเครือข่าย [yellow]{subnet_input}[/]...")

        found_devices = {}
        
        # Run multithreaded scan with a beautiful progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=40),
            TaskProgressColumn(),
            console=self.console
        ) as progress:
            found_devices = NetworkScanner.scan_subnet(subnet_input, ports, progress)

        # Print discovery summary
        if found_devices:
            self.console.print(f"\n[bold green]🎉 ค้นพบอุปกรณ์ทั้งหมด {len(found_devices)} ตัว ที่เปิดช่องทางกล้องวงจรปิด! 🔓[/]\n")
            
            table = Table(title="อุปกรณ์กล้องวงจรปิดที่ตรวจจับได้ (Discovered Cameras)", border_style="cyan")
            table.add_column("ลำดับ (#)", style="bold yellow", justify="center")
            table.add_column("IP Address", style="bold green")
            table.add_column("พอร์ตที่เปิดใช้งาน (Open Ports)", style="magenta")
            table.add_column("การวิเคราะห์ (Detection Notes)", style="white")

            devices_list = list(found_devices.items())
            for idx, (ip, open_ports) in enumerate(devices_list, 1):
                notes = []
                if 554 in open_ports or 556 in open_ports or 8554 in open_ports:
                    notes.append("[green]รองรับบริการ RTSP (แนะนำ)[/]")
                if 80 in open_ports or 8080 in open_ports:
                    notes.append("[cyan]รองรับ HTTP Web Admin[/]")
                
                table.add_row(
                    str(idx),
                    ip,
                    ", ".join(map(str, open_ports)),
                    " | ".join(notes)
                )

            self.console.print(table)
            
            # Offer deep scan on one of the found IPs
            if Confirm.ask("\n🔍 ต้องการเริ่มสแกนเพื่อทดสอบสตรีมและยืนยันข้อมูลจากอุปกรณ์เหล่านี้เลยไหมคะ?"):
                selected_idx = IntPrompt.ask(f"👉 เลือกลำดับกล้องที่ต้องการสแกน (1-{len(devices_list)})", default=1)
                if 1 <= selected_idx <= len(devices_list):
                    chosen_ip = devices_list[selected_idx - 1][0]
                    self.config["ip"] = chosen_ip
                    ConfigManager.save(self.config)
                    self.run_rtsp_deep_scan()
        else:
            self.console.print("\n[bold red]❌ ไม่พบอุปกรณ์กล้องวงจรปิดที่เปิดพอร์ต RTSP หรือ HTTP ในวงแลนช่วงนี้เลยค่ะ[/]")

    def run_rtsp_deep_scan(self):
        """Runs the detailed RTSP path and credential scanner on a target IP."""
        self.console.print("\n[bold yellow]🔍 สแกนรายละเอียดและข้อมูลยืนยันตัวตนกล้องวงจรปิด (Deep RTSP Scanner)[/]")
        
        target_ip = Prompt.ask("🖥 ใส่ IP Address ของกล้องที่ต้องการทดสอบ", default=self.config["ip"])
        username = Prompt.ask("👤 Username สำหรับกล้อง", default=self.config["user"])
        password = Prompt.ask("🔑 Password สำหรับกล้อง", default=self.config["password"])
        
        # Save IP to configuration dynamically for convenience
        self.config["ip"] = target_ip
        self.config["user"] = username
        self.config["password"] = password
        ConfigManager.save(self.config)

        suffixes = self.config["rtsp_suffixes"]
        self.console.print(f"\n⚡ กำลังทำการทดสอบรูปแบบ URL ทั้งหมด [cyan]{len(suffixes)} รูปแบบ[/] แบบขนาน...")

        successful_streams = []

        with Progress(
            SpinnerColumn(spinner_name="simpleDotsScrolling"),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=40, style="yellow"),
            TaskProgressColumn(),
            console=self.console
        ) as progress:
            successful_streams = RTSPValidator.scan_credentials_and_paths(
                target_ip, username, password, suffixes, progress
            )

        # Print deep scan summary table
        if successful_streams:
            self.console.print(f"\n[bold green]🎉 สำเร็จ! ตรวจพบ {len(successful_streams)} ช่องทางสตรีมวิดีโอที่สามารถเชื่อมต่อได้! ✔[/]\n")
            
            table = Table(title=f"ช่องสัญญาณกล้อง CCTV ที่เชื่อมต่อสำเร็จของ IP: {target_ip}", border_style="yellow")
            table.add_column("ลำดับ (#)", style="bold cyan", justify="center")
            table.add_column("RTSP URL Pattern (Masked)", style="white")
            table.add_column("Resolution (ความละเอียด)", style="green")
            table.add_column("FPS (เฟรมเรต)", style="magenta", justify="center")

            for idx, stream in enumerate(successful_streams, 1):
                table.add_row(
                    str(idx),
                    stream["masked_url"],
                    stream["resolution"],
                    str(stream["fps"])
                )

            self.console.print(table)

            # Recommend the best connection (determined by higher resolution and FPS combo)
            best_stream = max(successful_streams, key=lambda x: (int(x["resolution"].split('x')[0]) * int(x["resolution"].split('x')[1]), x["fps"]))
            self.console.print("\n[bold green]🏆 ช่องทางเชื่อมต่อแนะนำที่ให้คุณภาพการแสดงผลดีที่สุด (Recommended Stream):[/]")
            self.console.print(f"   👉 [cyan]URL:[/] [bold white]{best_stream['masked_url']}[/]")
            self.console.print(f"   👉 [cyan]Resolution:[/] {best_stream['resolution']} | [cyan]FPS:[/] {best_stream['fps']}")
            
            # Print sample integration code for StepGuard
            self.console.print(f"\n[bold white]📝 ตัวอย่างโค้ดไปใช้ในระบบหลัก (Integration Code):[/]")
            self.console.print(Panel(
                f"[green]cap = cv2.VideoCapture('{best_stream['url']}', cv2.CAP_FFMPEG)[/]\n"
                f"[green]cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)[/]\n"
                f"[green]cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 2000)[/]",
                title="Python Implementation snippet", border_style="green"
            ))

            # Prompt to preview the stream right away
            if Confirm.ask("\n🎬 ต้องการเปิดหน้าต่างพรีวิวเพื่อตรวจสอบภาพเคลื่อนไหวของกล้องตัวนี้ทันทีเลยไหมคะ?"):
                selected_idx = IntPrompt.ask(f"👉 เลือกลำดับสตรีมที่ต้องการเปิดพรีวิว (1-{len(successful_streams)})", default=1)
                if 1 <= selected_idx <= len(successful_streams):
                    chosen_stream = successful_streams[selected_idx - 1]
                    StreamPreviewer.preview(chosen_stream["url"], chosen_stream["masked_url"])
        else:
            self.console.print(f"\n[bold red]❌ การทดสอบเสร็จสิ้น แต่ไม่พบรูปแบบสัญญาณ RTSP URL ใดที่เข้ากันได้กับ IP {target_ip} หรือข้อมูลรหัสผ่านข้างต้น[/]")
            self.console.print("\n[bold yellow]💡 คำแนะนำการแก้ปัญหาขั้นต้นจากมะลิ:[/]")
            self.console.print("   1. กรุณาตรวจสอบว่ากล้องเปิดเครื่องและต่ออินเทอร์เน็ตอยู่จริง")
            self.console.print("   2. ตรวจสอบ Username / Password ให้ถูกต้อง และไม่พิมพ์ผิด")
            self.console.print("   3. รันเมนู [1] สแกนหาอุปกรณ์วงแลน เพื่อเช็กว่าพอร์ต RTSP (554/556) เปิดอยู่จริงหรือไม่")
            self.console.print("   4. หากเป็นกล้องยี่ห้อเฉพาะ อาจต้องใช้รูปแบบพอร์ต/ลิงก์พิเศษเพิ่มเติม")

    def run_direct_preview(self):
        """Allows direct playback of any user-specified RTSP URL."""
        self.console.print("\n[bold cyan]🎬 เครื่องมือเปิดพรีวิวสตรีมสด (Direct Video Stream Previewer)[/]")
        
        # Build a helpful suggestion
        suggested_url = f"rtsp://{self.config['user']}:{self.config['password']}@{self.config['ip']}:554/stream1"
        self.console.print(f"👉 ตัวอย่างรูปแบบลิงก์: [gray]{suggested_url}[/]")
        
        rtsp_input = Prompt.ask("🔗 กรุณากรอก RTSP URL ที่ถูกต้องแบบเต็ม (ตัวแอปจะเปิดพรีวิวทันที)")
        
        if not rtsp_input.strip():
            self.console.print("[bold red]❌ ลิงก์ห้ามว่างเปล่า![/]")
            return

        # Mask password in URL for display security
        masked_url = rtsp_input
        try:
            if '@' in rtsp_input:
                user_pass_part, host_part = rtsp_input.split('@', 1)
                protocol, creds = user_pass_part.split('//', 1)
                if ':' in creds:
                    usr, pas = creds.split(':', 1)
                    masked_url = f"{protocol}//{usr}:******@{host_part}"
        except Exception:
            pass

        StreamPreviewer.preview(rtsp_input, masked_url)

    def run_config_editor(self):
        """Interactively view and edit credentials, target IPs, ports and save them persistently."""
        while True:
            self.console.clear()
            self.console.print(Panel(
                Align.center("[bold yellow]⚙ เครื่องมือตั้งค่าสแกนเนอร์ CCTV Config Manager ⚙[/]"),
                border_style="yellow"
            ))
            
            table = Table(border_style="yellow")
            table.add_column("รายการตั้งค่า (Settings Name)", style="bold cyan")
            table.add_column("ค่าปัจจุบัน (Current Value)", style="white")
            
            table.add_row("1. Username", self.config["user"])
            table.add_row("2. Password", "****** (ความยาว: {})".format(len(self.config["password"])))
            table.add_row("3. Default Target IP", self.config["ip"])
            table.add_row("4. Ports to Scan", str(self.config["ports_to_test"]))
            table.add_row("5. Back to Main Menu", "[yellow]กลับสู่เมนูหลัก[/]")

            self.console.print(table)
            
            choice = Prompt.ask("👉 เลือกลำดับที่ต้องการแก้ไข (1-5)", choices=["1", "2", "3", "4", "5"], default="5")
            
            if choice == "1":
                self.config["user"] = Prompt.ask("👤 แก้ไข Username ของกล้อง", default=self.config["user"])
            elif choice == "2":
                self.config["password"] = Prompt.ask("🔑 แก้ไข Password ของกล้อง", default=self.config["password"])
            elif choice == "3":
                self.config["ip"] = Prompt.ask("🖥 แก้ไข Default Target IP Address", default=self.config["ip"])
            elif choice == "4":
                ports_input = Prompt.ask(
                    "🔌 ระบุพอร์ตที่ต้องการทดสอบสแกน (คั่นด้วยจุลภาค `,`)", 
                    default=",".join(map(str, self.config["ports_to_test"]))
                )
                try:
                    parsed_ports = [int(p.strip()) for p in ports_input.split(",") if p.strip().isdigit()]
                    if parsed_ports:
                        self.config["ports_to_test"] = parsed_ports
                    else:
                        self.console.print("[bold red]❌ ไม่มีพอร์ตที่ถูกต้อง! จะไม่มีการปรับเปลี่ยนค่านะคะ[/]")
                        time.sleep(1.5)
                except Exception:
                    self.console.print("[bold red]❌ รูปแบบข้อมูลพอร์ตไม่ถูกต้อง![/]")
                    time.sleep(1.5)
            elif choice == "5":
                break

            ConfigManager.save(self.config)
            self.console.print("[bold green]✔ ทำการบันทึกการตั้งค่าเรียบร้อยแล้วค่ะ! 💾[/]")
            time.sleep(1)


if __name__ == "__main__":
    # Perform clean execution environment preparation
    try:
        tui = InteractiveTUI()
        tui.run()
    except KeyboardInterrupt:
        console.print("\n\n[bold magenta]🌸 สัญญาณปิดโปรแกรมตรวจพบ! บ๊ายบายค่ะพี่กัปตัน~ 💕[/]\n")
        sys.exit(0)